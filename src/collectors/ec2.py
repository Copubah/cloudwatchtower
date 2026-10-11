"""Read-only EC2 inventory collector."""
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def collect_ec2_instances(region=None, session=None):
    """Collect EC2 instance details without modifying resources."""
    session = session or boto3.Session()
    region = region or session.region_name

    if not region:
        raise ValueError(
            "No AWS region configured. Set AWS_DEFAULT_REGION "
            "or pass region explicitly."
        )

    client = session.client("ec2", region_name=region)
    paginator = client.get_paginator("describe_instances")
    instances = []

    for page in paginator.paginate():
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                tags = {
                    tag["Key"]: tag["Value"]
                    for tag in instance.get("Tags", [])
                }

                instances.append({
                    "instance_id": instance["InstanceId"],
                    "name": tags.get("Name", "Unnamed"),
                    "state": instance["State"]["Name"],
                    "instance_type": instance["InstanceType"],
                    "region": region,
                    "launch_time": instance.get("LaunchTime"),
                    "availability_zone": instance.get(
                        "Placement", {}
                    ).get("AvailabilityZone"),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                })

    return instances


def main():
    try:
        instances = collect_ec2_instances()
        print(f"EC2 instances found: {len(instances)}")
        print("-" * 90)

        for instance in instances:
            launch_time = instance["launch_time"]
            launch_time = (
                launch_time.isoformat() if launch_time else "Unknown"
            )

            print(
                f'{instance["instance_id"]} | '
                f'{instance["name"]} | '
                f'{instance["state"]} | '
                f'{instance["instance_type"]} | '
                f'{instance["region"]} | '
                f'{launch_time}'
            )

    except (BotoCoreError, ClientError, ValueError) as exc:
        print(f"EC2 scan failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()