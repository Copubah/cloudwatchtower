
"""Read-only RDS inventory collector."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def collect_rds_instances(region=None, session=None):
    """Collect RDS database inventory without modifying resources."""
    session = session or boto3.Session()
    region = region or session.region_name

    if not region:
        raise ValueError(
            "No AWS region configured. Set AWS_DEFAULT_REGION "
            "or pass region explicitly."
        )

    client = session.client("rds", region_name=region)
    paginator = client.get_paginator("describe_db_instances")
    databases = []

    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            databases.append({
                "db_instance_id": db["DBInstanceIdentifier"],
                "status": db.get("DBInstanceStatus", "Unknown"),
                "engine": db.get("Engine", "Unknown"),
                "engine_version": db.get("EngineVersion"),
                "instance_class": db.get("DBInstanceClass"),
                "region": region,
                "availability_zone": db.get("AvailabilityZone"),
                "multi_az": db.get("MultiAZ", False),
                "storage_gb": db.get("AllocatedStorage"),
                "storage_type": db.get("StorageType"),
                "publicly_accessible": db.get(
                    "PubliclyAccessible", False
                ),
                "encrypted": db.get("StorageEncrypted", False),
                "endpoint": (
                    db.get("Endpoint", {}).get("Address")
                    if db.get("Endpoint")
                    else None
                ),
            })

    return databases


def main():
    try:
        databases = collect_rds_instances()

        print(f"RDS instances found: {len(databases)}")
        print("-" * 100)

        for db in databases:
            print(
                f'{db["db_instance_id"]} | '
                f'{db["status"]} | '
                f'{db["engine"]} {db["engine_version"] or ""} | '
                f'{db["instance_class"]} | '
                f'{db["region"]} | '
                f'Encrypted: {db["encrypted"]} | '
                f'Public: {db["publicly_accessible"]}'
            )

    except (BotoCoreError, ClientError, ValueError) as exc:
        print(f"RDS scan failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
