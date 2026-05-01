---
category: workflow
complexity: medium
estimated_time: "5-25 minutes (adaptive)"
dependencies: []
sub_commands: []
version: "1.0"
---

# Workflow Review PR

Review existing pull requests with comprehensive analysis and multi-agent validation for pp-security-master: $ARGUMENTS

## Usage Options

- `<pr_url>` - Adaptive review mode (scales based on complexity)
- `--mode security-focus <pr_url>` - Deep security analysis and vulnerability detection
- `--mode performance-focus <pr_url>` - Performance optimization analysis
- `--consensus <pr_url>` - Multi-agent consensus review
- `--submit --review-action approve <pr_url>` - Submit review to GitHub
- `--max-files <num> <pr_url>` - Limit number of files analyzed

## Prerequisites

- Valid GitHub PR URL
- GitHub CLI (gh) recommended for enhanced features
- PR must be from a public repository or one you have access to

## Instructions

This command reviews pull requests with comprehensive analysis, scaling from quick 2-minute reviews to detailed 25-minute assessments.

### Step 1: Parse and Validate Arguments

```python
import sys
import re
from pathlib import Path
from urllib.parse import urlparse

def main():
    args = sys.argv[1:]  # Get arguments from $ARGUMENTS
    
    if not args:
        print("❌ PR URL is required")
        return 1
    
    # Parse options
    mode = "adaptive"
    consensus = "--consensus" in args
    security = "--security" in args
    performance = "--performance" in args
    submit = "--submit" in args
    
    # Extract mode if specified
    if "--mode" in args:
        mode_idx = args.index("--mode")
        mode = args[mode_idx + 1] if mode_idx + 1 < len(args) else "adaptive"
    
    # Extract review action if specified
    review_action = "comment"
    if "--review-action" in args:
        action_idx = args.index("--review-action")
        review_action = args[action_idx + 1] if action_idx + 1 < len(args) else "comment"
    
    # Extract max files if specified
    max_files = 50
    if "--max-files" in args:
        max_idx = args.index("--max-files")
        try:
            max_files = int(args[max_idx + 1]) if max_idx + 1 < len(args) else 50
        except ValueError:
            max_files = 50
    
    # Get PR URL (last argument)
    pr_url = args[-1]
    
    print(f"🔍 Starting PR review for: {pr_url}")
    
    # Validate PR URL
    try:
        parsed = urlparse(pr_url)
        if parsed.netloc != "github.com":
            print(f"❌ URL must be a GitHub URL, got: {parsed.netloc}")
            return 1
        
        # Check for PR pattern: /owner/repo/pull/number
        pr_pattern = r"/[^/]+/[^/]+/pull/\d+$"
        if not re.search(pr_pattern, parsed.path):
            print("❌ URL must be a GitHub PR URL (format: https://github.com/owner/repo/pull/123)")
            return 1
            
    except Exception as e:
        print(f"❌ Invalid URL format: {e}")
        return 1
    
    # Extract PR information
    parts = parsed.path.strip("/").split("/")
    pr_info = {
        "owner": parts[0],
        "repo": parts[1], 
        "pr_number": parts[3],
        "full_name": f"{parts[0]}/{parts[1]}"
    }
    
    print(f"📋 Reviewing PR #{pr_info['pr_number']} in {pr_info['full_name']}")
    
    # Log the action
    log_file = Path("docs/planning/claude-file-change-log.md")
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not log_file.exists():
        log_file.write_text("# Claude File Change Log\n\n")
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    action = "PR Review Analysis"
    details = f"Mode: {mode}"
    if security:
        details += ", Security analysis enabled"
    if performance:
        details += ", Performance analysis enabled"
    if consensus:
        details += ", Multi-agent consensus enabled"
    if submit:
        details += f", Will submit review ({review_action})"
    
    log_entry = f"## {timestamp} - {action}\n"
    log_entry += f"**Repository**: {pr_info['full_name']} | **PR**: #{pr_info['pr_number']}\n"
    log_entry += f"**Details**: {details}\n\n"
    
    with log_file.open("a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # Build MCP parameters
    mcp_params = {
        "pr_url": pr_url,
        "mode": mode,
        "focus_security": security,
        "focus_performance": performance,
        "max_files_analyzed": max_files,
        "output_to_file": True,
        "submit_review": submit,
        "review_action": review_action,
        "include_fix_commands": True,
        "force_multi_agent": consensus,
        "skip_quality_gates": False,
        "use_sampling": False,
        "consensus_model": "auto" if consensus else "auto",
    }
    
    print("📋 Review Configuration:")
    print(f"   Mode: {mode}")
    print(f"   Max Files: {max_files}")
    print(f"   Security Focus: {security}")
    print(f"   Performance Focus: {performance}")
    print(f"   Multi-Agent: {consensus}")
    print(f"   Submit Review: {submit}")
    if submit:
        print(f"   Review Action: {review_action}")
    
    print("\n🔧 MCP Parameters:")
    for key, value in mcp_params.items():
        print(f"   {key}: {value}")
    
    print("\n🔧 To execute this command, call the MCP pr_review tool:")
    print("mcp__zen__pr_review(" + ", ".join(f"{k}={repr(v)}" for k, v in mcp_params.items()) + ")")
    
    print(f"\n🎯 Ready to review PR #{pr_info['pr_number']} in {pr_info['full_name']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Step 2: Execute MCP Tool

Use the generated parameters to call the MCP pr_review tool with the validated configuration.

## Examples

```bash
/workflow-review-pr https://github.com/byron/pp-security-master/pull/123
/workflow-review-pr --mode security-focus --security https://github.com/byron/pp-security-master/pull/456
/workflow-review-pr --consensus --submit --review-action approve https://github.com/byron/pp-security-master/pull/789
/workflow-review-pr --mode quick --max-files 20 https://github.com/byron/pp-security-master/pull/123
```

## Key Features

- **Adaptive Scaling**: 2-minute quick reviews to 25-minute comprehensive analysis
- **Security Focus**: OWASP compliance checks and vulnerability detection
- **Performance Analysis**: Performance optimization recommendations
- **Multi-Agent Consensus**: Enhanced validation with multiple expert perspectives
- **GitHub Integration**: Automated review submission with configurable actions
- **Repository Context**: Understands pp-security-master project structure
- **Change Logging**: Tracks all review activities in project log
