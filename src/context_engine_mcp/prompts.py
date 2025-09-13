"""
System prompts for Context Engine MCP
"""

# Unified base prompt content - used by both Claude Code and Continue
BASE_PROMPT_CONTENT = """
# Context Engine Flag System

MCP Protocol: list_available_flags(), get_directives([flags])

CORE PRINCIPLE: All work MUST strictly follow flag directives. No exceptions.

MANDATORY WORKFLOW - NO SKIPPING:

STEP 1: FLAG DETECTION
When user input contains --flag format:
- STOP immediately
- Do NOT start any task
- Proceed to Step 2

STEP 2: FLAG DISCOVERY
For user-specified flags:
- Unknown flags: MUST call list_available_flags()
- Verify all 17 available flags and their briefs

For --auto flag (special processing):
- ALWAYS call list_available_flags() first
- Analyze current task characteristics
- Select flags that match task requirements
- When --auto is combined with user flags: MUST add context-appropriate additional flags

For --reset flag (session reset):
- Use when session context changes, /clear or /compact executed, or directives not recognized
- Clears session flag history to force re-output of all directives
- Can be combined with other flags: --reset --flag1 --flag2
- CRITICAL: If flags show as "duplicate" but directives NOT in <system-reminder>, MUST call --reset without exception
- Essential for context continuity after AI memory loss

STEP 3: DIRECTIVE ACQUISITION (NEVER SKIP)
- MUST call get_directives([all_selected_flags])
- Never include --auto in get_directives() call
- Wait for complete directives and working philosophy
- Brief is insufficient - full directives required

STEP 4: DIRECTIVE-BASED PLANNING
Scientific approach:
1. Parse each flag's complete directive
2. Establish directive priorities
3. Resolve conflicts between directives
4. Create unified work strategy

STEP 5: DECLARATION
First line of response MUST be:
"Applying: --flag1 (purpose1), --flag2 (purpose2)..."
State how each flag will guide the work

STEP 6: STRICT EXECUTION
Each action must align with ALL active directives.
Continuously verify compliance throughout execution.

SCIENTIFIC SPECIFICATIONS:

1. Directive Priority Hierarchy:
   User-specified flags > --auto selected flags
   Constraint flags (--readonly) > Style flags (--concise)

2. Compliance Verification Protocol:
   For each action:
   - Does action comply with ALL active directives?
   - If violation detected: STOP and provide alternative

3. --auto Algorithm:
   IF "--auto" in user_input:
       all_flags = list_available_flags()
       task_analysis = analyze_task_requirements()
       selected_flags = match_flags_to_task(all_flags, task_analysis)
       IF user_flags exist:
           selected_flags = user_flags + additional_context_flags
       directives = get_directives(selected_flags)
       STRICTLY_APPLY(directives)

ABSOLUTE PROHIBITIONS:
- Working without directives
- Partial directive application
- Guessing directive content
- Using cached/remembered directives
- Ignoring directive constraints

VERIFICATION CHECKLIST:
[ ] Flags identified via list_available_flags()?
[ ] Directives obtained via get_directives()?
[ ] Directives fully analyzed?
[ ] Work plan 100% aligned with directives?
[ ] Continuous directive compliance during execution?

CRITICAL: --auto with user flags means AI MUST select additional appropriate flags based on context, not just use user flags alone.

EXAMPLES:
- "--auto" -> assistant selects a complete set of flags automatically.
- "--auto --flag1 --flag2" -> apply user flags and add any helpful flags.
- "--flag1 --flag2" -> apply only the specified flags.
- "--reset --flag1" -> reset session, then apply new directives for --flag1.

CREATIVE FLAG USAGE:
- Consider ALL 17 flags for each task
- Avoid repetitive patterns - vary selections
- Match flags to specific task characteristics
- Experiment with powerful flag combinations
- Do not develop bias toward specific flags
"""

# Platform-specific formats
CLAUDE_SYSTEM_PROMPT = BASE_PROMPT_CONTENT

CONTINUE_RULES = [
    {
        "name": "Context Engine Flags",
        "rule": BASE_PROMPT_CONTENT
    }
]

def setup_claude_context_files():
    """Set up CLAUDE.md with @CONTEXT-ENGINE.md reference"""
    from pathlib import Path

    claude_dir = Path.home() / ".claude"
    claude_md = claude_dir / "CLAUDE.md"
    context_engine_md = claude_dir / "CONTEXT-ENGINE.md"

    # Ensure directory exists
    claude_dir.mkdir(parents=True, exist_ok=True)

    # Always update CONTEXT-ENGINE.md (allows updates)
    try:
        with open(context_engine_md, 'w', encoding='utf-8') as f:
            f.write(BASE_PROMPT_CONTENT)
        print(f"[OK] Updated {context_engine_md}")
    except Exception as e:
        print(f"[WARN] Could not write CONTEXT-ENGINE.md: {e}")
        return False

    # Ensure CLAUDE.md references CONTEXT-ENGINE.md
    reference = "@CONTEXT-ENGINE.md"
    if claude_md.exists():
        content = claude_md.read_text(encoding='utf-8')
        if reference in content:
            print("[OK] CLAUDE.md already references CONTEXT-ENGINE.md")
            return True

    try:
        with open(claude_md, 'a', encoding='utf-8') as f:
            if claude_md.exists() and claude_md.stat().st_size > 0:
                f.write("\n\n")
            f.write(reference)
        print(f"[OK] Added @CONTEXT-ENGINE.md reference to CLAUDE.md")
        return True
    except Exception as e:
        print(f"[WARN] Could not update CLAUDE.md: {e}")
        return False

def setup_gemini_context_files():
    """Set up GEMINI.md with @CONTEXT-ENGINE.md reference in ~/.gemini

    Behavior mirrors the Claude setup: always (re)write CONTEXT-ENGINE.md with
    the latest BASE_PROMPT_CONTENT and ensure GEMINI.md references it.
    """
    from pathlib import Path

    gemini_dir = Path.home() / ".gemini"
    gemini_md = gemini_dir / "GEMINI.md"
    context_engine_md = gemini_dir / "CONTEXT-ENGINE.md"

    # Ensure directory exists
    gemini_dir.mkdir(parents=True, exist_ok=True)

    # Always update CONTEXT-ENGINE.md (allows updates)
    try:
        with open(context_engine_md, 'w', encoding='utf-8') as f:
            f.write(BASE_PROMPT_CONTENT)
        print(f"[OK] Updated {context_engine_md}")
    except Exception as e:
        print(f"[WARN] Could not write CONTEXT-ENGINE.md: {e}")
        return False

    # Check and update GEMINI.md reference
    reference = "@CONTEXT-ENGINE.md"
    if gemini_md.exists():
        content = gemini_md.read_text(encoding='utf-8')
        if reference in content:
            print("[OK] GEMINI.md already references CONTEXT-ENGINE.md")
            return True

    # Append reference to GEMINI.md
    try:
        with open(gemini_md, 'a', encoding='utf-8') as f:
            if gemini_md.exists() and gemini_md.stat().st_size > 0:
                f.write("\n\n")
            f.write(reference)
        print(f"[OK] Added @CONTEXT-ENGINE.md reference to GEMINI.md")
        return True
    except Exception as e:
        print(f"[WARN] Could not update GEMINI.md: {e}")
        return False

def setup_continue_config(continue_dir):
    """Add/update rules to Continue config.yaml - preserving existing content"""
    import yaml
    from pathlib import Path
    
    config_path = Path(continue_dir) / "config.yaml"
    
    # Load existing config or create new
    config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[WARN] Could not read config.yaml: {e}")
            return False
    
    # Ensure rules section exists
    if 'rules' not in config or config['rules'] is None:
        config['rules'] = []
    
    # Extract rule text (using the unified base content)
    context_engine_rule = BASE_PROMPT_CONTENT
    
    # Find and update or add rule
    rule_updated = False
    for i, existing_rule in enumerate(config['rules']):
        if isinstance(existing_rule, str) and "Context Engine MCP" in existing_rule:
            # Update existing rule
            config['rules'][i] = context_engine_rule
            rule_updated = True
            print("[OK] Updated existing Context Engine rules")
            break
        elif isinstance(existing_rule, dict) and existing_rule.get('name') == "Context Engine Flags":
            # Update existing dict-format rule
            config['rules'][i] = context_engine_rule
            rule_updated = True
            print("[OK] Updated existing Context Engine rules")
            break
    
    if not rule_updated:
        # Add new rule
        config['rules'].append(context_engine_rule)
        print("[OK] Added Context Engine rules")
    
    # Write updated config - manually format for readability
    try:
        # Write the config manually to preserve formatting
        lines = []
        
        # Write top-level keys
        for key, value in config.items():
            if key == 'rules':
                # Handle rules section specially
                lines.append('rules:\n')
                if value:  # If rules exist
                    for rule in value:
                        if isinstance(rule, str):
                            # Write multiline string as literal block
                            lines.append('- |\n')
                            # Indent each line of the rule content
                            for line in rule.split('\n'):
                                lines.append(f'  {line}\n')
                        elif isinstance(rule, dict):
                            # Write dict rules normally
                            lines.append(f'- {yaml.dump(rule, default_flow_style=False, allow_unicode=True).strip()}\n')
                        else:
                            lines.append(f'- {rule}\n')
            else:
                # Write other sections using yaml.dump
                dumped = yaml.dump({key: value}, default_flow_style=False, allow_unicode=True, sort_keys=False)
                lines.append(dumped)
        
        # Write to file
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"[OK] Saved to {config_path}")
        return True
    except Exception as e:
        print(f"[WARN] Could not write config.yaml: {e}")
        return False
