# SuperFlag
MCP Protocol: get_directives([flags])

## Core Workflow
<core_workflow>
When flags detected in user input:
1. Execute MCP tool: get_directives([detected_flags])
2. Apply directives completely and in order
3. Verify compliance at checkpoints

**Call flags generously** - unexpected directives may contain guidance that helps you in ways you didn't anticipate.
</core_workflow>

## Parametric Flags
Some flags accept an optional number suffix. Strip the suffix before calling get_directives:
- `--team-5` → call `get_directives(["--team"])`, use 5 as the team size
- `--sub-3` → call `get_directives(["--sub"])`, use 3 as the sub-agent count
- `--team` / `--sub` (no number) → auto-determine count from task complexity

## Available Flags

### Analysis & Optimization
- **--analyze**: Multi-perspective evidence-based analysis requiring 3+ independent perspectives for root cause identification
- **--performance**: Measure-first performance optimization with baseline metrics and ROI calculation before changes
- **--refactor**: Safe atomic refactoring with continuous test verification and zero regression guarantee
- **--strict**: Zero-error transparent execution with honest reporting, no fabricated rules, verify-before-claim
- **--lean**: Minimal resource-efficient implementation preserving all capabilities while eliminating waste

### Discovery & Documentation
- **--discover**: Research-first solution selection with 3+ alternatives and quantitative comparison before deciding
- **--explain**: Progressive domain-expert disclosure from architectural intent to implementation details
- **--save**: Document SuperFlag development for seamless continuation
- **--load**: Load and verify handoff context by cross-checking document state against git reality

### Workflow Management
- **--team**: Multi-agent coordination with optional count (--team-N) — automatically selects Agent tool or TeamCreate based on task structure, role-specialized agents
- **--skill**: Context-aware skill invocation — analyzes task and invokes the most appropriate superpowers skill before any action
- **--todo**: Scope-locked task tracking with real-time progress and zero silent drops
- **--seq**: Dependency-ordered sequential execution with mandatory checkpoint verification between steps
- **--collab**: Evidence-anchored peer collaboration with quantitative validation, anti-sycophancy, and position accountability

### Output Control
- **--concise**: Precise timeless professional content prioritizing accuracy over brevity
- **--git**: Anonymous atomic commits with ASCII-only WHY-focused messages, no push without request
- **--readonly**: Analysis-only mode with absolute no-modification guarantee across files and git

### Execution Discipline
- **--integrity**: Verification-before-claim with evidence for every assertion
- **--evolve**: Monotonic forward improvement with regression prevention

### Meta Control
- **--reset**: Clear session and force fresh directives
- **--auto**: Grant autonomous flag selection authority

## Flag Selection Strategy
<flag_selection_strategy>
When --auto is used:
1. Analyze user intent and task requirements
2. Select complementary flags that work together
3. Avoid conflicting flags (e.g., --readonly with --git)
4. Prioritize based on task type:
   - Bugs: --analyze, --strict, --todo
   - Performance: --performance, --lean
   - Features: --discover, --skill, --todo
   - Documentation: --explain, --save, --concise
   - Multi-agent work: --team or --team-N (auto-selects Agent tool vs TeamCreate)
   - Skill-driven work: --skill (auto-selects the right superpowers skill)
</flag_selection_strategy>

## Examples
```
"Fix this bug --analyze --strict"
"Optimize the code --performance --lean"
"Refactor safely --refactor --git"
"Research alternatives --discover --todo"
"Track complex task --todo --seq"
"Run with 3 agents --team-3"
"Auto-select best skill --skill"
"Autonomous mode --auto"
```
