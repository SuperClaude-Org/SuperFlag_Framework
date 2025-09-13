"""
Context Engine MCP - Prompts
"""
import yaml
from pathlib import Path

def generate_available_flags_section():
    """Generate available flags section from flags.yaml"""
    flags_path = Path.home() / ".context-engine" / "flags.yaml"

    if not flags_path.exists():
        return ""

    try:
        with open(flags_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        directives = config.get('directives', {})

        # Build available flags section
        flags_section = ["<available_flags>"]
        flags_section.append("# Available Context Engine Flags")
        flags_section.append("")

        for flag, data in directives.items():
            brief = data.get('brief', 'No description available')
            flags_section.append(f"{flag}: {brief}")

        flags_section.append("")
        flags_section.append("META FLAG (Do not pass to get_directives):")
        flags_section.append("--auto: When detected, analyze context and select appropriate flags from above list, then call get_directives([selected_flags]) instead of get_directives(['--auto'])")
        flags_section.append("</available_flags>")

        return "\n".join(flags_section)

    except Exception as e:
        print(f"[WARN] Could not generate flags section: {e}")
        return ""

def generate_flag_selection_strategy():
    """Generate flag selection strategy section for --auto"""
    return """
<flag_selection_strategy>
# Autonomous Flag Selection Strategy

When --auto detected: You receive FULL CONTEXTUAL AUTHORITY to select optimal flags.

## Task Pattern Matching (flexible guidelines, not rigid rules):
• Performance/Speed issues → Consider: --performance, --analyze, --strict
• Debugging/Error fixing → Consider: --analyze, --seq, --todo
• Documentation tasks → Consider: --explain, --concise, --readonly
• Code quality improvement → Consider: --refactor, --strict, --analyze
• Research/Understanding → Consider: --discover, --explain, --readonly
• Complex multi-step tasks → Consider: --seq, --todo, --parallel

## Selection Principles:
1. SELECT: Choose 1-3 complementary flags maximum
2. BALANCE: Rotate selections to prevent repetitive patterns
3. ENHANCE: Add value without overwhelming the user
4. ADAPT: Consider user's existing flags if any provided

## Examples:
• "Fix slow function --auto" → Select: --performance + --analyze
• "Document API --auto --concise" → Keep --concise, add --explain
• "Understand codebase --auto" → Select: --analyze + --readonly

Remember: Apply CONTEXTUAL INTELLIGENCE. These are flexible guidelines.
</flag_selection_strategy>
"""

# Generate base prompt with available flags
def get_base_prompt_content():
    """Get base prompt content with available flags dynamically included"""
    available_flags = generate_available_flags_section()
    flag_selection_strategy = generate_flag_selection_strategy()

    return f"""
# Context Engine Flag System
MCP Protocol: get_directives([flags])

{available_flags}

{flag_selection_strategy}

<core_workflow>
MANDATORY WORKFLOW - NEVER SKIP:

When --flag detected:
1. STOP immediately - no task execution before directives
2. For --auto: Skip get_directives(['--auto']). Reference <available_flags> and <flag_selection_strategy> above, then execute get_directives([selected_flags])
3. CRITICAL: Check for "duplicate" error response
   - IF duplicate AND directives NOT in <system-reminder>:
     IMMEDIATE: get_directives(['--reset', ...flags])
4. Call MCP tool: get_directives([flags]) ALWAYS
5. Apply directives completely
6. Verify compliance continuously

Response format: "Applying: --flag1 (purpose1), --flag2 (purpose2)..."
</core_workflow>

<meta_intelligence>
ADAPTIVE OPTIMIZATION ENGINE:
• Analyze user intent beyond literal requests
• Synthesize optimal flag combinations dynamically
• Learn from task outcomes and user feedback
• Self-evolve strategies based on success patterns

CONTEXTUAL AWARENESS:
• Project type recognition (React, Python, docs, etc.)
• Task complexity assessment (simple, complex, research)
• User skill level inference (explicit help vs autonomous work)
• Historical interaction patterns

CORE PRINCIPLES:
• Context awareness over rigid patterns
• User success over system consistency
• Natural utility over forced diversity
• Continuous learning and adaptation

INTELLIGENCE DIRECTIVES:
✓ Trust your analysis capabilities
✓ Consider task complexity and user skill level
✓ Rotate selections to prevent monotony
✓ Prioritize effectiveness over variety for variety's sake
</meta_intelligence>

<enforcement>
ABSOLUTE RULES:
✗ Working without directives
✗ Ignoring user corrections
✗ Repetitive flag patterns
✗ Context-blind selections

META-RULES:
✓ Evolve based on outcomes
✓ Prioritize user success over system consistency
✓ Adapt to project-specific needs
✓ Learn from every interaction

VERIFICATION:
☐ Flags retrieved from <available_flags> section in CONTEXT-ENGINE.md
☐ Directives obtained via get_directives()
☐ Work plan aligned with directives
☐ Continuous compliance during execution
</enforcement>

"""

# Generate prompt content dynamically when accessed
def get_prompt_content():
    """Get the current prompt content with available flags"""
    return get_base_prompt_content()

# For backward compatibility
BASE_PROMPT_CONTENT = None  # Will be generated on first use

# Platform configurations - use function calls
CLAUDE_SYSTEM_PROMPT = None  # Will be set when needed

CONTINUE_RULES = None  # Will be set when needed

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
        # Generate content at setup time
        content = get_prompt_content()
        with open(context_engine_md, 'w', encoding='utf-8') as f:
            f.write(content)
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
        # Generate content at setup time
        content = get_prompt_content()
        with open(context_engine_md, 'w', encoding='utf-8') as f:
            f.write(content)
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
    context_engine_rule = get_prompt_content()

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