---
category: workflow
complexity: medium
estimated_time: "5-10 minutes"
dependencies: []
sub_commands: []
version: "1.0"
---

# Workflow Prepare PR

Prepare and create pull requests with comprehensive validation and safety checks for pp-security-master: $ARGUMENTS

## Usage Options

- `<phase> <issue>` - Standard PR preparation with validation
- `--dry-run <phase> <issue>` - Validation only, no actual PR creation
- `--security <phase> <issue>` - Enhanced security analysis during preparation
- `--target <branch> <phase> <issue>` - Override default target branch
- `--title "<title>" <phase> <issue>` - Custom PR title

## Prerequisites

- Valid git repository with remote origin
- Issue format must follow PX-XXX pattern (e.g., P0-001, P0-003)
- Phase number must match issue prefix

## Instructions

This command prepares pull requests with repository-specific validation and intelligent defaults for the pp-security-master project.

### Step 1: Parse and Validate Arguments

```python
import sys
import subprocess
import re
from pathlib import Path

def main():
    args = sys.argv[1:]  # Get arguments from $ARGUMENTS
    
    # Parse options and arguments
    dry_run = "--dry-run" in args
    security = "--security" in args
    performance = "--performance" in args
    
    # Extract target branch if specified
    target = "auto"
    if "--target" in args:
        target_idx = args.index("--target")
        target = args[target_idx + 1] if target_idx + 1 < len(args) else "auto"
    
    # Extract title if specified
    title = None
    if "--title" in args:
        title_idx = args.index("--title")
        title = args[title_idx + 1] if title_idx + 1 < len(args) else None
    
    # Get phase and issue (last two arguments)
    phase = args[-2]
    issue = args[-1]
    
    print(f"🚀 Starting workflow prepare PR for Phase {phase}, Issue {issue}")
    
    # Validate issue format for pp-security-master
    issue_pattern = re.compile(r'^P\d+-\d{3}$')
    if not issue_pattern.match(issue):
        print(f"❌ Issue format should be PX-XXX (e.g., P0-001), got: {issue}")
        return 1
    
    # Extract phase from issue and validate consistency
    issue_phase = issue.split('-')[0][1:]  # Extract phase number from P0-001 -> 0
    if phase != issue_phase:
        print(f"❌ Phase mismatch: phase={phase}, issue phase={issue_phase}")
        return 1
    
    # Determine appropriate target branch
    if target == "auto":
        if phase == "0":
            target = "main"  # Phase 0 foundation work targets main
        else:
            # Check if phase branch exists
            try:
                subprocess.check_output(
                    ["git", "rev-parse", "--verify", f"origin/phase-{phase}-development"],
                    stderr=subprocess.DEVNULL
                )
                target = f"phase-{phase}-development"
            except subprocess.CalledProcessError:
                target = "main"
    
    # Get repository information
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True
        ).strip()
        
        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                repo_part = remote_url.split(":")[-1].replace(".git", "")
            else:
                repo_part = remote_url.split("github.com/")[-1].replace(".git", "")
            
            owner, repo = repo_part.split("/")
            repo_info = f"{owner}/{repo}"
        else:
            repo_info = "byron/pp-security-master"
    except subprocess.CalledProcessError:
        repo_info = "byron/pp-security-master"
    
    print(f"📂 Repository: {repo_info}")
    print(f"🎯 Target branch: {target}")
    
    # Log the action
    log_file = Path("docs/planning/claude-file-change-log.md")
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not log_file.exists():
        log_file.write_text("# Claude File Change Log\n\n")
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    action = "PR Preparation (Dry Run)" if dry_run else "PR Creation"
    details = f"Target: {target}, Type: feat"
    if security:
        details += ", Security analysis enabled"
    if performance:
        details += ", Performance analysis enabled"
    
    log_entry = f"## {timestamp} - {action}\n"
    log_entry += f"**Phase**: {phase} | **Issue**: {issue}\n"
    log_entry += f"**Details**: {details}\n\n"
    
    with log_file.open("a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # Build MCP parameters
    mcp_params = {
        "dry_run": dry_run,
        "no_push": True,  # Safe default
        "include_wtd": True,
        "security": security,
        "performance": performance,
        "target_branch": target,
        "base_branch": "auto",
        "change_type": "feat",
        "breaking": False,
        "phase_merge": False,
        "skip_deps": False,
        "create_pr": not dry_run,
    }
    
    if title:
        mcp_params["title"] = title
    
    print("📋 MCP Parameters:")
    for key, value in mcp_params.items():
        print(f"   {key}: {value}")
    
    print("\n🔧 To execute this command, call the MCP pr_prepare tool:")
    print("mcp__zen__pr_prepare(" + ", ".join(f"{k}={repr(v)}" for k, v in mcp_params.items()) + ")")
    
    if dry_run:
        print("\n✅ Dry run completed successfully")
        return 0
    
    print(f"\n🎯 Ready to create PR for Phase {phase}, Issue {issue}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Step 2: Execute MCP Tool

Use the generated parameters to call the MCP pr_prepare tool with the validated and repository-specific configuration.

## Examples

```bash
/workflow-prepare-pr 0 P0-001
/workflow-prepare-pr --dry-run --security 0 P0-003
/workflow-prepare-pr --target main --title "Phase 0 Complete" 0 P0-005
```

## Key Features

- **Issue Format Validation**: Enforces PX-XXX format used in pp-security-master
- **Phase Consistency**: Validates phase numbers match issue prefixes
- **Smart Branch Targeting**: Phase 0 → main, later phases → phase-X-development
- **Repository Context**: Auto-detects repository information
- **Change Logging**: Integrates with existing claude-file-change-log.md
- **Dry Run Support**: Test configuration without creating PRs
