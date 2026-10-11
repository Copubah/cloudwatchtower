
"""Collect read-only AWS Elastic Load Balancing inventory."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError
def collect_load_balancers(region=None, session=None):
    """Collect ALB, NLB, and Classic Load Balancer inventory."""
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
        try:
            # Application and Network Load Balancers: ELBv2 API
            elbv2 = session.client(
                "elbv2", region_name=current_region
            )
            paginator = elbv2.get_paginator("describe_load_balancers")

            for page in paginator.paginate():
                for lb in page.get("LoadBalancers", []):
                    inventory.append({
                        "name": lb.get("LoadBalancerName"),
                        "arn": lb.get("LoadBalancerArn"),
                        "type": lb.get("Type", "Unknown"),
                        "scheme": lb.get("Scheme", "Unknown"),
                        "state": lb.get("State", {}).get(
                            "Code", "Unknown"
                        ),
                        "dns_name": lb.get("DNSName"),
                        "vpc_id": lb.get("VpcId"),
                        "availability_zones": [
                            zone.get("ZoneName")
                            for zone in lb.get("AvailabilityZones", [])
                        ],
                        "security_groups": lb.get("SecurityGroups", []),
                        "created_at": (
                            lb["CreatedTime"].isoformat()
                            if lb.get("CreatedTime")
                            else None
                        ),
                        "region": current_region,
                    })

            # Classic Load Balancers: ELB API
            classic = session.client(
                "elb", region_name=current_region
            )
            classic_paginator = classic.get_paginator(
                "describe_load_balancers"
            )

            for page in classic_paginator.paginate():
                for lb in page.get("LoadBalancerDescriptions", []):
                    inventory.append({
                        "name": lb.get("LoadBalancerName"),
                        "arn": None,
                        "type": "classic",
                        "scheme": lb.get("Scheme", "Unknown"),
                        "state": "Unknown",
                        "dns_name": lb.get("DNSName"),
                        "vpc_id": lb.get("VPCId"),
                        "availability_zones": lb.get(
                            "AvailabilityZones", []
                        ),
                        "security_groups": lb.get("SecurityGroups", []),
                        "created_at": (
                            lb["CreatedTime"].isoformat()
                            if lb.get("CreatedTime")
                            else None
                        ),
                        "region": current_region,
                    })

        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"Failed to collect load balancers in "
                f"{current_region}: {exc}"
            ) from exc

    return inventory


def main():
    load_balancers = collect_load_balancers()

    print(f"Load balancers found: {len(load_balancers)}")

    for lb in load_balancers:
        print(
            f"{lb['name']}: type={lb['type']}, "
            f"scheme={lb['scheme']}, state={lb['state']}, "
            f"region={lb['region']}"
        )


if __name__ == "__main__":
    main()
