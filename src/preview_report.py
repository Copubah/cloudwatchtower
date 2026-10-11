"""Generate a local HTML preview of the AWS report."""

from pathlib import Path

from src.email_report import render_html_report
from src.report import generate_report


def main():
    report = generate_report()
    html = render_html_report(report)

    output = Path("report.html")
    output.write_text(html, encoding="utf-8")

    print(f"HTML report saved to: {output.resolve()}")


if __name__ == "__main__":
    main()