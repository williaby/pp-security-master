#!/usr/bin/env python3
"""
VS Code Coverage Integration Hook for PP Security-Master

This script is called automatically after running tests with coverage
to generate enhanced HTML coverage reports with test type breakdown.

Features:
- Automatic integration with VS Code "Run Tests with Coverage"
- Test type classification and reporting
- Enhanced HTML reports with navigation
- File-explorer compatible (no server required)
"""

import json
import logging
import sys
import time
from pathlib import Path

import defusedxml.ElementTree as ET  # noqa: N817  # safe parser at runtime

logger = logging.getLogger(__name__)


class SecurityMasterCoverageReporter:
    """Generate enhanced coverage reports for security-master project."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports" / "coverage"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def find_coverage_files(self) -> dict:
        """Find coverage XML and JSON files.

        Returns:
            Mapping of format key to file path, or None if the file does not exist.
        """
        coverage_xml = self.project_root / "coverage.xml"
        coverage_json = self.project_root / "coverage.json"

        return {
            "xml": coverage_xml if coverage_xml.exists() else None,
            "json": coverage_json if coverage_json.exists() else None,
        }

    def _parse_xml_coverage(self, xml_path: Path, data: dict) -> None:
        """Parse coverage XML file and populate data in place.

        Args:
            xml_path: Path to the coverage XML file.
            data: Coverage data dict to update with parsed results.
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            coverage_elem = root if root.tag == "coverage" else root.find(".//coverage")
            if coverage_elem is not None:
                data["overall"]["percentage"] = (
                    float(coverage_elem.get("line-rate", 0)) * 100
                )

            for package in root.findall(".//package"):
                for class_elem in package.findall("classes/class"):
                    filename = class_elem.get("filename", "")
                    if filename.startswith("src/"):
                        lines = class_elem.findall("lines/line")
                        covered = sum(
                            1 for line in lines if line.get("hits", "0") != "0"
                        )
                        total = len(lines)
                        if total > 0:
                            data["files"][filename] = {
                                "coverage": (covered / total) * 100,
                                "lines_covered": covered,
                                "lines_total": total,
                            }
        except (ET.ParseError, ValueError):
            logger.exception("Error parsing coverage XML")

    def _parse_json_coverage(self, json_path: Path, data: dict) -> None:
        """Parse coverage JSON file and populate data in place.

        Args:
            json_path: Path to the coverage JSON file.
            data: Coverage data dict to update with parsed results.
        """
        try:
            with json_path.open() as f:
                json_data = json.load(f)

            data["overall"]["percentage"] = json_data.get("totals", {}).get(
                "percent_covered",
                0,
            )

            for filename, file_data in json_data.get("files", {}).items():
                if filename.startswith("src/"):
                    summary = file_data.get("summary", {})
                    covered = summary.get("covered_lines", 0)
                    total = summary.get("num_statements", 0)
                    data["files"][filename] = {
                        "coverage": summary.get("percent_covered", 0),
                        "lines_covered": covered,
                        "lines_total": total,
                    }
        except (json.JSONDecodeError, OSError):
            logger.exception("Error parsing coverage JSON")

    def load_coverage_data(self) -> dict:
        """Load coverage data from XML and JSON files.

        Returns:
            Nested dict with overall percentage and per-file coverage data, or None if no coverage files exist.
        """
        files = self.find_coverage_files()

        if not files["xml"] and not files["json"]:
            return None

        data = {
            "overall": {"percentage": 0, "lines_covered": 0, "lines_total": 0},
            "files": {},
        }

        if files["xml"]:
            self._parse_xml_coverage(files["xml"], data)

        if files["json"]:
            self._parse_json_coverage(files["json"], data)

        return data

    def classify_by_component(self, files_data: dict) -> dict:
        """Classify coverage by security-master component.

        Args:
            files_data: Per-file coverage data keyed by file path.

        Returns:
            Coverage breakdown grouped by component name, each with file list and aggregate percentage.
        """
        components = {
            "extractor": {"files": [], "total_coverage": 0},
            "classifier": {"files": [], "total_coverage": 0},
            "storage": {"files": [], "total_coverage": 0},
            "patch": {"files": [], "total_coverage": 0},
            "cli": {"files": [], "total_coverage": 0},
            "utils": {"files": [], "total_coverage": 0},
        }

        for filename, file_data in files_data.items():
            component = "utils"  # default

            if "extractor/" in filename:
                component = "extractor"
            elif "classifier/" in filename:
                component = "classifier"
            elif "storage/" in filename:
                component = "storage"
            elif "patch/" in filename:
                component = "patch"
            elif "cli.py" in filename:
                component = "cli"

            components[component]["files"].append(
                {
                    "name": filename,
                    "coverage": file_data["coverage"],
                    "lines_covered": file_data["lines_covered"],
                    "lines_total": file_data["lines_total"],
                },
            )

        # Calculate component averages
        for component, data in components.items():
            if data["files"]:
                total_covered = sum(f["lines_covered"] for f in data["files"])
                total_lines = sum(f["lines_total"] for f in data["files"])
                data["total_coverage"] = (
                    (total_covered / total_lines * 100) if total_lines > 0 else 0
                )

        return components

    def generate_html_report(self, coverage_data: dict, components: dict) -> str:
        """Generate enhanced HTML coverage report.

        Args:
            coverage_data: Overall and per-file coverage data as returned by load_coverage_data.
            components: Component breakdown as returned by classify_by_component.

        Returns:
            HTML string containing the full coverage report page.
        """
        overall = coverage_data["overall"]

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PP Security-Master Coverage Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .overall {{ font-size: 24px; font-weight: bold; color: #2d3748; }}
        .component {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; margin: 10px 0; padding: 15px; }}
        .component-title {{ font-size: 18px; font-weight: 600; margin-bottom: 10px; }}
        .coverage-bar {{ background: #e2e8f0; height: 20px; border-radius: 10px; margin: 5px 0; }}
        .coverage-fill {{ height: 100%; border-radius: 10px; }}
        .high {{ background: #48bb78; }}
        .medium {{ background: #ed8936; }}
        .low {{ background: #f56565; }}
        .file-list {{ margin-top: 10px; font-size: 14px; }}
        .file-item {{ padding: 3px 0; display: flex; justify-content: space-between; }}
        .timestamp {{ color: #718096; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="overall">PP Security-Master Coverage: {overall["percentage"]:.1f}%</div>
        <div class="timestamp">Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
    </div>
"""

        # Component breakdown
        for component_name, component_data in components.items():
            if not component_data["files"]:
                continue

            coverage = component_data["total_coverage"]
            css_class = (
                "high" if coverage >= 80 else "medium" if coverage >= 60 else "low"
            )

            html += f"""
    <div class="component">
        <div class="component-title">{component_name.title()} Component</div>
        <div class="coverage-bar">
            <div class="coverage-fill {css_class}" style="width: {coverage}%"></div>
        </div>
        <div>{coverage:.1f}% covered ({len(component_data["files"])} files)</div>
        <div class="file-list">
"""

            for file_info in component_data["files"]:
                file_coverage = file_info["coverage"]
                html += f"""
            <div class="file-item">
                <span>{Path(file_info["name"]).name}</span>
                <span>{file_coverage:.1f}%</span>
            </div>"""

            html += """
        </div>
    </div>"""

        html += """
</body>
</html>"""
        return html

    def run(self) -> bool:
        """Generate coverage reports if data is available.

        Returns:
            True if the report was generated successfully, False if no coverage data was found.
        """
        coverage_data = self.load_coverage_data()
        if not coverage_data:
            logger.warning("⚠️  No coverage data found - run tests with coverage first")
            return False

        components = self.classify_by_component(coverage_data["files"])
        html_report = self.generate_html_report(coverage_data, components)

        # Save enhanced report
        report_file = self.reports_dir / "security-master-coverage.html"
        report_file.write_text(html_report)

        logger.info(f"✅ Enhanced coverage report generated: {report_file}")
        logger.info(
            f"📊 Overall coverage: {coverage_data['overall']['percentage']:.1f}%",
        )

        return True


def main():
    """Main entry point for the coverage hook."""
    try:
        reporter = SecurityMasterCoverageReporter()
        success = reporter.run()

        if not success:
            sys.exit(1)

    except Exception:
        logger.exception("❌ Error generating coverage report")
        sys.exit(1)


if __name__ == "__main__":
    main()
