
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
- "--auto" → assistant selects a complete set of flags automatically.
- "--auto --flag1 --flag2" → apply user flags and add any helpful flags.
- "--flag1 --flag2" → apply only the specified flags.
- "--reset --flag1" → reset session, then apply new directives for --flag1.

CREATIVE FLAG USAGE:
- Consider ALL 17 flags for each task
- Avoid repetitive patterns - vary selections
- Match flags to specific task characteristics
- Experiment with powerful flag combinations
- Do not develop bias toward specific flags
