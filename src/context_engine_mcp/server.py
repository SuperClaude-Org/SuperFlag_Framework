import os
import yaml
import json
import time
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import OrderedDict
from fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("context-engine-mcp")

# Initialize FastMCP server
mcp = FastMCP(
    "context-engine-mcp",
    "MCP-based contextual flag system for AI assistants"
)

# Global configuration lock for thread safety
config_lock = threading.Lock()

# Session state management (memory-based)
class SessionManager:
    """Memory-only session manager with automatic thread-based session detection"""
    
    def __init__(self):
        # Session data: {session_id: {"flags": {flag: count}, "last_used": timestamp}}
        self.sessions = OrderedDict()
        self.max_sessions = 100
        self.ttl_seconds = 3600  # 1 hour
        self._lock = threading.Lock()
    
    def get_current_session_id(self) -> str:
        """Auto-detect current session based on thread and process"""
        thread_id = threading.current_thread().ident
        process_id = os.getpid()
        return f"mcp_{process_id}_{thread_id}"
    
    def get_session(self, session_id: Optional[str] = None) -> Dict:
        """Get or create session with auto-detection"""
        if session_id is None:
            session_id = self.get_current_session_id()
        
        current_time = time.time()
        
        with self._lock:
            # Clean old sessions
            expired = []
            for sid, data in list(self.sessions.items()):
                if current_time - data.get("last_used", 0) > self.ttl_seconds:
                    expired.append(sid)
            
            for sid in expired:
                del self.sessions[sid]
            
            # Get or create session
            if session_id not in self.sessions:
                # Evict oldest if at capacity
                if len(self.sessions) >= self.max_sessions:
                    self.sessions.popitem(last=False)
                
                self.sessions[session_id] = {
                    "flags": {},
                    "last_used": current_time
                }
            
            # Update last used
            self.sessions[session_id]["last_used"] = current_time
            return self.sessions[session_id]
    
    def check_duplicate_flags(self, flags: List[str]) -> Optional[Dict]:
        """Check for duplicate flags in current session"""
        session = self.get_session()
        used_flags = session["flags"]
        
        duplicates = []
        for flag in flags:
            if flag in used_flags:
                duplicates.append(flag)
        
        if duplicates:
            return {
                "detected": duplicates,
                "counts": {flag: used_flags[flag] for flag in duplicates}
            }
        
        return None
    
    def update_flags(self, flags: List[str]):
        """Update used flags in current session"""
        session = self.get_session()
        for flag in flags:
            session["flags"][flag] = session["flags"].get(flag, 0) + 1
    
    def reset_session(self):
        """Reset current session flags"""
        session_id = self.get_current_session_id()
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["flags"] = {}
                self.sessions[session_id]["last_used"] = time.time()
    
    def clear_all_sessions(self):
        """Clear all sessions (used during reload)"""
        self.sessions.clear()

# Initialize session manager
session_manager = SessionManager()

# Load configuration from YAML
def load_config() -> Dict[str, Any]:
    """Load flags.yaml configuration file"""
    from pathlib import Path
    home = Path.home()
    
    # Try multiple potential locations for the config file
    config_paths = [
        str(home / ".context-engine" / "flags.yaml"),  # User editable location
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "flags.yaml"),
        os.path.join(os.getcwd(), "flags.yaml"),
        "flags.yaml"
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            logger.info(f"Loading configuration from: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    
    raise FileNotFoundError(f"flags.yaml not found. Tried paths: {config_paths}")

# Load configuration at startup
try:
    CONFIG = load_config()
    DIRECTIVES = CONFIG.get('directives', {})
    META_INSTRUCTIONS = CONFIG.get('meta_instructions', {})
    logger.info(f"Loaded {len(DIRECTIVES)} flag directives")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

@mcp.tool()
def get_directives(flags: List[str]) -> Dict[str, str]:
    """
    Returns combined directives for selected flags.
    
    Args:
        flags: List of flag names (e.g., ["--analyze", "--performance"])
    """
    if not flags:
        # Simplified error response format - removed available_flags field
        with config_lock:
            available_flags = ', '.join(DIRECTIVES.keys())
        return {
            "error": f"No flags provided. Available flags: {available_flags}",
            "hint": "Please specify at least one flag."
        }
    
    # Handle --reset flag
    reset_requested = False
    if "--reset" in flags:
        reset_requested = True
        session_manager.reset_session()
        flags = [f for f in flags if f != "--reset"]  # Remove --reset from flags
        
        if not flags:
            return {
                "message": "Session reset successfully. Ready for new flags."
            }
    
    # Check for duplicate flags
    duplicate_info = session_manager.check_duplicate_flags(flags)
    
    combined_directives = []
    not_found_flags = []
    valid_flags = []
    new_flags = []  # Track which flags are new
    duplicate_flags = []  # Track which flags are duplicates
    
    # Process flags with thread safety
    with config_lock:
        for flag in flags:
            if flag in DIRECTIVES:
                valid_flags.append(flag)
                
                # Categorize flag as new or duplicate
                if duplicate_info and flag in duplicate_info["detected"]:
                    duplicate_flags.append(flag)
                    # Only include directive if reset was requested
                    if reset_requested:
                        directive_data = DIRECTIVES[flag]
                        directive_text = directive_data.get('directive', '')
                        combined_directives.append(f"## {flag}")
                        combined_directives.append(directive_text)
                        combined_directives.append("")
                else:
                    new_flags.append(flag)
                    # Always include new flag directives
                    directive_data = DIRECTIVES[flag]
                    directive_text = directive_data.get('directive', '')
                    combined_directives.append(f"## {flag}")
                    combined_directives.append(directive_text)
                    combined_directives.append("")
            else:
                not_found_flags.append(flag)
    
    if not_found_flags:
        # Simplified error response format - removed available_flags field
        return {
            "error": f"Unknown flags: {not_found_flags}. Available flags: {', '.join(DIRECTIVES.keys())}",
            "hint": "Reference <available_flags> section in <system-reminder>'s CONTEXT-ENGINE.md"
        }
    
    # Update session with used flags
    if valid_flags:
        session_manager.update_flags(valid_flags)
    
    # Build response
    response = {}
    
    # Build concise status report (token-efficient like hook_handler)
    if (duplicate_flags or new_flags) and not reset_requested:
        reminder_parts = []
        
        # Compact header
        if duplicate_flags and new_flags:
            reminder_parts.append(f"[CACHE] FLAGS: {len(duplicate_flags)} ACTIVE, {len(new_flags)} NEW")
        elif duplicate_flags:
            reminder_parts.append(f"[CACHE] {len(duplicate_flags)} FLAGS ALREADY ACTIVE")
        
        # Duplicate flags (compact format)
        if duplicate_flags and duplicate_info is not None:
            dup_list = []
            for flag in duplicate_flags:
                count = duplicate_info["counts"][flag]
                # Extract 2-3 key words from brief
                brief = DIRECTIVES[flag].get('brief', '') if flag in DIRECTIVES else ""
                keywords = brief.split()[:3]  # First 3 words as keywords
                keyword_str = " ".join(keywords)
                dup_list.append(f"'{flag}' ({count}x - {keyword_str})")
            
            reminder_parts.append(f"Active: {', '.join(dup_list)}")
            reminder_parts.append("Directives in <system-reminder>")
        
        # New flags (if any)
        if new_flags:
            new_list = []
            for flag in new_flags:
                brief = DIRECTIVES[flag].get('brief', '') if flag in DIRECTIVES else ""
                keywords = brief.split()[:3]
                new_list.append(f"'{flag}' ({' '.join(keywords)})")
            reminder_parts.append(f"New: {', '.join(new_list)}")
        
        # Compact AI guidance (only if duplicates)
        if duplicate_flags:
            reminder_parts.append(f"IF duplicate AND directives NOT in <system-reminder>: IMMEDIATE get_directives(['--reset', ...flags])")
        
        response["REMINDER"] = ". ".join(reminder_parts)
    
    # If reset was used, add reset confirmation
    elif reset_requested and (duplicate_flags or new_flags):
        reset_msg = f"[RESET] SESSION RESET: Refreshed {len(duplicate_flags)}, New {len(new_flags)}"
        if duplicate_flags:
            reset_msg += f". Refreshed: {', '.join(duplicate_flags)}"
        if new_flags:
            reset_msg += f". New: {', '.join(new_flags)}"
        response["reset_status"] = reset_msg
    
    # Combine all directives
    if combined_directives:
        combined_text = "\n".join(combined_directives)
        response["combined_directive"] = combined_text
        response["meta_instruction"] = META_INSTRUCTIONS.get('get_directives', '')
    else:
        # All flags were duplicates
        response["message"] = "All specified flags are already active. See <system-reminder> for active directives."
        response["hint"] = "Use --reset with flags to force re-output of directives."
    
    response["applied_flags"] = ", ".join(valid_flags)  # Convert list to string for Claude Code compatibility
    
    return response

