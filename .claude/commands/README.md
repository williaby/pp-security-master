# Custom Slash Commands for pp-security-master

This directory contains custom slash commands that extend the workflow capabilities for the pp-security-master project.

## Available Commands

### `/workflow-prepare-pr`

Prepare and create pull requests with comprehensive validation and safety checks.

**Usage:**

```bash
/workflow-prepare-pr [options] <phase> <issue>
```

**Examples:**

```bash
/workflow-prepare-pr 0 P0-001
/workflow-prepare-pr --dry-run --security 0 P0-003
/workflow-prepare-pr --target main --title "Phase 0 Complete" 0 P0-005
```

**Key Features:**

- Validates issue format (PX-XXX) and phase consistency
- Automatically determines appropriate target branch
- Repository context awareness
- Comprehensive security and performance analysis options
- Dry run capability for testing

### `/workflow-review-pr`

Review existing pull requests with comprehensive analysis and multi-agent validation.

**Usage:**

```bash
/workflow-review-pr [options] <pr_url>
```

**Examples:**

```bash
/workflow-review-pr https://github.com/byron/pp-security-master/pull/123
/workflow-review-pr --mode security-focus --security https://github.com/byron/pp-security-master/pull/456
/workflow-review-pr --consensus --submit --review-action approve https://github.com/byron/pp-security-master/pull/789
```

**Key Features:**

- Adaptive review modes (quick to comprehensive analysis)
- Security-focused and performance-focused analysis
- Multi-agent consensus capabilities
- Automated GitHub review submission
- Scales from 2-minute quick reviews to 25-minute comprehensive analysis

## Repository-Specific Adaptations

These commands have been specifically adapted for the pp-security-master project:

1. **Issue Format Validation**: Enforces the `PX-XXX` format used in this project (e.g., P0-001, P0-003)
2. **Phase-Based Branching**: Automatically determines target branches based on phase (Phase 0 → main)
3. **Repository Context**: Auto-detects repository information from git remote
4. **Change Logging**: Integrates with existing `claude-file-change-log.md` system

## Integration with MCP Tools

Both commands generate parameters for the underlying MCP tools:

- `mcp__zen__pr_prepare` for PR preparation
- `mcp__zen__pr_review` for PR review

The commands handle all the complexity of parameter validation and formatting, making it easy to use the powerful MCP PR tools with repository-specific configurations.

## Validation

All commands include comprehensive validation:

- Issue format validation
- Phase consistency checks
- Repository context detection
- Environment validation
- Parameter validation

## Testing

All commands support dry-run mode for testing:

```bash
/workflow-prepare-pr --dry-run 0 P0-001
```

This allows you to test the command configuration without actually creating PRs or making changes.
