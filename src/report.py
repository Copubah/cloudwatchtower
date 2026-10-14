
"""Build the CloudWatchtower AWS inventory and cost report."""

from datetime import datetime, timezone, timedelta
from src.collectors.ec2 import collect_ec2_instances
from src.collectors.rds import collect_rds_instances
from src.collectors.s3 import collect_s3_buckets
from src.collectors.lambda_functions import collect_lambda_functions
from src.collectors.ebs import collect_ebs_volumes
from src.collectors.ecs import collect_ecs_inventory
from src.collectors.elb import collect_load_balancers
from src.collectors.nat_gateway import collect_nat_gateways
from src.collectors.elastic_ips import collect_elastic_ips
from src.collectors.vpc import collect_vpc_inventory
from src.collectors.cloudwatch import collect_cloudwatch_inventory
from src.cost.cost_explorer import collect_costs
from src.security_findings import analyze_report


def build_report(region=None, session=None):
    """Collect AWS inventory and cost data, then analyze findings."""
    session = session or __import__("boto3").Session()
    region = region or session.region_name or "us-east-1"

    # Collect resource inventory.
    ec2_instances = collect_ec2_instances(region=region, session=session)
    rds_instances = collect_rds_instances(region=region, session=session)
    s3_buckets = collect_s3_buckets(session=session)
    lambda_functions = collect_lambda_functions(region=region, session=session)
    ebs_volumes = collect_ebs_volumes(region=region, session=session)
    ecs_inventory = collect_ecs_inventory(region=region, session=session)
    load_balancers = collect_load_balancers(region=region, session=session)
    nat_gateways = collect_nat_gateways(region=region, session=session)
    elastic_ips = collect_elastic_ips(region=region, session=session)
    vpc_inventory = collect_vpc_inventory(region=region, session=session)
    cloudwatch_inventory = collect_cloudwatch_inventory(
        region=region,
        session=session,
    )
    costs = collect_costs(session=session)

    # EC2 inventory.
    ec2 = {
        "total": len(ec2_instances),
        "running": sum(
            item.get("state") == "running" for item in ec2_instances
        ),
        "instances": ec2_instances,
    }

    # RDS inventory.
    rds = {
        "total": len(rds_instances),
        "publicly_accessible": sum(
            item.get("publicly_accessible") is True
            for item in rds_instances
        ),
        "unencrypted": sum(
            item.get("encrypted") is False for item in rds_instances
        ),
        "instances": rds_instances,
    }

    # S3 inventory.
    s3 = {
        "total": len(s3_buckets),
        "buckets": s3_buckets,
    }

    # Lambda inventory.
    lambda_summary = {
        "total": len(lambda_functions),
        "functions": lambda_functions,
    }

    # EBS inventory.
    ebs = {
        "total": len(ebs_volumes),
        "unattached": sum(
            item.get("state") == "available" for item in ebs_volumes
        ),
        "volumes": ebs_volumes,
    }

    # ECS collector returns a list of cluster dictionaries.
    ecs = {
        "total": len(ecs_inventory),
        "running_tasks": sum(
            cluster.get("running_tasks", 0)
            for cluster in ecs_inventory
        ),
        "pending_tasks": sum(
            cluster.get("pending_tasks", 0)
            for cluster in ecs_inventory
        ),
        "active_services": sum(
            cluster.get("active_services", 0)
            for cluster in ecs_inventory
        ),
        "clusters": ecs_inventory,
    }

    # Load balancers.
    load_balancer_items = (
        load_balancers.get("load_balancers", [])
        if isinstance(load_balancers, dict)
        else load_balancers
    )
    load_balancer_summary = {
        "total": len(load_balancer_items),
        "load_balancers": load_balancer_items,
    }

    # NAT gateways.
    nat_gateway_items = (
        nat_gateways.get("gateways", [])
        if isinstance(nat_gateways, dict)
        else nat_gateways
    )
    nat = {
        "total": len(nat_gateway_items),
        "available": sum(
            item.get("state") == "available"
            for item in nat_gateway_items
        ),
        "failed": sum(
            item.get("state") == "failed"
            for item in nat_gateway_items
        ),
        "gateways": nat_gateway_items,
    }

    # Elastic IP addresses.
    if isinstance(elastic_ips, dict):
        eip_items = elastic_ips.get("items", [])
        eips = {
            **elastic_ips,
            "total": elastic_ips.get("total", len(eip_items)),
            "items": eip_items,
        }
    else:
        eip_items = elastic_ips
        eips = {
            "total": len(eip_items),
            "items": eip_items,
        }

    # VPC inventory is retained as returned by its collector.
    vpc = vpc_inventory

    # CloudWatch monitoring inventory.
    cloudwatch = {
        **cloudwatch_inventory,
        "alarm_count": cloudwatch_inventory.get(
            "alarm_count",
            len(cloudwatch_inventory.get("alarms", [])),
        ),
        "composite_alarm_count": cloudwatch_inventory.get(
            "composite_alarm_count",
            len(cloudwatch_inventory.get("composite_alarms", [])),
        ),
        "log_group_count": cloudwatch_inventory.get(
            "log_group_count",
            len(cloudwatch_inventory.get("log_groups", [])),
        ),
    }

    eat = timezone(timedelta(hours=3))

    report = {
        "generated_at_eat": datetime.now(eat).isoformat(),
        "region": region,
        "ec2": ec2,
        "rds": rds,
        "s3": s3,
        "lambda": lambda_summary,
        "ebs": ebs,
        "ecs": ecs,
        "load_balancers": load_balancer_summary,
        "nat_gateways": nat,
        "elastic_ips": eips,
        "vpc": vpc,
        "cloudwatch": cloudwatch,
        "costs": costs,
    }

    # Analyze inventory without modifying AWS resources.
    report["security_findings"] = analyze_report(report)

    return report


if __name__ == "__main__":
    import json

    report_data = build_report()
    print(json.dumps(report_data, indent=2, default=str))
