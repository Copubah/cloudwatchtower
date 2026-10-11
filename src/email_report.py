
"""Render CloudWatchtower reports as HTML and plain text."""

from html import escape
from pathlib import Path


def money(value, currency="USD"):
    """Format a numeric amount as currency."""
    try:
        return f"{currency} {float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{currency} 0.00"


def table(headers, rows):
    """Render an HTML table."""
    header_html = "".join(
        f"<th>{escape(str(header))}</th>" for header in headers
    )

    if not rows:
        body_html = (
            f'<tr><td colspan="{len(headers)}">No data available</td></tr>'
        )
    else:
        body_html = "".join(
            "<tr>"
            + "".join(
                f"<td>{escape(str(value if value is not None else 'N/A'))}</td>"
                for value in row
            )
            + "</tr>"
            for row in rows
        )

    return (
        '<div class="table-wrap"><table>'
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{body_html}</tbody>"
        "</table></div>"
    )


def summary_card(label, value):
    """Render a report summary card."""
    return (
        '<div class="card">'
        f'<div class="card-label">{escape(str(label))}</div>'
        f'<div class="card-value">{escape(str(value))}</div>'
        "</div>"
    )


def render_html_report(report):
    """Render the complete report as HTML."""
    costs = report.get("costs", {})
    currency = costs.get("currency", "USD")
    daily_costs = costs.get("daily_costs", [])

    cost_rows = []
    for day in daily_costs:
        services = day.get("services", [])
        service_total = sum(
            float(service.get("amount", 0) or 0)
            for service in services
        )
        cost_rows.append(
            [
                day.get("date", "Unknown"),
                money(day.get("total", service_total), currency),
                ", ".join(
                    f"{service.get('service', 'Unknown')}: "
                    f"{money(service.get('amount', 0), currency)}"
                    for service in services
                )
                or "No service breakdown",
            ]
        )

    ec2 = report.get("ec2", {})
    rds = report.get("rds", {})
    s3 = report.get("s3", {})
    lambdas = report.get("lambda", {})
    ebs = report.get("ebs", {})
    ecs = report.get("ecs", {})
    load_balancers = report.get("load_balancers", {})
    nat = report.get("nat_gateways", {})
    eips = report.get("elastic_ips", {})
    vpc = report.get("vpc", {})
    cloudwatch = report.get("cloudwatch", {})

    sections = []

    sections.append(
        "<h2>Cost Overview</h2>"
        + "".join(
            [
                summary_card(
                    "Month-to-date cost",
                    money(costs.get("month_to_date", 0), currency),
                ),
                summary_card(
                    "Reporting period",
                    f"{costs.get('period_start', 'N/A')} to "
                    f"{costs.get('period_end_exclusive', 'N/A')}",
                ),
            ]
        )
        + table(
            ["Date", "Daily Cost", "Cost by Service"],
            cost_rows,
        )
    )

    sections.append(
        "<h2>EC2 Instances</h2>"
        + "".join(
            [
                summary_card("Total instances", ec2.get("total", 0)),
                summary_card(
                    "Running instances",
                    ec2.get("running", 0),
                ),
            ]
        )
        + table(
            [
                "Instance ID",
                "Name",
                "State",
                "Instance Type",
                "Region",
                "Availability Zone",
                "Private IP",
                "Public IP",
            ],
            [
                [
                    item.get("instance_id"),
                    item.get("name"),
                    item.get("state"),
                    item.get("instance_type"),
                    item.get("region"),
                    item.get("availability_zone"),
                    item.get("private_ip"),
                    item.get("public_ip"),
                ]
                for item in ec2.get("instances", [])
            ],
        )
    )

    sections.append(
        "<h2>RDS Databases</h2>"
        + "".join(
            [
                summary_card("Total databases", rds.get("total", 0)),
                summary_card(
                    "Publicly accessible",
                    rds.get("publicly_accessible", 0),
                ),
                summary_card(
                    "Unencrypted databases",
                    rds.get("unencrypted", 0),
                ),
            ]
        )
        + table(
            [
                "Database ID",
                "Status",
                "Engine",
                "Class",
                "Region",
                "Multi-AZ",
                "Storage (GB)",
                "Public",
                "Encrypted",
            ],
            [
                [
                    item.get("db_instance_id"),
                    item.get("status"),
                    item.get("engine"),
                    item.get("instance_class"),
                    item.get("region"),
                    item.get("multi_az"),
                    item.get("storage_gb"),
                    item.get("publicly_accessible"),
                    item.get("encrypted"),
                ]
                for item in rds.get("instances", [])
            ],
        )
    )

    sections.append(
        "<h2>S3 Buckets</h2>"
        + summary_card("Total buckets", s3.get("total", 0))
        + table(
            [
                "Bucket",
                "Region",
                "Created",
                "Versioning",
                "Encryption",
                "Encryption Error",
            ],
            [
                [
                    item.get("name"),
                    item.get("region"),
                    item.get("creation_date"),
                    item.get("versioning"),
                    item.get("encryption"),
                    item.get("encryption_error"),
                ]
                for item in s3.get("buckets", [])
            ],
        )
    )

    sections.append(
        "<h2>Lambda Functions</h2>"
        + summary_card(
            "Total functions",
            lambdas.get("total", 0),
        )
        + table(
            [
                "Function",
                "Runtime",
                "State",
                "Memory (MB)",
                "Timeout (seconds)",
                "Region",
                "Last Modified",
            ],
            [
                [
                    item.get("function_name"),
                    item.get("runtime"),
                    item.get("state"),
                    item.get("memory_mb"),
                    item.get("timeout_seconds"),
                    item.get("region"),
                    item.get("last_modified"),
                ]
                for item in lambdas.get("functions", [])
            ],
        )
    )

    sections.append(
        "<h2>EBS Volumes</h2>"
        + "".join(
            [
                summary_card("Total volumes", ebs.get("total", 0)),
                summary_card(
                    "Unattached volumes",
                    ebs.get("unattached", 0),
                ),
            ]
        )
        + table(
            [
                "Volume ID",
                "State",
                "Size (GB)",
                "Type",
                "Availability Zone",
                "Encrypted",
                "Attachments",
            ],
            [
                [
                    item.get("volume_id"),
                    item.get("state"),
                    item.get("size_gb"),
                    item.get("volume_type"),
                    item.get("availability_zone"),
                    item.get("encrypted"),
                    ", ".join(
                        attachment.get("instance_id", "Unknown")
                        for attachment in item.get("attachments", [])
                    )
                    or "Unattached",
                ]
                for item in ebs.get("volumes", [])
            ],
        )
    )

    ecs_rows = []
    for cluster in ecs.get("clusters", []):
        services = cluster.get("services", [])
        ecs_rows.append(
            [
                cluster.get("cluster_name"),
                cluster.get("status"),
                cluster.get("running_tasks", 0),
                cluster.get("pending_tasks", 0),
                cluster.get("active_services", len(services)),
                ", ".join(
                    f"{service.get('service_name', 'Unknown')} "
                    f"({service.get('running_count', 0)}/"
                    f"{service.get('desired_count', 0)})"
                    for service in services
                )
                or "No services",
            ]
        )

    sections.append(
        "<h2>ECS Clusters</h2>"
        + summary_card("Total clusters", ecs.get("total", 0))
        + table(
            [
                "Cluster",
                "Status",
                "Running Tasks",
                "Pending Tasks",
                "Active Services",
                "Services",
            ],
            ecs_rows,
        )
    )

    sections.append(
        "<h2>Load Balancers</h2>"
        + summary_card(
            "Total load balancers",
            load_balancers.get("total", 0),
        )
        + table(
            [
                "Name",
                "Type",
                "Scheme",
                "State",
                "VPC",
                "DNS Name",
                "Region",
            ],
            [
                [
                    item.get("name"),
                    item.get("type"),
                    item.get("scheme"),
                    item.get("state"),
                    item.get("vpc_id"),
                    item.get("dns_name"),
                    item.get("region"),
                ]
                for item in load_balancers.get("load_balancers", [])
            ],
        )
    )

    sections.append(
        "<h2>NAT Gateways</h2>"
        + "".join(
            [
                summary_card("Total NAT gateways", nat.get("total", 0)),
                summary_card(
                    "Available NAT gateways",
                    nat.get("available", 0),
                ),
            ]
        )
        + table(
            [
                "NAT Gateway ID",
                "State",
                "Connectivity",
                "VPC",
                "Subnet",
                "Region",
            ],
            [
                [
                    item.get("nat_gateway_id"),
                    item.get("state"),
                    item.get("connectivity_type"),
                    item.get("vpc_id"),
                    item.get("subnet_id"),
                    item.get("region"),
                ]
                for item in nat.get("gateways", [])
            ],
        )
    )

    sections.append(
        "<h2>Elastic IP Addresses</h2>"
        + "".join(
            [
                summary_card("Total addresses", eips.get("total", 0)),
                summary_card(
                    "Unassociated addresses",
                    eips.get("unassociated_count", 0),
                ),
            ]
        )
        + table(
            [
                "Public IP",
                "Allocation ID",
                "Association ID",
                "Instance ID",
                "Region",
                "Unassociated",
            ],
            [
                [
                    item.get("public_ip"),
                    item.get("allocation_id"),
                    item.get("association_id"),
                    item.get("instance_id"),
                    item.get("region"),
                    item.get("unassociated"),
                ]
                for item in eips.get("items", [])
            ],
        )
    )

    sections.append(
        "<h2>VPC and Network Inventory</h2>"
        + "".join(
            [
                summary_card("VPCs", vpc.get("vpc_count", 0)),
                summary_card("Subnets", vpc.get("subnet_count", 0)),
                summary_card(
                    "Route tables",
                    vpc.get("route_table_count", 0),
                ),
                summary_card(
                    "Internet gateways",
                    vpc.get("internet_gateway_count", 0),
                ),
                summary_card(
                    "Detached internet gateways",
                    vpc.get("detached_internet_gateway_count", 0),
                ),
            ]
        )
        + "<h3>VPCs</h3>"
        + table(
            ["VPC ID", "CIDR", "State", "Default VPC", "Region"],
            [
                [
                    item.get("vpc_id"),
                    item.get("cidr_block"),
                    item.get("state"),
                    item.get("is_default"),
                    item.get("region"),
                ]
                for item in vpc.get("vpcs", [])
            ],
        )
        + "<h3>Subnets</h3>"
        + table(
            [
                "Subnet ID",
                "VPC ID",
                "CIDR",
                "Availability Zone",
                "Available IPs",
                "Auto-assign Public IP",
            ],
            [
                [
                    item.get("subnet_id"),
                    item.get("vpc_id"),
                    item.get("cidr_block"),
                    item.get("availability_zone"),
                    item.get("available_ip_address_count"),
                    item.get("map_public_ip_on_launch"),
                ]
                for item in vpc.get("subnets", [])
            ],
        )
        + "<h3>Route Tables</h3>"
        + table(
            ["Route Table ID", "VPC ID", "Routes", "Associations"],
            [
                [
                    item.get("route_table_id"),
                    item.get("vpc_id"),
                    len(item.get("routes", [])),
                    item.get("associations_count"),
                ]
                for item in vpc.get("route_tables", [])
            ],
        )
        + "<h3>Internet Gateways</h3>"
        + table(
            ["Internet Gateway ID", "Attached VPCs", "Attachment States"],
            [
                [
                    item.get("internet_gateway_id"),
                    ", ".join(item.get("attached_vpc_ids", [])) or "None",
                    ", ".join(item.get("attachment_states", [])) or "None",
                ]
                for item in vpc.get("internet_gateways", [])
            ],
        )
    )

    alarm_rows = [
        [
            alarm.get("name"),
            alarm.get("state"),
            alarm.get("namespace"),
            alarm.get("metric_name"),
            alarm.get("comparison_operator"),
            alarm.get("threshold"),
            alarm.get("actions_enabled"),
        ]
        for alarm in cloudwatch.get("alarms", [])
    ]

    composite_rows = [
        [
            alarm.get("name"),
            alarm.get("state"),
            alarm.get("state_reason"),
            alarm.get("actions_enabled"),
        ]
        for alarm in cloudwatch.get("composite_alarms", [])
    ]

    log_group_rows = [
        [
            group.get("name"),
            group.get("stored_bytes", 0),
            (
                f"{group.get('retention_days')} days"
                if group.get("retention_days") is not None
                else "Never expire"
            ),
            group.get("kms_key_id") or "No customer-managed KMS key reported",
        ]
        for group in cloudwatch.get("log_groups", [])
    ]

    sections.append(
        "<h2>CloudWatch Monitoring</h2>"
        + "".join(
            [
                summary_card(
                    "Metric alarms",
                    cloudwatch.get("alarm_count", len(alarm_rows)),
                ),
                summary_card(
                    "Alarms in ALARM state",
                    cloudwatch.get(
                        "alarms_in_alarm_state",
                        sum(row[1] == "ALARM" for row in alarm_rows),
                    ),
                ),
                summary_card(
                    "Composite alarms",
                    cloudwatch.get(
                        "composite_alarm_count",
                        len(composite_rows),
                    ),
                ),
                summary_card(
                    "Log groups",
                    cloudwatch.get("log_group_count", len(log_group_rows)),
                ),
                summary_card(
                    "Log groups without retention",
                    cloudwatch.get("log_groups_without_retention", 0),
                ),
            ]
        )
        + "<h3>Metric Alarms</h3>"
        + table(
            [
                "Alarm",
                "State",
                "Namespace",
                "Metric",
                "Comparison",
                "Threshold",
                "Actions Enabled",
            ],
            alarm_rows,
        )
        + "<h3>Composite Alarms</h3>"
        + table(
            ["Alarm", "State", "Reason", "Actions Enabled"],
            composite_rows,
        )
        + "<h3>Log Groups</h3>"
        + table(
            [
                "Log Group",
                "Stored Bytes",
                "Retention",
                "Customer-managed KMS Key",
            ],
            log_group_rows,
        )
    )

    generated_at = report.get("generated_at_eat", "Unknown")
    region = report.get("region", "Unknown")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloudWatchtower AWS Report</title>
<style>
:root {{
    color-scheme: light;
    font-family: Arial, Helvetica, sans-serif;
    color: #1f2937;
    background: #f3f6fa;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 24px; }}
main {{ max-width: 1440px; margin: 0 auto; }}
header {{
    background: #172554;
    color: #ffffff;
    padding: 28px;
    border-radius: 12px;
    margin-bottom: 24px;
}}
header h1 {{ margin: 0 0 10px; }}
header p {{ margin: 5px 0; color: #dbeafe; }}
section {{
    background: #ffffff;
    padding: 22px;
    margin-bottom: 22px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}}
h2 {{ margin: 0 0 18px; color: #1d4ed8; }}
h3 {{ margin-top: 24px; color: #374151; }}
.cards {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 18px;
}}
.card {{
    flex: 1 1 180px;
    min-width: 150px;
    padding: 16px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}}
.card-label {{
    font-size: 12px;
    color: #64748b;
    margin-bottom: 8px;
}}
.card-value {{
    font-size: 20px;
    font-weight: 700;
    overflow-wrap: anywhere;
}}
.table-wrap {{ width: 100%; overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{
    padding: 10px;
    text-align: left;
    vertical-align: top;
    border-bottom: 1px solid #e5e7eb;
}}
th {{ background: #f1f5f9; white-space: nowrap; }}
tbody tr:hover {{ background: #f8fafc; }}
footer {{ color: #64748b; font-size: 12px; padding: 12px 0; }}
@media (max-width: 640px) {{
    body {{ padding: 10px; }}
    header, section {{ padding: 16px; }}
}}
</style>
</head>
<body>
<main>
<header>
<h1>CloudWatchtower</h1>
<p>AWS Cost, Resource and Monitoring Report</p>
<p>Region: {escape(str(region))}</p>
<p>Generated: {escape(str(generated_at))}</p>
</header>
{''.join(f'<section>{content}</section>' for content in sections)}
<footer>
Generated by CloudWatchtower. Inventory and findings are informational;
review AWS configuration before taking action.
</footer>
</main>
</body>
</html>"""


def render_text_report(report):
    """Render a compact plain-text report."""
    costs = report.get("costs", {})
    currency = costs.get("currency", "USD")
    ec2 = report.get("ec2", {})
    rds = report.get("rds", {})
    s3 = report.get("s3", {})
    lambdas = report.get("lambda", {})
    ebs = report.get("ebs", {})
    ecs = report.get("ecs", {})
    load_balancers = report.get("load_balancers", {})
    nat = report.get("nat_gateways", {})
    eips = report.get("elastic_ips", {})
    vpc = report.get("vpc", {})
    cloudwatch = report.get("cloudwatch", {})

    lines = [
        "CLOUDWATCHTOWER AWS REPORT",
        "=" * 32,
        f"Generated: {report.get('generated_at_eat', 'Unknown')}",
        f"Region: {report.get('region', 'Unknown')}",
        "",
        "COST OVERVIEW",
        f"Month-to-date: {money(costs.get('month_to_date', 0), currency)}",
        f"Period: {costs.get('period_start', 'N/A')} to "
        f"{costs.get('period_end_exclusive', 'N/A')}",
        "",
        "EC2",
        f"Total instances: {ec2.get('total', 0)}",
        f"Running instances: {ec2.get('running', 0)}",
        "",
        "RDS",
        f"Total databases: {rds.get('total', 0)}",
        f"Publicly accessible: {rds.get('publicly_accessible', 0)}",
        f"Unencrypted databases: {rds.get('unencrypted', 0)}",
        "",
        "S3",
        f"Total buckets: {s3.get('total', 0)}",
        "",
        "LAMBDA",
        f"Total functions: {lambdas.get('total', 0)}",
        "",
        "EBS",
        f"Total volumes: {ebs.get('total', 0)}",
        f"Unattached volumes: {ebs.get('unattached', 0)}",
        "",
        "ECS",
        f"Total clusters: {ecs.get('total', 0)}",
        "",
        "LOAD BALANCERS",
        f"Total load balancers: {load_balancers.get('total', 0)}",
        "",
        "NAT GATEWAYS",
        f"Total NAT gateways: {nat.get('total', 0)}",
        f"Available NAT gateways: {nat.get('available', 0)}",
        "",
        "ELASTIC IP ADDRESSES",
        f"Total addresses: {eips.get('total', 0)}",
        f"Unassociated addresses: {eips.get('unassociated_count', 0)}",
        "",
        "VPC AND NETWORK",
        f"VPCs: {vpc.get('vpc_count', 0)}",
        f"Subnets: {vpc.get('subnet_count', 0)}",
        f"Route tables: {vpc.get('route_table_count', 0)}",
        f"Internet gateways: {vpc.get('internet_gateway_count', 0)}",
        f"Detached internet gateways: "
        f"{vpc.get('detached_internet_gateway_count', 0)}",
        "",
        "CLOUDWATCH",
        f"Metric alarms: {cloudwatch.get('alarm_count', 0)}",
        f"Alarms in ALARM state: "
        f"{cloudwatch.get('alarms_in_alarm_state', 0)}",
        f"Composite alarms: {cloudwatch.get('composite_alarm_count', 0)}",
        f"Log groups: {cloudwatch.get('log_group_count', 0)}",
        f"Log groups without retention: "
        f"{cloudwatch.get('log_groups_without_retention', 0)}",
        "",
        "DAILY COSTS",
    ]

    for day in costs.get("daily_costs", []):
        lines.append(
            f"{day.get('date', 'Unknown')}: "
            f"{money(day.get('total', 0), currency)}"
        )
        for service in day.get("services", []):
            lines.append(
                f"  {service.get('service', 'Unknown')}: "
                f"{money(service.get('amount', 0), currency)}"
            )

    lines.extend(
        [
            "",
            "This report is informational. Review findings before taking action.",
        ]
    )

    return "\n".join(lines)


def save_html_report(report, output_path="report.html"):
    """Write the HTML report to disk and return its path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html_report(report), encoding="utf-8")
    return path


def save_text_report(report, output_path="report.txt"):
    """Write the plain-text report to disk and return its path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_text_report(report), encoding="utf-8")
    return path


if __name__ == "__main__":
    from src.report import build_report

    report_data = build_report()
    html_path = save_html_report(report_data, "report.html")
    text_path = save_text_report(report_data, "report.txt")

    print(f"HTML report saved to: {html_path.resolve()}")
    print(f"Text report saved to: {text_path.resolve()}")

