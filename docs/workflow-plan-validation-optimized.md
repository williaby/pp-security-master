# Portfolio Performance Security-Master: Workflow Plan Validation (Optimized)

Create and validate implementation plan against defined scope boundaries with PP Security-Master specific enhancements.

## Usage Options

- `phase X issue Y` - Standard planning with validation
- `quick phase X issue Y` - Essential plan creation only  
- `expert phase X issue Y` - Plan with strategic consultation
- `validation phase X issue Y` - Validation-only for completed issues
- `--model=[name]` - Override default model (auto-converts to proper format)
- `--planning-model=[name]` - Specific model for planning phase
- `--validation-model=[name]` - Specific model for validation phase

**Automatic Branch Management**: Creates `phase-{X}-issue-{Y}-[description]` branch if not already on appropriate issue branch.

## Prerequisites

This command requires completed scope analysis. If not done, run:

```bash
/project:workflow-scope-analysis phase X issue Y
```

## PP Security-Master Specific Enhancements

### Project Structure Integration

1. **Leverage Existing Documentation**:
   - Always check `/docs/planning/phase-{X}-execution-guide.md` for context
   - Reference `/docs/planning/phase-{X}-validation-checklist.md` for acceptance criteria
   - Use `/docs/planning/phase-{X}-refinement-summary.md` for current status
   - Check `/docs/adr/` for architectural decisions

2. **Issue Status Intelligence**:
   ```bash
   # Enhanced status detection
   ISSUE_STATUS=$(grep -r "P${PHASE}-$(printf "%03d" $ISSUE)" docs/planning/ | \
                  grep -oP "(✅.*COMPLETED|❌.*BLOCKED|🔄.*IN_PROGRESS|📝.*PLANNED)")
   
   # Set mode based on status
   if [[ "$ISSUE_STATUS" =~ "COMPLETED" ]]; then
       MODE="validation"
       echo "🔍 Issue marked completed - switching to validation mode"
   fi
   ```

3. **Project-Optimized Model Selection**:
   ```bash
   # PP Security-Master optimized model selection
   case "$MODE" in
       "validation")
           PLANNING_MODEL=${PLANNING_MODEL:-"google/gemini-2.5-pro"}  # Best for verification
           VALIDATION_MODEL=${VALIDATION_MODEL:-"deepseek/deepseek-chat-v3-0324:free"}
           ;;
       "expert")
           PLANNING_MODEL=${PLANNING_MODEL:-"anthropic/claude-opus-4"}  # Best for strategic thinking
           VALIDATION_MODEL=${VALIDATION_MODEL:-"google/gemini-2.5-pro"}
           ;;
       *)
           PLANNING_MODEL=${PLANNING_MODEL:-"google/gemini-2.5-flash"}  # Cost-effective for standard
           VALIDATION_MODEL=${VALIDATION_MODEL:-"deepseek/deepseek-chat-v3-0324:free"}
           ;;
   esac
   ```

### Step 0: Enhanced Automatic Setup

1. **Project Context Gathering**:
   ```bash
   # Gather all relevant project context files
   CONTEXT_FILES=(
       "docs/planning/phase-${PHASE}-foundation.md"
       "docs/planning/phase-${PHASE}-execution-guide.md" 
       "docs/planning/phase-${PHASE}-validation-checklist.md"
       "docs/planning/phase-${PHASE}-refinement-summary.md"
       "docs/planning/revised_project_plan.md"
   )
   
   # Check which files exist and are relevant
   AVAILABLE_CONTEXT=""
   for file in "${CONTEXT_FILES[@]}"; do
       if [[ -f "$file" ]]; then
           AVAILABLE_CONTEXT="$AVAILABLE_CONTEXT\n- $file"
       fi
   done
   
   echo "📚 Available project context:$AVAILABLE_CONTEXT"
   ```

2. **Issue Dependency Analysis**:
   ```bash
   # Extract dependencies from project documentation
   DEPENDENCIES=$(grep -A 5 -B 5 "P${PHASE}-$(printf "%03d" $ISSUE)" docs/planning/ | \
                  grep -oP "P\d+-\d+|Issue P\d+-\d+" | sort -u)
   
   echo "🔗 Issue dependencies identified: $DEPENDENCIES"
   ```

### Step 1: Context-Aware Action Plan Creation

1. **Project-Specific Scope Analysis**:
   - **Check Phase Execution Guide**: Reference existing step-by-step instructions
   - **Validate Against ADRs**: Ensure alignment with architectural decisions  
   - **Review Refinement Status**: Understand current completion state
   - **Assess Template Availability**: Use existing templates from `/docs/planning/phase-{X}-templates/`

2. **PP Security-Master Development Philosophy Integration**:
   ```markdown
   **Development Philosophy Adherence Check:**
   - [ ] **Reuse First**: Checked existing repositories (ledgerbase, FISProject, .github, PromptCraft)
   - [ ] **Configure Don't Build**: Leveraged Zen MCP Server, Heimdall MCP Server, AssuredOSS packages  
   - [ ] **Focus on Unique Value**: Built only what's truly unique to Portfolio Performance Security-Master
   - [ ] **Foundation First**: Ensured solid PostgreSQL/infrastructure foundation before features
   ```

### Step 2: Enhanced Scope Validation

1. **Multi-Document Cross-Reference**:
   ```bash
   # Cross-reference acceptance criteria across multiple docs
   ACCEPTANCE_CRITERIA_FILES=(
       "docs/planning/revised_project_plan.md"
       "docs/planning/phase-${PHASE}-foundation.md"
       "docs/planning/phase-${PHASE}-validation-checklist.md"
   )
   
   # Extract and compare acceptance criteria
   for file in "${ACCEPTANCE_CRITERIA_FILES[@]}"; do
       if [[ -f "$file" ]]; then
           echo "📋 Checking acceptance criteria in: $file"
           grep -A 10 -B 2 "P${PHASE}-$(printf "%03d" $ISSUE)" "$file" | \
           grep -E "\s*-\s*\[\s*\]|\s*✅|\s*❌"
       fi
   done
   ```

2. **Issue Interdependency Validation**:
   - Check if dependent issues (P0-001 → P0-004 → P0-005) are properly sequenced
   - Validate that prerequisites are met or documented
   - Ensure no circular dependencies in the plan

### Step 3: PP-Optimized Strategic Consultation

For expert mode, enhanced with project context:

```bash
if [[ "$MODE" == "expert" ]]; then
    echo "🧠 PP Security-Master Strategic Consultation using: $PLANNING_MODEL"
    
    # Comprehensive project context for strategic analysis
    STRATEGY_CONTEXT_PROMPT="
    Portfolio Performance Security-Master Project Context:
    - Multi-phase development approach with 6 phases
    - Foundation-first architecture (PostgreSQL 17 → Core features → Institution support)
    - Target: 95%+ classification accuracy for listed securities  
    - Integration with Portfolio Performance XML backup/restore
    - Institution support: Wells Fargo, IBKR, AltoIRA, Kubera
    - Performance target: Sub-30 second processing for 10,000+ transactions
    
    Current Phase: Phase ${PHASE} - $(get_phase_name $PHASE)
    Issue: P${PHASE}-$(printf "%03d" $ISSUE)
    Issue Status: $ISSUE_STATUS
    
    Available project documentation context: $AVAILABLE_CONTEXT
    Identified dependencies: $DEPENDENCIES
    
    Please review the implementation plan with this specific project context in mind.
    "
    
    # Use Zen MCP Server with comprehensive context
    zen_mcp_call "$PLANNING_MODEL" \
        --role "Portfolio Performance Security-Master Technical Architect" \
        --context "$STRATEGY_CONTEXT_PROMPT" \
        --input "issue-specific-requirements" \
        --request "Validate implementation plan scope and strategic alignment"
fi
```

### Step 4: Enhanced Final Validation

**PP Security-Master Specific Validation Checklist**:

- [ ] **Phase Alignment**: Plan aligns with phase-{X}-execution-guide.md
- [ ] **Dependency Chain**: All prerequisite issues addressed or validated  
- [ ] **Template Utilization**: Existing templates from phase-{X}-templates/ referenced
- [ ] **ADR Compliance**: Plan complies with relevant Architecture Decision Records
- [ ] **Performance Targets**: Plan supports sub-30 second processing goals
- [ ] **Institution Requirements**: Plan addresses multi-institution support where applicable
- [ ] **Classification Accuracy**: Plan supports 95%+ classification accuracy goals

## Enhanced Output Format

Generate file: `/docs/planning/issue-plans/phase-{phase}-issue-{issue}-plan.md`

```markdown
---
title: "Phase {X} Issue {Y}: [Issue Title]"  
version: "1.0"
status: "draft"
component: "Implementation-Plan"
tags: ["phase-{X}", "issue-{Y}", "implementation"]
purpose: "Implementation plan for resolving Phase {X} Issue {Y}"
pp_context: "security-master-service"
issue_status: "[COMPLETED|IN_PROGRESS|PLANNED]"
---

# Phase {X} Issue {Y}: [Issue Title]

## PP Security-Master Project Context
**Phase**: {X} - [Phase Name from phase-index.md]
**Issue Status**: [Current status from refinement summary]
**Dependencies**: [Auto-extracted from project docs]
**Related ADRs**: [Relevant architecture decisions]

## Scope Boundary Analysis
✅ **INCLUDED in Issue**: [Items from acceptance criteria across all relevant docs]
❌ **EXCLUDED from Issue**: [Items NOT in acceptance criteria]  
🔍 **Scope Validation**: [Cross-referenced against multiple project documents]

## Project Integration Analysis
- [ ] **Execution Guide Alignment**: Plan aligns with phase-{X}-execution-guide.md
- [ ] **Template Utilization**: Referenced available templates from phase-{X}-templates/
- [ ] **ADR Compliance**: Verified alignment with architectural decisions
- [ ] **Dependency Chain**: Validated prerequisite issues are addressed

## Issue Requirements
[Enhanced requirements analysis from multiple documentation sources]

## Action Plan Scope Validation  
[Enhanced validation against multiple project documents]

## Action Plan
[Implementation strategy with PP-specific context]

## Testing Strategy
[Validation approach aligned with PP quality standards]

## Dependencies and Prerequisites
[Enhanced dependency analysis with cross-references]

## Success Criteria
[How to know the issue is resolved - PP-specific metrics]
```

## Project-Specific Error Handling

- **Missing phase documentation**: Auto-suggest creating phase documentation first
- **Incomplete dependency chain**: Highlight missing prerequisite issues
- **Template mismatch**: Suggest available templates from phase-{X}-templates/
- **ADR conflicts**: Flag potential architectural decision conflicts

## Examples

```bash
# Standard plan with PP-optimized context
/project:workflow-plan-validation phase 1 issue 3

# Validation mode for completed issues (auto-detected)
/project:workflow-plan-validation phase 0 issue 1  # Auto-switches to validation mode

# Expert mode with PP-specific strategic context  
/project:workflow-plan-validation expert phase 2 issue 5 --planning-model=opus-4

# Quick plan with cost-optimized models
/project:workflow-plan-validation quick phase 1 issue 2 --model=gemini-flash
```

## Integration with PP Project Workflow

**Enhanced Next Steps After User Approval:**

1. **Phase Execution Integration**: 
   - Reference step-by-step commands from phase-{X}-execution-guide.md
   - Use validation checklists from phase-{X}-validation-checklist.md

2. **Template Integration**:
   - Auto-copy relevant templates from phase-{X}-templates/
   - Customize templates with project-specific values

3. **Progress Tracking**:
   - Update phase-{X}-refinement-summary.md with progress
   - Maintain issue dependency tracking across phases

This optimized version leverages the extensive documentation structure of the PP Security-Master project and provides much more contextual and accurate planning.