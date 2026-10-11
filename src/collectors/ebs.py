
"""Read-only EBS volume inventory collector."""
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def collect_ebs_volumes(region=None, session=None):
    """Collect EBS volume metadata without modifying resources."""
    session = session or boto3.Session()
    region = region or session.region_name

    if not region:
        raise ValueError(
            "No AWS region configured. Set AWS_DEFAULT_REGION "
            "or pass region explicitly."
        )

    client = session.client("ec2", region_name=region)
    paginator = client.get_paginator("describe_volumes")
    volumes = []

    for page in paginator.paginate():
        for volume in page.get("Volumes", []):
            attachments = volume.get("Attachments", [])

            volumes.append({
                "volume_id": volume["VolumeId"],
                "state": volume.get("State", "Unknown"),
                "size_gb": volume.get("Size"),
                "volume_type": volume.get("VolumeType", "Unknown"),
                "iops": volume.get("Iops"),
                "throughput_mbps": volume.get("Throughput"),
                "availability_zone": volume.get("AvailabilityZone"),
                "region": region,
                "encrypted": volume.get("Encrypted", False),
                "kms_key_id": volume.get("KmsKeyId"),
                "created_at": (
                    volume["CreateTime"].isoformat()
                    if volume.get("CreateTime")
                    else None
                ),
                "attachments": [
                    {
                        "instance_id": attachment.get("InstanceId"),
                        "state": attachment.get("State"),
                        "device": attachment.get("Device"),
                    }
                    for attachment in attachments
                ],
                "tags": {
                    tag["Key"]: tag["Value"]
                    for tag in volume.get("Tags", [])
                },
            })

    return volumes


def main():
    try:
        volumes = collect_ebs_volumes()

        print(f"EBS volumes found: {len(volumes)}")
        print("-" * 100)

        for volume in volumes:
            name = volume["tags"].get("Name", "Unnamed")
            attachment_state = (
                ", ".join(
                    f'{item["instance_id"]}:{item["state"]}'
                    for item in volume["attachments"]
                )
                if volume["attachments"]
                else "UNATTACHED"
            )

            print(
                f'{volume["volume_id"]} | '
                f'{name} | '
                f'{volume["state"]} | '
                f'{volume["size_gb"]} GiB | '
                f'{volume["volume_type"]} | '
                f'Encrypted: {volume["encrypted"]} | '
                f'{attachment_state}'
            )

    except (BotoCoreError, ClientError, ValueError) as exc:
        print(f"EBS scan failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
