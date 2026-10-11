
"""Read-only inventory collector for AWS VPCs and related networking resources."""

from datetime import datetime, timezone
import boto3
def collect_vpc_inventory(region=None, session=None):
    """Collect VPCs, subnets, route tables, and internet gateways.

    Args:
        region: AWS region to inspect. Uses the session's default region if omitted.
        session: Optional boto3 Session for testing or custom credentials.

    Returns:
        A dictionary containing VPC and networking inventory.
    """
    session = session or boto3.Session()
    client = session.client("ec2", region_name=region)

    vpcs_response = client.describe_vpcs()
    subnets_response = client.describe_subnets()
    route_tables_response = client.describe_route_tables()
    gateways_response = client.describe_internet_gateways()

    def tags_to_dict(tags):
        return {
            tag["Key"]: tag["Value"]
            for tag in (tags or [])
            if "Key" in tag and "Value" in tag
        }

    vpcs = []
    for item in vpcs_response.get("Vpcs", []):
        vpcs.append({
            "vpc_id": item.get("VpcId"),
            "state": item.get("State", "unknown"),
            "cidr_block": item.get("CidrBlock"),
            "is_default": item.get("IsDefault", False),
            "dhcp_options_id": item.get("DhcpOptionsId"),
            "region": client.meta.region_name,
            "tags": tags_to_dict(item.get("Tags")),
        })

    subnets = []
    for item in subnets_response.get("Subnets", []):
        subnets.append({
            "subnet_id": item.get("SubnetId"),
            "vpc_id": item.get("VpcId"),
            "cidr_block": item.get("CidrBlock"),
            "availability_zone": item.get("AvailabilityZone"),
            "state": item.get("State", "unknown"),
            "available_ip_address_count": item.get(
                "AvailableIpAddressCount", 0
            ),
            "map_public_ip_on_launch": item.get(
                "MapPublicIpOnLaunch", False
            ),
            "region": client.meta.region_name,
            "tags": tags_to_dict(item.get("Tags")),
        })

    route_tables = []
    for item in route_tables_response.get("RouteTables", []):
        routes = []
        for route in item.get("Routes", []):
            routes.append({
                "destination_cidr_block": route.get("DestinationCidrBlock"),
                "destination_ipv6_cidr_block": route.get(
                    "DestinationIpv6CidrBlock"
                ),
                "gateway_id": route.get("GatewayId"),
                "nat_gateway_id": route.get("NatGatewayId"),
                "state": route.get("State"),
            })

        route_tables.append({
            "route_table_id": item.get("RouteTableId"),
            "vpc_id": item.get("VpcId"),
            "routes": routes,
            "associations_count": len(item.get("Associations", [])),
            "region": client.meta.region_name,
            "tags": tags_to_dict(item.get("Tags")),
        })

    internet_gateways = []
    for item in gateways_response.get("InternetGateways", []):
        attachments = item.get("Attachments", [])
        internet_gateways.append({
            "internet_gateway_id": item.get("InternetGatewayId"),
            "attached_vpc_ids": [
                attachment.get("VpcId")
                for attachment in attachments
                if attachment.get("VpcId")
            ],
            "attachment_states": [
                attachment.get("State", "unknown")
                for attachment in attachments
            ],
            "is_attached": bool(attachments),
            "region": client.meta.region_name,
            "tags": tags_to_dict(item.get("Tags")),
        })

    return {
        "region": client.meta.region_name,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "vpcs": vpcs,
        "vpc_count": len(vpcs),
        "subnets": subnets,
        "subnet_count": len(subnets),
        "route_tables": route_tables,
        "route_table_count": len(route_tables),
        "internet_gateways": internet_gateways,
        "internet_gateway_count": len(internet_gateways),
        "detached_internet_gateway_count": sum(
            not gateway["is_attached"] for gateway in internet_gateways
        ),
    }


if __name__ == "__main__":
    import json

    inventory = collect_vpc_inventory()
    print(json.dumps(inventory, indent=2, default=str))
