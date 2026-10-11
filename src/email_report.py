
"""Render the CloudWatchtower AWS inventory and cost report."""

from html import escape


def table(headers, rows):
    header_html = "".join(
        f"<th>{escape(str(header))}</th>" for header in headers
    )
    body_html = "".join(rows)

    if not body_html:
        body_html = (
            f'<tr><td colspan="{len(headers)}">'
            "No resources found.</td></tr>"
        )

    return (
        "<table><thead><tr>"
        + header_html
        + "</tr></thead><tbody>"
        + body_html
        + "</tbody></table>"
    )


def render_html_report(report):
    def cell(value):
        if value is None or value == "":
            value = "N/A"
        return f"<td>{escape(str(value))}</td>"

    def yes_no_unknown(value):
        if value is True:
            return "Yes"
        if value is False:
            return "No"
        return "Unknown"

    def money(value):
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return "0.00"

    costs = report.get("costs", {})
    ec2 = report.get("ec2", {})
    rds = report.get("rds", {})
    s3 = report.get("s3", {})
    lambda_data = report.get("lambda", {})
    ebs = report.get("ebs", {})
    ecs = report.get("ecs", {})
    load_balancers = report.get("load_balancers", {})
    nat_gateways = report.get("nat_gateways", {})
    elastic_ips = report.get("elastic_ips", {})

    # Cost summary
    mtd = costs.get("month_to_date", {})
    daily_costs = costs.get("daily_costs", {})

    if not isinstance(daily_costs, dict):
        daily_costs = {}

    if isinstance(mtd, dict):
        currency = mtd.get(
            "currency", daily_costs.get("currency", "USD")
        )
        mtd_total = mtd.get("total", 0)
    elif isinstance(mtd, (int, float)):
        currency = daily_costs.get("currency", "USD")
        mtd_total = mtd
    else:
        currency = daily_costs.get("currency", "USD")
        mtd_total = 0

    period_start = costs.get("period_start", "N/A")
    period_end = costs.get("period_end_exclusive", "N/A")

    daily_rows = []
    by_day = daily_costs.get("by_day", {})

    if isinstance(by_day, dict):
        for day, details in by_day.items():
            if not isinstance(details, dict):
                continue

            daily_rows.append(
                "<tr>"
                + cell(day)
                + cell(money(details.get("total", 0)))
                + cell(details.get("currency", currency))
                + "</tr>"
            )

    service_rows = []
    if isinstance(by_day, dict):
        for day, details in by_day.items():
            if not isinstance(details, dict):
                continue

            services = details.get("services", {})
            if not isinstance(services, dict):
                continue

            for service, amount in services.items():
                service_rows.append(
                    "<tr>"
                    + cell(day)
                    + cell(service)
                    + cell(money(amount))
                    + "</tr>"
                )

    # EC2 instances
    ec2_rows = []
    for item in ec2.get("items", []):
        ec2_rows.append(
            "<tr>"
            + cell(item.get("instance_id"))
            + cell(item.get("name"))
            + cell(item.get("state"))
            + cell(item.get("instance_type"))
            + cell(item.get("region"))
            + cell(item.get("availability_zone"))
            + cell(item.get("public_ip"))
            + "</tr>"
        )

    # RDS databases
    rds_rows = []
    for item in rds.get("items", []):
        rds_rows.append(
            "<tr>"
            + cell(item.get("db_instance_id"))
            + cell(item.get("status"))
            + cell(item.get("engine"))
            + cell(item.get("instance_class"))
            + cell(item.get("storage_gb"))
            + cell(yes_no_unknown(item.get("multi_az")))
            + cell(yes_no_unknown(item.get("encrypted")))
            + cell(yes_no_unknown(item.get("publicly_accessible")))
            + "</tr>"
        )

    # S3 buckets
    s3_rows = []
    for item in s3.get("items", []):
        versioning = item.get("versioning", {})
        if not isinstance(versioning, dict):
            versioning = {}

        encryption_status = (
            "Enabled"
            if item.get("encryption")
            else (
                "Unknown"
                if item.get("encryption_error")
                else "Not detected"
            )
        )

        s3_rows.append(
            "<tr>"
            + cell(item.get("bucket_name"))
            + cell(item.get("region"))
            + cell(versioning.get("Status", "Unknown"))
            + cell(encryption_status)
            + "</tr>"
        )

    # Lambda functions
    lambda_rows = []
    for item in lambda_data.get("items", []):
        lambda_rows.append(
            "<tr>"
            + cell(item.get("function_name"))
            + cell(item.get("runtime"))
            + cell(item.get("state"))
            + cell(item.get("memory_mb"))
            + cell(item.get("timeout_seconds"))
            + cell(item.get("region"))
            + "</tr>"
        )

    # EBS volumes
    ebs_rows = []
    for item in ebs.get("items", []):
        attachments = item.get("attachments", [])
        attached_instances = ", ".join(
            attachment.get("instance_id", "Unknown")
            for attachment in attachments
        ) or "Unattached"

        ebs_rows.append(
            "<tr>"
            + cell(item.get("volume_id"))
            + cell(item.get("state"))
            + cell(item.get("size_gb"))
            + cell(item.get("volume_type"))
            + cell(item.get("availability_zone"))
            + cell(yes_no_unknown(item.get("encrypted")))
            + cell(attached_instances)
            + "</tr>"
        )

    # ECS clusters and services
    ecs_cluster_rows = []
    ecs_service_rows = []

    for cluster in ecs.get("items", []):
        ecs_cluster_rows.append(
            "<tr>"
            + cell(cluster.get("cluster_name"))
            + cell(cluster.get("status"))
            + cell(cluster.get("registered_container_instances"))
            + cell(cluster.get("running_tasks"))
            + cell(cluster.get("pending_tasks"))
            + cell(cluster.get("active_services"))
            + "</tr>"
        )

        for service in cluster.get("services", []):
            ecs_service_rows.append(
                "<tr>"
                + cell(cluster.get("cluster_name"))
                + cell(service.get("service_name"))
                + cell(service.get("status"))
                + cell(service.get("desired_count"))
                + cell(service.get("running_count"))
                + cell(service.get("pending_count"))
                + "</tr>"
            )

    # Load balancers
    load_balancer_rows = []
    for item in load_balancers.get("items", []):
        load_balancer_rows.append(
            "<tr>"
            + cell(item.get("name"))
            + cell(item.get("type"))
            + cell(item.get("scheme"))
            + cell(item.get("state"))
            + cell(item.get("vpc_id"))
            + cell(item.get("region"))
            + "</tr>"
        )

    # NAT Gateways
    nat_rows = []
    for item in nat_gateways.get("items", []):
        addresses = item.get("addresses", [])
        public_ips = ", ".join(
            address.get("public_ip", "")
            for address in addresses
            if address.get("public_ip")
        ) or "N/A"

        tags = item.get("tags", {})
        if isinstance(tags, dict):
            name = tags.get("Name", "Unnamed")
        elif isinstance(tags, list):
            name = next(
                (
                    tag.get("Value")
                    for tag in tags
                    if tag.get("Key") == "Name"
                ),
                "Unnamed",
            )
        else:
            name = "Unnamed"

        nat_rows.append(
            "<tr>"
            + cell(item.get("nat_gateway_id"))
            + cell(name)
            + cell(item.get("state"))
            + cell(item.get("connectivity_type"))
            + cell(item.get("vpc_id"))
            + cell(item.get("subnet_id"))
            + cell(public_ips)
            + cell(item.get("region"))
            + "</tr>"
        )

    nat_state_summary = ", ".join(
        f"{state}: {count}"
        for state, count in nat_gateways.get("by_state", {}).items()
    ) or "No NAT Gateways"

    nat_connectivity_summary = ", ".join(
        f"{kind}: {count}"
        for kind, count in nat_gateways.get(
            "by_connectivity_type", {}
        ).items()
    ) or "N/A"

    # Elastic IP addresses
    elastic_ip_rows = []
    for item in elastic_ips.get("items", []):
        tags = item.get("tags", {})
        if isinstance(tags, dict):
            name = tags.get("Name", "Unnamed")
        else:
            name = "Unnamed"

        elastic_ip_rows.append(
            "<tr>"
            + cell(item.get("public_ip"))
            + cell(name)
            + cell(item.get("allocation_id"))
            + cell(item.get("instance_id"))
            + cell(item.get("network_interface_id"))
            + cell(item.get("private_ip"))
            + cell(item.get("region"))
            + cell("Yes" if item.get("unassociated") else "No")
            + "</tr>"
        )

    generated_at = report.get("generated_at_eat", "Unknown")

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CloudWatchtower Daily AWS Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #222;
                margin: 24px;
                line-height: 1.5;
            }}
            h1, h2, h3 {{ color: #17365d; }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 24px;
                font-size: 13px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                overflow-wrap: anywhere;
            }}
            th {{ background-color: #edf2f7; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
            .summary {{
                background-color: #f1f5f9;
                padding: 16px;
                margin-bottom: 24px;
                border-radius: 6px;
            }}
            .muted {{ color: #555; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>CloudWatchtower Daily AWS Report</h1>
        <p>Generated at: {escape(str(generated_at))}</p>

        <div class="summary">
            <h2>Cost Summary</h2>
            <p><strong>Month-to-date cost:</strong>
                {escape(str(currency))} {escape(money(mtd_total))}</p>
            <p><strong>Period:</strong>
                {escape(str(period_start))} to
                {escape(str(period_end))} (end date exclusive)</p>
        </div>

        <h2>Daily Costs</h2>
        {table(["Date", "Total Cost", "Currency"], daily_rows)}

        <h2>Cost by Service</h2>
        {table(["Date", "Service", "Cost"], service_rows)}

        <h2>EC2 Instances</h2>
        <p>Total: {escape(str(ec2.get("total", 0)))}</p>
        {table([
            "Instance ID", "Name", "State", "Type",
            "Region", "Availability Zone", "Public IP"
        ], ec2_rows)}

        <h2>RDS Databases</h2>
        <p>Total: {escape(str(rds.get("total", 0)))}</p>
        {table([
            "DB Identifier", "Status", "Engine", "Instance Class",
            "Storage (GB)", "Multi-AZ", "Encrypted",
            "Publicly Accessible"
        ], rds_rows)}

        <h2>S3 Buckets</h2>
        <p>Total: {escape(str(s3.get("total", 0)))}</p>
        {table([
            "Bucket", "Region", "Versioning", "Encryption"
        ], s3_rows)}

        <h2>Lambda Functions</h2>
        <p>Total: {escape(str(lambda_data.get("total", 0)))}</p>
        {table([
            "Function", "Runtime", "State", "Memory (MB)",
            "Timeout (seconds)", "Region"
        ], lambda_rows)}

        <h2>EBS Volumes</h2>
        <p>Total: {escape(str(ebs.get("total", 0)))}</p>
        <p>Unattached volumes:
            {escape(str(ebs.get("unattached_count", 0)))}</p>
        {table([
            "Volume ID", "State", "Size (GB)", "Type",
            "Availability Zone", "Encrypted", "Attachments"
        ], ebs_rows)}

        <h2>ECS Clusters</h2>
        <p>Total clusters: {escape(str(ecs.get("total_clusters", 0)))}</p>
        <p>Running tasks: {escape(str(ecs.get("running_tasks", 0)))}</p>
        <p>Pending tasks: {escape(str(ecs.get("pending_tasks", 0)))}</p>
        <p>Total services: {escape(str(ecs.get("total_services", 0)))}</p>
        {table([
            "Cluster", "Status", "Container Instances",
            "Running Tasks", "Pending Tasks", "Active Services"
        ], ecs_cluster_rows)}

        <h3>ECS Services</h3>
        {table([
            "Cluster", "Service", "Status", "Desired",
            "Running", "Pending"
        ], ecs_service_rows)}

        <h2>Load Balancers</h2>
        <p>Total: {escape(str(load_balancers.get("total", 0)))}</p>
        {table([
            "Name", "Type", "Scheme", "State", "VPC", "Region"
        ], load_balancer_rows)}

        <h2>NAT Gateways</h2>
        <p><strong>Total:</strong>
            {escape(str(nat_gateways.get("total", 0)))}</p>
        <p><strong>Failed:</strong>
            {escape(str(nat_gateways.get("failed_count", 0)))}</p>
        <p><strong>By state:</strong>
            {escape(nat_state_summary)}</p>
        <p><strong>By connectivity type:</strong>
            {escape(nat_connectivity_summary)}</p>
        {table([
            "NAT Gateway ID", "Name", "State", "Connectivity",
            "VPC ID", "Subnet ID", "Public IPs", "Region"
        ], nat_rows)}

        <h2>Elastic IP Addresses</h2>
        <p><strong>Total:</strong>
            {escape(str(elastic_ips.get("total", 0)))}</p>
        <p><strong>Associated:</strong>
            {escape(str(elastic_ips.get("associated_count", 0)))}</p>
        <p><strong>Unassociated:</strong>
            {escape(str(elastic_ips.get("unassociated_count", 0)))}</p>
        {table([
            "Public IP", "Name", "Allocation ID", "Instance ID",
            "Network Interface", "Private IP", "Region",
            "Unassociated"
        ], elastic_ip_rows)}

        <p class="muted">
            This report is read-only and does not automatically stop,
            modify, or delete AWS resources. Cost Explorer data may be
            delayed and may not reflect the latest AWS usage.
            Unassociated Elastic IPs are candidates for cost review;
            verify their usage before taking action.
        </p>
    </body>
    </html>
    """
