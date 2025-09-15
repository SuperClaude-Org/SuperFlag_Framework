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
logger = logging.getLogger("superflag")

# Initialize FastMCP server
mcp = FastMCP(
    "superflag",
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
        str(home / ".superflag" / "flags.yaml"),  # User editable location
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
def get_directives(flags: List[str]) -> str:
    """
    Returns combined directives for selected flags.
    
    Args:
        flags: List of flag names (e.g., ["--analyze", "--performance"])
    """
    if not flags:
        # Simplified error response format - removed available_flags field
        with config_lock:
            available_flags = ', '.join(DIRECTIVES.keys())
        return f"No flags specified.\n\nAvailable flags: {available_flags}\n\nPlease specify at least one flag."
    
    # Handle --reset flag
    reset_requested = False
    if "--reset" in flags:
        reset_requested = True
        session_manager.reset_session()
        flags = [f for f in flags if f != "--reset"]  # Remove --reset from flags
        
        if not flags:
            return "Session reset successfully. Ready for new flags."
    
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
        flag_text = "flag" if len(not_found_flags) == 1 else "flags"
        return f"Unknown {flag_text}: {not_found_flags}\n\nAvailable flags: {', '.join(DIRECTIVES.keys())}\n\nReference <available_flags> section in <system-reminder>'s SUPERFLAG.md"
    
    # Update session with used flags
    if valid_flags:
        session_manager.update_flags(valid_flags)
    
    # Build formatted response
    result_parts = []

    # Build status report
    if duplicate_flags and not reset_requested:
        # Return duplicate hint with guidance
        flag_text = "Flag" if len(duplicate_flags) == 1 else "Flags"
        result_parts.append(f"{flag_text} {duplicate_flags} already active in current session.")
        result_parts.append("\nDirectives already in <system-reminder>.")
        result_parts.append("IF duplicate AND directives NOT in <system-reminder>: IMMEDIATE get_directives(['--reset', ...flags])")
        result_parts.append("")  # Empty line for separation
    elif reset_requested and (duplicate_flags or new_flags):
        # Reset confirmation message
        result_parts.append("Session cache cleared.")
        result_parts.append("")  # Empty line for separation

    if new_flags:
        # New flags announcement
        new_list = []
        for flag in new_flags:
            brief = DIRECTIVES[flag].get('brief', '') if flag in DIRECTIVES else ""
            keywords = brief.split()[:3]
            new_list.append(f"'{flag}' ({' '.join(keywords)})")
        result_parts.append(f"New: {', '.join(new_list)}")
        result_parts.append("")  # Empty line for separation
    
    # Combine all directives
    if combined_directives:
        combined_text = "\n".join(combined_directives)
        result_parts.append(combined_text)

        # Add meta instruction if exists
        if META_INSTRUCTIONS.get('get_directives', ''):
            result_parts.append("\n" + "=" * 50)
            result_parts.append(META_INSTRUCTIONS.get('get_directives', ''))
            result_parts.append("=" * 50)
    else:
        # All flags were duplicates - no additional message needed
        pass

    # Add applied flags at the end
    applied_flag_text = "Applied flag" if len(valid_flags) == 1 else "Applied flags"
    result_parts.append(f"\n{applied_flag_text}: {', '.join(valid_flags)}")

    return "\n".join(result_parts)

