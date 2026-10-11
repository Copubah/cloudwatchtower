
"""Read-only AWS CloudWatch alarms and log-group inventory."""

from datetime import datetime, timezone

import boto3


def collect_cloudwatch_inventory(region=None, session=None):
    """Collect CloudWatch alarms and CloudWatch Logs group metadata."""
    session = session or boto3.Session()

    cloudwatch = session.client("cloudwatch", region_name=region)
    logs = session.client("logs", region_name=region)

    alarms = []
    paginator = cloudwatch.get_paginator("describe_alarms")

    for page in paginator.paginate():
        for alarm in page.get("MetricAlarms", []):
            alarms.append({
                "name": alarm.get("AlarmName"),
                "state": alarm.get("StateValue"),
                "state_reason": alarm.get("StateReason"),
                "metric_name": alarm.get("MetricName"),
                "namespace": alarm.get("Namespace"),
                "comparison_operator": alarm.get("ComparisonOperator"),
                "threshold": alarm.get("Threshold"),
                "evaluation_periods": alarm.get("EvaluationPeriods"),
                "period_seconds": alarm.get("Period"),
                "actions_enabled": alarm.get("ActionsEnabled", False),
                "region": cloudwatch.meta.region_name,
            })

    composite_alarms = []
    paginator = cloudwatch.get_paginator("describe_alarms")

    for page in paginator.paginate(AlarmTypes=["CompositeAlarm"]):
        for alarm in page.get("CompositeAlarms", []):
            composite_alarms.append({
                "name": alarm.get("AlarmName"),
                "state": alarm.get("StateValue"),
                "state_reason": alarm.get("StateReason"),
                "actions_enabled": alarm.get("ActionsEnabled", False),
                "region": cloudwatch.meta.region_name,
            })

    log_groups = []
    paginator = logs.get_paginator("describe_log_groups")

    for page in paginator.paginate():
        for group in page.get("logGroups", []):
            retention_days = group.get("retentionInDays")

            log_groups.append({
                "name": group.get("logGroupName"),
                "stored_bytes": group.get("storedBytes", 0),
                "retention_days": retention_days,
                "retention_configured": retention_days is not None,
                "kms_key_id": group.get("kmsKeyId"),
                "region": logs.meta.region_name,
                "creation_time_ms": group.get("creationTime"),
            })

    return {
        "region": cloudwatch.meta.region_name,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "alarms": alarms,
        "alarm_count": len(alarms),
        "composite_alarms": composite_alarms,
        "composite_alarm_count": len(composite_alarms),
        "log_groups": log_groups,
        "log_group_count": len(log_groups),
        "alarms_in_alarm_state": sum(
            alarm.get("state") == "ALARM" for alarm in alarms
        ),
        "log_groups_without_retention": sum(
            not group["retention_configured"] for group in log_groups
        ),
    }


if __name__ == "__main__":
    import json

    inventory = collect_cloudwatch_inventory()
    print(json.dumps(inventory, indent=2, default=str))
