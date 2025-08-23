---
category: workflow
complexity: medium
estimated_time: "10-15 minutes"
dependencies: []
sub_commands: []
version: "1.0"
---

# Workflow Scope Analysis

Analyze and define boundaries for a project issue to prevent scope creep: $ARGUMENTS

## Usage Options

- `phase X issue Y` - Standard analysis (e.g., "phase 1 issue 3")
- `quick phase X issue Y` - Essential boundary definition only
- `detailed phase X issue Y` - Comprehensive analysis with validation

## Instructions

### Step 1: Issue-Specific Analysis

1. **Read ONLY the Issue Definition First**:
   - `/docs/planning/phase-{X}-foundation.md` - For Phase 0 issues (foundation setup)
   - `/docs/planning/phase-{X}-core-infrastructure.md` - For Phase 1+ issues
   - Search for issue ID pattern `P{X}-{YYY}` or `Issue P{X}-{YYY}` using Grep tool
   - **STOP HERE** - Do not read broader documentation yet

2. **Extract and Isolate Issue Scope**:
   - Issue title and description
   - **Acceptance criteria** (this defines the boundary)
   - Dependencies listed in the issue
   - Testing requirements from the issue
   - Time estimates
   - **Current completion status** (some issues may be partially complete)
   - **Document the EXACT scope boundary**

### Step 2: Scope Boundary Validation

1. **Define Issue Boundaries**:
   - List what IS included in acceptance criteria
   - List what is NOT mentioned in acceptance criteria
   - Identify any ambiguous requirements that need clarification

2. **Create Scope Constraint Document**:

   ```text
   ISSUE SCOPE BOUNDARY:
   ✅ INCLUDED: [List from acceptance criteria]
   ❌ EXCLUDED: [Anything not in acceptance criteria]
   ❓ UNCLEAR: [Items needing clarification]
   ```

### Step 3: Contextual Research (Only After Scope Definition)

**ONLY AFTER establishing scope boundaries**, read supporting documentation as needed:

- `/docs/adr/` - Architecture Decision Records relevant to your defined scope
- `/docs/project/PROJECT_PLAN.md` - Read ONLY if broader project context is needed for acceptance criteria
- `/docs/project/TAXONOMY_GUIDE.md` - Read ONLY if classification standards are part of acceptance criteria
- `CLAUDE.md` - Read ONLY for development standards relevant to acceptance criteria
- `README.md` - Read ONLY if basic project setup is part of acceptance criteria

**Research Constraint**: Only read sections that directly relate to items in your acceptance criteria. Skip all other content.

## Output Format

```markdown
# Scope Analysis: Phase {X} Issue {Y}

## Issue Overview
- **Title**: [Issue title]
- **Description**: [Brief description]
- **Estimated Time**: [From issue]
- **Priority**: [From issue]
- **Status**: [Current completion status]

## Scope Boundaries
✅ **INCLUDED in Issue** (Completed/To Do):
- [Item 1 from acceptance criteria] (Status)
- [Item 2 from acceptance criteria] (Status)

❌ **EXCLUDED from Issue**:
- [Item not mentioned in acceptance criteria]
- [Another excluded item]

❓ **UNCLEAR Requirements**:
- [Ambiguous item needing clarification]

## Dependencies
- [List from issue with completion status]

## Testing Requirements
- [Testing requirements from issue]

## Deliverables
- [List from issue]

## Next Steps
- Proceed to `/project:workflow-plan-validation` with these boundaries
- Address unclear requirements before planning
```

## Error Handling

- **Issue file not found**: Look in `/docs/planning/phase-index.md` to identify correct phase file location
- **Large file content**: Use Grep tool to search for issue ID pattern instead of reading entire files
- **No acceptance criteria**: Request clarification from user before proceeding
- **Ambiguous scope**: Generate specific clarifying questions
- **Dependencies missing**: List what needs to be resolved first
- **Partially completed issues**: Clearly identify completed vs incomplete acceptance criteria

## Examples

```bash
# Standard scope analysis
/project:workflow-scope-analysis phase 1 issue 3

# Quick boundary definition
/project:workflow-scope-analysis quick phase 2 issue 7

# Detailed analysis with full validation
/project:workflow-scope-analysis detailed phase 1 issue 1
```
