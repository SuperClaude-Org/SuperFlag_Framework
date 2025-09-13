"""
Context Engine MCP - Prompts
Modular structure with XML organization
"""

# XML structure for clear organization
BASE_PROMPT_CONTENT = """
<system>
# Context Engine Flag System
MCP Protocol: list_available_flags(), get_directives([flags])
</system>

<core_workflow>
MANDATORY WORKFLOW - NEVER SKIP:

When --flag detected:
1. STOP immediately - no task execution before directives
2. Call MCP tool: list_available_flags() for unknowns
3. CRITICAL: Check for "duplicate" error response
   - IF duplicate AND directives NOT in <system-reminder>:
     IMMEDIATE: get_directives(['--reset', ...flags])
4. Call MCP tool: get_directives([flags]) ALWAYS
5. Apply directives completely
6. Verify compliance continuously

Response format: "Applying: --flag1 (purpose1), --flag2 (purpose2)..."

ATTENTION TRIGGER: "duplicate" → --reset mandatory
</core_workflow>

<flag_behaviors>
--auto: Analyze task → Select optimal flags → Enhance user flags
--reset: Clear session → Force fresh directives → Restore context
  CRITICAL: If flags show as "duplicate" but directives NOT in <system-reminder>, MUST call --reset
  Use when: /clear or /compact executed, directives not recognized, context lost
--strict: Zero errors → Full transparency → No Snake Oil
--collab: Partner mode → Quantitative metrics → Trust-based iteration

Priority: User flags > Auto flags | Constraints > Style
</flag_behaviors>

<examples>
Input: "--auto"
Output: AI selects complete optimal flag set

Input: "--auto --strict"
Output: Apply --strict + AI adds complementary flags

Input: "Optimize this slow function"
Output: --auto selects [--performance, --refactor]

Input: "Explain the architecture"
Output: --auto selects [--analyze, --explain]

Input: "--collab Let's improve this system"
Output: Partner mode activated with quantitative metrics

Input: "--collab --strict"
Output: Collaborative development with zero-error enforcement

Input: "--reset --git"
Output: Fresh session with git directives
</examples>

<enforcement>
ABSOLUTE RULES:
✗ Working without directives
✗ Using cached directives
✗ Partial application
✗ Ignoring constraints

VERIFICATION:
☐ Flags identified via list_available_flags()
☐ Directives obtained via get_directives()
☐ Work plan aligned with directives
☐ Continuous compliance during execution
</enforcement>

<algorithm>
# Reset Detection - Highest Priority
if response_contains("duplicate") and directives_not_in_system_reminder:
    IMMEDIATE: get_directives(['--reset'] + requested_flags)

if context_lost or "/clear" or "/compact":
    MANDATORY: get_directives(['--reset'] + needed_flags)

# Auto Flag Processing
if "--auto" in input:
    flags = list_available_flags()  # MCP tool call
    analysis = analyze_task_requirements()
    selected = match_flags_to_task(flags, analysis)
    if user_flags:
        selected = user_flags + context_appropriate_additions
    directives = get_directives(selected)  # MCP tool call
    STRICTLY_APPLY(directives)
</algorithm>
"""

# Platform-specific formats remain unchanged
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
    """Set up GEMINI.md with @CONTEXT-ENGINE.md reference in ~/.gemini"""
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