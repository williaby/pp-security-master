#!/usr/bin/env python3
"""
Workflow Review PR Command
==========================
Custom slash command: `/project:workflow-review-pr`
Reviews existing pull requests with comprehensive analysis and multi-agent validation.
Integrates with the existing workflow system and follows project standards.
Usage:
        /project:workflow-review-pr [options] <pr_url>
Options:
    --mode <mode>               Review mode (adaptive, quick, thorough, security-focus, performance-focus)
    --consensus                 Enable multi-agent consensus analysis
    --security                  Enable additional security analysis
    --performance               Enable performance optimization analysis
    --output-file <path>        Custom path for markdown output file
    --max-files <num>           Maximum number of files to analyze (default: 50)
    --submit                    Submit review to GitHub (draft by default)
    --review-action <action>    GitHub review action (approve, request_changes, comment)
    --force-multi-agent         Force multi-agent analysis even for simple cases
    --skip-quality-gates        Skip automated quality checks
    --use-sampling              Force sampling strategy for large PRs
Examples:
    /project:workflow-review-pr https://github.com/byron/pp-security-master/pull/123
        /project:workflow-review-pr --mode security-focus --security https://github.com/byron/pp-security-master/pull/123
    /project:workflow-review-pr --consensus --submit --review-action approve https://github.com/byron/pp-security-master/pull/123
    /project:workflow-review-pr --mode quick --max-files 20 https://github.com/byron/pp-security-master/pull/123
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the workflow review PR command.

    Returns:
        The result.
    """
    parser = argparse.ArgumentParser(
        description="Review pull requests with comprehensive analysis and multi-agent validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # Core arguments
    parser.add_argument("pr_url", type=str, help="GitHub PR URL to review")
    # Review mode options
    parser.add_argument(
        "--mode",
        type=str,
        choices=[
            "adaptive",
            "quick",
            "thorough",
            "security-focus",
            "performance-focus",
        ],
        default="adaptive",
        help="Review mode - adaptive scales based on complexity (default: adaptive)",
    )
    parser.add_argument(
        "--consensus",
        action="store_true",
        help="Enable multi-agent consensus analysis",
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Enable additional security analysis",
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Enable performance optimization analysis",
    )
    # Output options
    parser.add_argument(
        "--output-file",
        type=str,
        help="Custom path for markdown output file (auto-generated if not provided)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=50,
        help="Maximum number of files to analyze (default: 50)",
    )
    parser.add_argument(
        "--no-output-file",
        action="store_true",
        help="Skip saving detailed review report to markdown file",
    )
    # GitHub integration options
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit review to GitHub (draft by default)",
    )
    parser.add_argument(
        "--review-action",
        type=str,
        choices=["approve", "request_changes", "comment"],
        default="comment",
        help="GitHub review action (default: comment)",
    )
    parser.add_argument(
        "--no-fix-commands",
        action="store_true",
        help="Exclude copy-paste fix commands from review",
    )
    # Advanced options
    parser.add_argument(
        "--force-multi-agent",
        action="store_true",
        help="Force multi-agent analysis even for simple cases",
    )
    parser.add_argument(
        "--skip-quality-gates",
        action="store_true",
        help="Skip automated quality checks",
    )
    parser.add_argument(
        "--use-sampling",
        action="store_true",
        help="Force sampling strategy for large PRs",
    )
    parser.add_argument(
        "--consensus-model",
        type=str,
        choices=["auto", "lightweight", "comprehensive"],
        default="auto",
        help="Consensus model selection (default: auto)",
    )
    return parser.parse_args()


def validate_pr_url(url: str) -> bool:
    """Validate that the provided URL is a valid GitHub PR URL.

    Args:
        url: The url value.

    Returns:
        The result.
    """
    try:
        parsed = urlparse(url)
        if parsed.netloc != "github.com":
            print(f"❌ URL must be a GitHub URL, got: {parsed.netloc}")
            return False
        # Check for PR pattern: /owner/repo/pull/number
        pr_pattern = r"/[^/]+/[^/]+/pull/\d+$"
        if not re.search(pr_pattern, parsed.path):
            print(
                "❌ URL must be a GitHub PR URL (format: https://github.com/owner/repo/pull/123)",
            )
            return False
    except (ValueError, TypeError) as e:
        print(f"❌ Invalid URL format: {e}")
        return False
    else:
        return True


def extract_pr_info(url: str) -> dict[str, str]:
    """Extract PR information from the URL.

    Args:
        url: The url value.

    Returns:
        The result.
    """
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    return {
        "owner": parts[0],
        "repo": parts[1],
        "pr_number": parts[3],
        "full_name": f"{parts[0]}/{parts[1]}",
    }


def build_mcp_params(args: argparse.Namespace) -> dict[str, Any]:
    """Build parameters for the MCP pr_review function.

    Args:
        args: The args value.

    Returns:
        The result.
    """
    params = {
        "pr_url": args.pr_url,
        "mode": args.mode,
        "focus_security": args.security,
        "focus_performance": args.performance,
        "max_files_analyzed": args.max_files,
        "output_to_file": not args.no_output_file,
        "submit_review": args.submit,
        "review_action": args.review_action,
        "include_fix_commands": not args.no_fix_commands,
        "force_multi_agent": args.force_multi_agent or args.consensus,
        "skip_quality_gates": args.skip_quality_gates,
        "use_sampling": args.use_sampling,
        "consensus_model": args.consensus_model if args.consensus else "auto",
    }
    # Add optional parameters if provided
    if args.output_file:
        params["output_file_path"] = args.output_file
    return params


def log_change(pr_info: dict[str, str], action: str, details: str) -> None:
    """Log the workflow action to the change log.

    Args:
        pr_info: The pr info value.
        action: The action value.
        details: The details value.
    """
    log_file = Path("docs/planning/claude-file-change-log.md")
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
    if not log_file.exists():
        log_file.write_text("# Claude File Change Log\n\n")
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"## {timestamp} - {action}\n"
    log_entry += (
        f"**Repository**: {pr_info['full_name']} | **PR**: #{pr_info['pr_number']}\n"
    )
    log_entry += f"**Details**: {details}\n\n"
    # Append to log file
    with log_file.open("a", encoding="utf-8") as f:
        f.write(log_entry)


def validate_environment() -> bool:
    """Validate that the environment is ready for PR review.

    Returns:
        The result.
    """
    print("🔍 Validating environment...")
    # Check if we have GitHub CLI available (for potential PR operations)
    import shutil

    if not shutil.which("gh"):
        print("⚠️  GitHub CLI (gh) not found - some features may be limited")
    else:
        print("✅ GitHub CLI available")
    print("✅ Environment validation passed")
    return True


def main() -> int:
    """Main entry point for the workflow review PR command.

    Returns:
        The result.
    """
    args = parse_arguments()
    print(f"🔍 Starting PR review for: {args.pr_url}")
    # Validate PR URL
    if not validate_pr_url(args.pr_url):
        return 1
    # Extract PR information
    pr_info = extract_pr_info(args.pr_url)
    print(f"📋 Reviewing PR #{pr_info['pr_number']} in {pr_info['full_name']}")
    # Validate environment
    if not validate_environment():
        return 1
    # Build MCP parameters
    mcp_params = build_mcp_params(args)
    # Log the action
    action = "PR Review Analysis"
    details = f"Mode: {args.mode}"
    if args.security:
        details += ", Security analysis enabled"
    if args.performance:
        details += ", Performance analysis enabled"
    if args.consensus:
        details += ", Multi-agent consensus enabled"
    if args.submit:
        details += f", Will submit review ({args.review_action})"
    log_change(pr_info, action, details)
    # Print what would be executed
    print("📋 Review Configuration:")
    print(f"   Mode: {args.mode}")
    print(f"   Max Files: {args.max_files}")
    print(f"   Security Focus: {args.security}")
    print(f"   Performance Focus: {args.performance}")
    print(f"   Multi-Agent: {args.consensus or args.force_multi_agent}")
    print(f"   Submit Review: {args.submit}")
    if args.submit:
        print(f"   Review Action: {args.review_action}")
    print("\n🔧 MCP Parameters:")
    for key, value in mcp_params.items():
        print(f"   {key}: {value}")
    print(
        "\n🔧 To execute this command, use the MCP pr_review tool with these parameters:",
    )
    print(
        "   mcp__zen__pr_review("
        + ", ".join(f"{k}={v!r}" for k, v in mcp_params.items())
        + ")",
    )
    print(f"\n🎯 Ready to review PR #{pr_info['pr_number']} in {pr_info['full_name']}")
    print("💡 Use Claude Code with the MCP pr_review tool to execute this review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
