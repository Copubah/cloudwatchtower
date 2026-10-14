
"""Generate read-only security and cost review findings from AWS inventory."""
def analyze_report(report):
    """Return actionable findings based on the collected AWS inventory."""
    findings = []

    def add_finding(severity, resource_type, resource_id, title, detail, recommendation):
        findings.append(
            {
                "severity": severity,
                "resource_type": resource_type,
                "resource_id": str(resource_id or "Unknown"),
                "title": title,
                "detail": detail,
                "recommendation": recommendation,
            }
        )

    # RDS checks
    rds = report.get("rds", {})
    for db in rds.get("instances", []):
        db_id = db.get("db_instance_id", "Unknown")

        if db.get("publicly_accessible") is True:
            add_finding(
                "HIGH",
                "RDS",
                db_id,
                "Database is publicly accessible",
                "The database is configured to allow public accessibility.",
                "Verify whether public access is required. Prefer private networking "
                "and restrict inbound access using security groups.",
            )

        if db.get("encrypted") is False:
            add_finding(
                "MEDIUM",
                "RDS",
                db_id,
                "Database storage is not encrypted",
                "The inventory reports storage encryption as disabled.",
                "Review data sensitivity and migration requirements before "
                "enabling encryption.",
            )

    # S3 checks
    s3 = report.get("s3", {})
    for bucket in s3.get("buckets", []):
        bucket_name = bucket.get("name", "Unknown")
        versioning = str(bucket.get("versioning", "")).lower()
        encryption = str(bucket.get("encryption", "")).lower()

        if versioning in {"disabled", "suspended"}:
            add_finding(
                "LOW",
                "S3",
                bucket_name,
                "Bucket versioning is not enabled",
                f"Reported versioning status: {bucket.get('versioning')}.",
                "Assess recovery and retention requirements before enabling "
                "versioning. Review storage costs and lifecycle rules.",
            )

        if encryption in {"", "none", "unknown", "not configured"}:
            add_finding(
                "MEDIUM",
                "S3",
                bucket_name,
                "Bucket encryption could not be confirmed",
                "The inventory does not report a recognized encryption setting.",
                "Verify the bucket's default encryption configuration. Do not "
                "assume that missing inventory data proves objects are unencrypted.",
            )

    # EBS checks
    ebs = report.get("ebs", {})
    for volume in ebs.get("volumes", []):
        if volume.get("state") == "available":
            volume_id = volume.get("volume_id", "Unknown")
            size = volume.get("size_gb", "Unknown")

            add_finding(
                "MEDIUM",
                "EBS",
                volume_id,
                "Volume is unattached",
                f"The volume is available and unattached. Reported size: {size} GB.",
                "Confirm whether the volume is needed for recovery or retained "
                "data. If not required, snapshot or delete it only after approval.",
            )

    # Elastic IP checks
    eips = report.get("elastic_ips", {})
    for address in eips.get("items", []):
        if address.get("unassociated") is True:
            add_finding(
                "MEDIUM",
                "Elastic IP",
                address.get("allocation_id") or address.get("public_ip"),
                "Elastic IP is unassociated",
                f"Public IP: {address.get('public_ip', 'Unknown')}.",
                "Confirm whether the address is required. Review current "
                "public IPv4 pricing before releasing unused addresses.",
            )

    # CloudWatch log retention checks
    cloudwatch = report.get("cloudwatch", {})
    for group in cloudwatch.get("log_groups", []):
        if group.get("retention_configured") is False:
            add_finding(
                "LOW",
                "CloudWatch Logs",
                group.get("name", "Unknown"),
                "Log group has no configured retention period",
                "Logs may be retained indefinitely, increasing storage costs.",
                "Choose a retention period that meets operational, compliance "
                "and investigation requirements.",
            )

    # CloudWatch alarm checks
    for alarm in cloudwatch.get("alarms", []):
        if alarm.get("state") == "ALARM":
            add_finding(
                "HIGH",
                "CloudWatch Alarm",
                alarm.get("name", "Unknown"),
                "Alarm is in ALARM state",
                str(alarm.get("state_reason") or "The alarm is currently firing."),
                "Investigate the underlying metric and determine whether "
                "corrective action is required.",
            )

    # IAM checks, included when IAM inventory has been integrated
    iam = report.get("iam", {})
    for user in iam.get("users", []):
        username = user.get("username", "Unknown")

        if user.get("mfa_enabled") is False:
            add_finding(
                "MEDIUM",
                "IAM User",
                username,
                "IAM user has no MFA device reported",
                "The inventory reports no MFA devices for this user.",
                "Confirm whether the user needs console or programmatic access. "
                "Require MFA for interactive access where appropriate.",
            )

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    findings.sort(
        key=lambda finding: (
            severity_order.get(finding["severity"], 4),
            finding["resource_type"],
            finding["resource_id"],
        )
    )

    return {
        "total_findings": len(findings),
        "high": sum(f["severity"] == "HIGH" for f in findings),
        "medium": sum(f["severity"] == "MEDIUM" for f in findings),
        "low": sum(f["severity"] == "LOW" for f in findings),
        "findings": findings,
    }


if __name__ == "__main__":
    # Local smoke test: no AWS API calls are made.
    sample_report = {
        "rds": {
            "instances": [
                {
                    "db_instance_id": "example-db",
                    "publicly_accessible": True,
                    "encrypted": False,
                }
            ]
        },
        "s3": {
            "buckets": [
                {
                    "name": "example-bucket",
                    "versioning": "Disabled",
                    "encryption": "AES256",
                }
            ]
        },
        "ebs": {"volumes": []},
        "elastic_ips": {"items": []},
        "cloudwatch": {"log_groups": [], "alarms": []},
        "iam": {"users": []},
    }

    import json

    print(json.dumps(analyze_report(sample_report), indent=2))

