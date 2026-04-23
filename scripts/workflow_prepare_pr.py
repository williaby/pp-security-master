#!/usr/bin/env python3
"""
Workflow Prepare PR Command
===========================
Custom slash command: `/project:workflow-prepare-pr`
Prepares and creates pull requests with comprehensive validation and safety checks.
Integrates with the existing workflow system and follows project standards.
Usage:
    /project:workflow-prepare-pr [options] <phase> <issue>
Options:
    --dry-run          Run validation only, don't create PR
    --force-push       Override automatic push safety checks
    --no-wtd           Skip WhatTheDiff summary inclusion
    --security         Enable additional security analysis
    --performance      Enable performance impact analysis
    --target <branch>  Override default target branch (auto-detect from phase)
    --title <title>    Custom PR title (auto-generate if not provided)
Examples:
    /project:workflow-prepare-pr 0 P0-001
    /project:workflow-prepare-pr --dry-run --security 0 P0-003
    /project:workflow-prepare-pr --target main --title "Phase 0 Complete" 0 P0-005
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the workflow prepare PR command."""
    parser = argparse.ArgumentParser(
        description="Prepare and create pull requests with comprehensive validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # Core arguments
    parser.add_argument("phase", type=str, help="Phase number or identifier")
    parser.add_argument("issue", type=str, help="Issue number or identifier")
    # PR options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run validation only, don't create PR",
    )
    parser.add_argument(
        "--force-push",
        action="store_true",
        help="Override automatic push safety checks",
    )
    parser.add_argument(
        "--no-wtd",
        action="store_true",
        help="Skip WhatTheDiff summary inclusion",
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Enable additional security analysis",
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Enable performance impact analysis",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="auto",
        help="Override default target branch (default: auto-detect from phase)",
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Custom PR title (auto-generate if not provided)",
    )
    parser.add_argument(
        "--base",
        type=str,
        default="auto",
        help="Base branch for comparison (default: auto-detect)",
    )
    # Change type options
    parser.add_argument(
        "--change-type",
        type=str,
        choices=[
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "perf",
            "test",
            "chore",
            "build",
            "ci",
        ],
        default="feat",
        help="Type of change (default: feat)",
    )
    parser.add_argument(
        "--breaking",
        action="store_true",
        help="Contains breaking changes",
    )
    parser.add_argument("--issue-number", type=int, help="Related issue number")
    # Advanced options
    parser.add_argument(
        "--phase-merge",
        action="store_true",
        help="Phase completion PR targeting main",
    )
    parser.add_argument(
        "--phase-number",
        type=int,
        help="Phase number for phase-based development",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency validation and requirements generation",
    )
    return parser.parse_args()


def validate_issue_format(phase: str, issue: str) -> bool:
    """Validate issue format matches pp-security-master patterns (PX-XXX)."""
    # Check if issue follows PX-XXX format
    issue_pattern = re.compile(r"^P\d+-\d{3}$")
    if not issue_pattern.match(issue):
        print(f"❌ Issue format should be PX-XXX (e.g., P0-001), got: {issue}")
        return False
    # Extract phase from issue and validate consistency
    issue_phase = issue.split("-")[0][1:]  # Extract phase number from P0-001 -> 0
    if phase != issue_phase:
        print(f"❌ Phase mismatch: phase={phase}, issue phase={issue_phase}")
        return False
    return True


def determine_target_branch(phase: str, target: str) -> str:
    """Determine appropriate target branch based on phase and current branch."""
    if target != "auto":
        return target
    # For pp-security-master, phase 0 work typically targets main
    # Later phases might target phase-specific branches
    try:
        subprocess.check_output(
            ["git", "branch", "--show-current"],
            text=True,
        ).strip()
        if phase == "0":
            # Phase 0 foundation work typically targets main
            return "main"
        # Later phases might have dedicated development branches
        phase_branch = f"phase-{phase}-development"
        # Check if phase branch exists
        try:
            subprocess.check_output(
                ["git", "rev-parse", "--verify", f"origin/{phase_branch}"],
                stderr=subprocess.DEVNULL,
            )
            return phase_branch
        except subprocess.CalledProcessError:
            # Fall back to main if phase branch doesn't exist
            return "main"
    except subprocess.CalledProcessError:
        return "main"


def get_repository_info() -> dict[str, str]:
    """Get repository information from git remote."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
        ).strip()
        # Only handle valid GitHub URLs by parsing the host field
        owner = repo = None
        if remote_url.startswith("git@"):
            # SSH format: git@github.com:owner/repo.git
            # Split on '@', then ':'
            _user_host, path_part = remote_url.split("@", 1)
            if path_part.startswith("github.com:"):
                repo_part = path_part[len("github.com:") :].replace(".git", "")
                if "/" in repo_part:
                    owner, repo = repo_part.split("/", 1)
        else:
            # HTTPS or git protocol, try to parse the URL
            parsed = urlparse(remote_url)
            if parsed.hostname == "github.com":
                # parsed.path starts with /, so skip it
                repo_part = parsed.path.lstrip("/").replace(".git", "")
                if "/" in repo_part:
                    owner, repo = repo_part.split("/", 1)
        if owner and repo:
            return {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}",
            }
    except subprocess.CalledProcessError:
        pass
    # Default fallback for pp-security-master
    return {
        "owner": "byron",
        "repo": "pp-security-master",
        "full_name": "byron/pp-security-master",
        "url": "https://github.com/byron/pp-security-master",
    }


def build_mcp_params(args: argparse.Namespace) -> dict[str, Any]:
    """Build parameters for the MCP pr_prepare function."""
    params = {
        "dry_run": args.dry_run,
        "no_push": not args.force_push,  # Invert logic - no_push is opposite of force_push
        "include_wtd": not args.no_wtd,  # Invert logic - include_wtd is opposite of no_wtd
        "security": args.security,
        "performance": args.performance,
        "target_branch": args.target,
        "base_branch": args.base,
        "change_type": args.change_type,
        "breaking": args.breaking,
        "phase_merge": args.phase_merge,
        "skip_deps": args.skip_deps,
        "create_pr": not args.dry_run,  # Only create PR if not dry run
    }
    # Add optional parameters if provided
    if args.title and args.title != "auto":
        params["title"] = args.title
    if args.issue_number:
        params["issue_number"] = args.issue_number
    if args.phase_number:
        params["phase_number"] = args.phase_number
    return params


def log_change(phase: str, issue: str, action: str, details: str) -> None:
    """Log the workflow action to the change log."""
    log_file = Path("docs/planning/claude-file-change-log.md")
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
    if not log_file.exists():
        log_file.write_text("# Claude File Change Log\n\n")
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"## {timestamp} - {action}\n"
    log_entry += f"**Phase**: {phase} | **Issue**: {issue}\n"
    log_entry += f"**Details**: {details}\n\n"
    # Append to log file
    with log_file.open("a", encoding="utf-8") as f:
        f.write(log_entry)


def validate_environment() -> bool:
    """Validate that the environment is ready for PR creation."""
    print("🔍 Validating environment...")
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("❌ Not in a git repository")
        return False
    # Check if we have the required MCP tools available
    # This would typically be validated by the actual MCP call
    print("✅ Environment validation passed")
    return True


def main() -> int:
    """Main entry point for the workflow prepare PR command."""
    args = parse_arguments()
    print(f"🚀 Starting workflow prepare PR for Phase {args.phase}, Issue {args.issue}")
    # Validate issue format for pp-security-master
    if not validate_issue_format(args.phase, args.issue):
        return 1
    # Determine appropriate target branch
    target_branch = determine_target_branch(args.phase, args.target)
    args.target = target_branch
    # Get repository information
    repo_info = get_repository_info()
    print(f"📂 Repository: {repo_info['full_name']}")
    print(f"🎯 Target branch: {target_branch}")
    # Validate environment
    if not validate_environment():
        return 1
    # Build MCP parameters
    mcp_params = build_mcp_params(args)
    # Log the action
    action = "PR Preparation (Dry Run)" if args.dry_run else "PR Creation"
    details = f"Target: {args.target}, Type: {args.change_type}"
    if args.security:
        details += ", Security analysis enabled"
    if args.performance:
        details += ", Performance analysis enabled"
    log_change(args.phase, args.issue, action, details)
    # Print what would be executed
    print("📋 MCP Parameters:")
    for key, value in mcp_params.items():
        print(f"   {key}: {value}")
    print(
        "\n🔧 To execute this command, use the MCP pr_prepare tool with these parameters:",
    )
    print(
        "   mcp__zen__pr_prepare("
        + ", ".join(f"{k}={v!r}" for k, v in mcp_params.items())
        + ")",
    )
    if args.dry_run:
        print("\n✅ Dry run completed successfully")
        return 0
    print(f"\n🎯 Ready to create PR for Phase {args.phase}, Issue {args.issue}")
    print("💡 Use Claude Code with the MCP pr_prepare tool to execute this preparation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
