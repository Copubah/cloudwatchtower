
"""Generate a local HTML preview of the CloudWatchtower report."""

from pathlib import Path

from src.report import build_report
from src.email_report import save_html_report


def main():
    """Build the AWS report and save it as HTML."""
    report = build_report()

    output_path = Path("report.html")
    save_html_report(report, output_path)

    print(f"HTML report saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
