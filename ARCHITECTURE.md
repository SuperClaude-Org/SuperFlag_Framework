# SuperFlag - Architecture

## Overview

SuperFlag addresses a fundamental challenge in prompt engineering: providing contextually appropriate directives at runtime without the overhead of persistent system prompts. This architectural document explains the design philosophy, technical decisions, and implementation approach.

## Problem Statement

Developers face three critical challenges with AI assistants:
1. **Context Overhead**: Maintaining comprehensive system prompts consumes significant tokens (often 2000-5000 tokens per interaction)
2. **Directive Fatigue**: Manually specifying appropriate prompts for each task creates cognitive burden
3. **Consistency Gap**: Different domains require different prompting strategies, but switching contexts lacks standardization

## Design Philosophy

### Core Principle: Just-In-Time Context Injection

Rather than loading all possible directives upfront, SuperFlag injects precisely the needed context at runtime. This approach parallels just-in-time compilation in programming languages - optimize when needed, not before.

### Scientific Foundation

The system leverages established prompt engineering techniques:

- **Chain of Thought (CoT)**: Sequential reasoning through `--seq` flag using structured thinking chains
- **Few-Shot Learning**: Every directive includes `<example>` sections demonstrating expected behavior
- **Progressive Disclosure**: `--explain` implements forest→tree→branch→leaf information architecture
- **Role-Based Prompting**: `--collab` establishes peer-level engineering partnership
- **Constraint-Based Validation**: `<verify>` checkpoints ensure directive compliance
- **XML Structural Tagging**: Semantic structure improves directive parsing and attention

### --auto Flag: Contextual Automatic Flag Selection

The `--auto` flag enables AI to analyze task context and automatically select optimal flag combinations:

**Target Users**:
- Users who want to leverage AI's contextual judgment
- Users seeking quick task execution
- Users who want optimal flag combination recommendations

**How It Works**:
- AI analyzes task type (debugging, refactoring, documentation, etc.)
- Automatically selects 1-3 appropriate flags for the task
- Can be combined with user-specified flags

### Architectural Decisions

#### 1. MCP Protocol Selection
**Decision**: Use Model Context Protocol (MCP) as the communication layer
**Rationale**:
- Standard protocol across multiple AI clients (Claude, Gemini, Continue)
- Stateful session management for tracking active flags
- Tool-based interaction aligns with assistant capabilities

#### 2. Hook System Integration (Claude Code)
**Decision**: Leverage Claude Code's hook system for enhanced directive compliance
**Rationale**:
- Hooks provide pre-processing capability before assistant receives prompts
- Enables 95%+ MCP tool invocation compliance rate
- Allows context-aware message injection based on detected flags

#### 3. Distributed Configuration Architecture
**Decision**: Place `flags.yaml` in `~/.superflag/` for user customization
**Rationale**:
- Domain-specific flags can be added without modifying core package
- Separation of mechanism (server) from policy (flags)
- Version-controlled defaults with user override capability

#### 4. Priming Strategy
**Decision**: Place SUPERFLAG.md references in configuration files and session priming
**Rationale**:
- Claude Code/Gemini: @SUPERFLAG.md reference in CLAUDE.md/GEMINI.md
- Continue: rules section in config.yaml
- Initial session priming with --auto or tool mention enhances compliance
- Reference pattern establishes mental model

## Technical Architecture

### Component Map

```
superflag/
├── src/superflag/
│   ├── server.py           # MCP stdio server implementation
│   ├── claude_hook.py       # Hook system for Claude Code
│   ├── install.py          # Multi-target installation logic
│   └── config_manager.py   # YAML and configuration handling
├── flags.yaml              # Directive definitions (17 flags)
├── README.md               # User guide and installation docs
└── ARCHITECTURE.md         # This document
```

### Data Flow

1. **User Input**: "Fix this bug --analyze --strict"
2. **Flag Detection**: Hook/assistant identifies flags
3. **MCP Invocation**: `get_directives(['--analyze', '--strict'])`
4. **Directive Retrieval**: Server returns combined directives
5. **Context Injection**: Assistant receives structured instructions
6. **Task Execution**: Assistant follows directive constraints

### Session Management

The MCP server maintains session state to prevent directive duplication:
- First invocation: Full directive text
- Subsequent invocations: Brief reminder with reference to system-reminder
- Reset capability: `--reset` flag clears session cache

**Important Note**: Flag states are maintained per session. In Claude, when using `/clear`, `/compact`, or during automatic compaction, flag states persist. Use the `--reset` flag explicitly to reinitialize flag states when needed.

**Tip for --git users**: To ensure complete anonymity and prevent signatures like "🤖 Generated with Claude Code" or "Co-Authored-By: Claude <noreply@anthropic.com>" from appearing in commits, always use `--reset` with `--git` flag (e.g., `--reset --git`).

## Performance Characteristics

### Token Efficiency
- **Persistent Context Approach**: Full system prompt included in every interaction
- **SuperFlag**: Only necessary directives injected on-demand
- **Benefit**: Reduced token usage leads to lower API costs

### Response Quality
- **Directive Compliance**: Hook system enhances MCP tool invocation compliance
- **Task Completion**: Structured directives provide clear task execution
- **Error Handling**: `--strict` flag enables systematic error management

## Extensibility Model

### Custom Flag Development

Users can add domain-specific flags by following the pattern:

```yaml
"--custom":
  brief: "Brief description"
  directive: |
    <task>Core objective</task>
    <approach>Step-by-step method</approach>
    <verify>Validation criteria</verify>
```

The consistent XML structure ensures AI models can parse and apply new flags without retraining.

### AI-Assisted Custom Flag Creation

When needing new flags for specific domains or situations:
1. Ask AI to reference existing flags.yaml tone and structure
2. Request: "Based on flags.yaml patterns, create a flag and prompt for [specific situation]"
3. AI generates new flag with prompt engineering techniques applied
4. Add generated flag to ~/.superflag/flags.yaml

Example: `--edit-docs` (documentation refinement)
```yaml
"--edit-docs":
  brief: "Refine documentation for clarity, accuracy, and professional tone"
  directive: |
    <task>Improve existing documentation through systematic refinement</task>
    <approach>
    1. Structure Analysis - evaluate information hierarchy
    2. Accuracy Review - verify technical correctness
    3. Tone Calibration - adjust for target audience
    4. Clarity Enhancement - simplify without oversimplifying
    </approach>
    <verify>
    ☐ All claims verifiable
    ☐ Tone appropriate for audience
    ☐ Technical accuracy maintained
    </verify>
```

This approach enables creating effective directives without prompt engineering expertise.

### Multi-Client Support

Current implementations:
- **Claude Code**: MCP + Hook system (enhanced compliance) + CLAUDE.md reference
- **Gemini CLI**: MCP + GEMINI.md reference
- **Continue**: MCP + config.yaml rules

Future clients require only:
1. MCP stdio server support
2. Optional: Configuration file for priming effect

## NLP Optimization

### Attention Mechanism Design

The directive structure exploits transformer attention patterns:
- **Hierarchical XML tags**: Create semantic boundaries
- **Imperative voice**: Triggers action-oriented processing
- **Verification checklists**: Establish completion criteria
- **Concrete examples**: Activate pattern matching

### Linguistic Choices

Key terms selected for maximum attention weight:
- "MUST", "CRITICAL", "IMMEDIATE": High urgency signals
- "☐" checkboxes: Visual parsing anchors
- `<task>`, `<approach>`, `<verify>`: Consistent semantic markers

## Future Directions

### Adaptive Flag Selection
Research into user pattern analysis for improving `--auto` flag selection accuracy. Potential approaches:
- Frequency analysis of flag combinations
- Task classification via embedding similarity
- Reinforcement learning from user feedback

### Performance Telemetry
Anonymous usage metrics to optimize:
- Flag combination effectiveness
- Token usage patterns
- Task completion rates

## Conclusion

Context Engine transforms prompt engineering from static system prompts to dynamic runtime injection. By providing only the necessary context in real-time, the system achieves both token efficiency and directive compliance. The user-customizable structure enables application across various domains and situations.