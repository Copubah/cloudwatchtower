
"""Collect read-only AWS NAT Gateway inventory."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError
def collect_nat_gateways(region=None, session=None):
    """Return NAT Gateway inventory for one AWS region."""
    session = session or boto3.Session()

    if region:
        regions = [region]
    else:
        regions = [session.region_name] if session.region_name else []

    if not regions:
        raise ValueError(
            "No AWS region configured. Set AWS_DEFAULT_REGION "
            "or pass region='your-region'."
        )

    inventory = []

    for current_region in regions:
        client = session.client("ec2", region_name=current_region)

        try:
            paginator = client.get_paginator("describe_nat_gateways")

            for page in paginator.paginate():
                for gateway in page.get("NatGateways", []):
                    addresses = [
                        {
                            "public_ip": address.get("PublicIp"),
                            "private_ip": address.get("PrivateIp"),
                            "allocation_id": address.get("AllocationId"),
                            "network_interface_id": address.get(
                                "NetworkInterfaceId"
                            ),
                            "association_id": address.get("AssociationId"),
                            "is_primary": address.get("IsPrimary"),
                        }
                        for address in gateway.get("NatGatewayAddresses", [])
                    ]

                    inventory.append({
                        "nat_gateway_id": gateway.get("NatGatewayId"),
                        "state": gateway.get("State"),
                        "vpc_id": gateway.get("VpcId"),
                        "subnet_id": gateway.get("SubnetId"),
                        "connectivity_type": gateway.get(
                            "ConnectivityType", "Unknown"
                        ),
                        "created_at": (
                            gateway["CreateTime"].isoformat()
                            if gateway.get("CreateTime")
                            else None
                        ),
                        "deleted_at": (
                            gateway["DeleteTime"].isoformat()
                            if gateway.get("DeleteTime")
                            else None
                        ),
                        "failure_code": gateway.get("FailureCode"),
                        "failure_message": gateway.get("FailureMessage"),
                        "addresses": addresses,
                        "region": current_region,
                        "tags": {
                            tag["Key"]: tag["Value"]
                            for tag in gateway.get("Tags", [])
                        },
                    })

        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"Failed to collect NAT Gateways in "
                f"{current_region}: {exc}"
            ) from exc

    return inventory


def main():
    gateways = collect_nat_gateways()

    print(f"NAT Gateways found: {len(gateways)}")

    for gateway in gateways:
        name = gateway["tags"].get("Name", "Unnamed")
        print(
            f"{gateway['nat_gateway_id']} ({name}): "
            f"state={gateway['state']}, "
            f"type={gateway['connectivity_type']}, "
            f"vpc={gateway['vpc_id']}, "
            f"region={gateway['region']}"
        )


if __name__ == "__main__":
    main()
