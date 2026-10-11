
"""Read-only Elastic IP inventory collector."""

from datetime import datetime, timezone
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def collect_elastic_ips(region=None, session=None):
    """Collect Elastic IPs and identify unassociated addresses."""
    session = session or boto3.Session()

    client_kwargs = {}
    if region:
        client_kwargs["region_name"] = region

    ec2 = session.client("ec2", **client_kwargs)

    addresses = []

    try:
        # describe_addresses is not a pageable Boto3 operation.
        response = ec2.describe_addresses()

        for address in response.get("Addresses", []):
            association_id = address.get("AssociationId")

            addresses.append({
                "public_ip": address.get("PublicIp"),
                "allocation_id": address.get("AllocationId"),
                "association_id": association_id,
                "instance_id": address.get("InstanceId"),
                "network_interface_id": address.get(
                    "NetworkInterfaceId"
                ),
                "network_interface_owner_id": address.get(
                    "NetworkInterfaceOwnerId"
                ),
                "private_ip": address.get("PrivateIpAddress"),
                "domain": address.get("Domain"),
                "network_border_group": address.get(
                    "NetworkBorderGroup"
                ),
                "public_ipv4_pool": address.get("PublicIpv4Pool"),
                "region": region or session.region_name,
                "tags": {
                    tag["Key"]: tag.get("Value", "")
                    for tag in address.get("Tags", [])
                },
                "unassociated": not bool(association_id),
            })

    except (BotoCoreError, ClientError):
        raise

    total = len(addresses)
    unassociated_count = sum(
        1 for address in addresses if address["unassociated"]
    )

    return {
        "total": total,
        "associated_count": total - unassociated_count,
        "unassociated_count": unassociated_count,
        "failed_count": 0,
        "items": addresses,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import json

    result = collect_elastic_ips()
    print(json.dumps(result, indent=2, default=str))
