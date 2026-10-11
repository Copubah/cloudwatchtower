
"""Build a consolidated AWS cost and resource inventory report."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo
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


def build_report(region=None):
    """Collect AWS costs, resource inventory, and monitoring metadata."""

    region = region or "us-east-1"

    generated_at_eat = datetime.now(
        ZoneInfo("Africa/Nairobi")
    ).isoformat()

    # Collect AWS resource inventories.
    ec2_instances = collect_ec2_instances(region=region)
    rds_instances = collect_rds_instances(region=region)
    s3_buckets = collect_s3_buckets()
    lambda_functions = collect_lambda_functions(region=region)
    ebs_volumes = collect_ebs_volumes(region=region)
    ecs_inventory = collect_ecs_inventory(region=region)
    load_balancers = collect_load_balancers(region=region)
    nat_gateways = collect_nat_gateways(region=region)
    elastic_ips = collect_elastic_ips(region=region)
    vpc_inventory = collect_vpc_inventory(region=region)
    cloudwatch_inventory = collect_cloudwatch_inventory(region=region)

    # Collect AWS Cost Explorer data.
    costs = collect_costs()

    # EC2 summary.
    ec2_by_state = {}
    for instance in ec2_instances:
        state = instance.get("state", "unknown")
        ec2_by_state[state] = ec2_by_state.get(state, 0) + 1

    # RDS summary.
    rds_by_status = {}
    for instance in rds_instances:
        status = instance.get("status", "unknown")
        rds_by_status[status] = rds_by_status.get(status, 0) + 1

    # Lambda summary.
    lambda_by_state = {}
    for function in lambda_functions:
        state = function.get("state", "unknown")
        lambda_by_state[state] = lambda_by_state.get(state, 0) + 1

    # EBS summary.
    ebs_by_state = {}
    unattached_volumes = 0

    for volume in ebs_volumes:
        state = volume.get("state", "unknown")
        ebs_by_state[state] = ebs_by_state.get(state, 0) + 1

        if not volume.get("attachments"):
            unattached_volumes += 1

    # ECS summary.
    total_ecs_running_tasks = sum(
        cluster.get("running_tasks", 0)
        for cluster in ecs_inventory
    )
    total_ecs_pending_tasks = sum(
        cluster.get("pending_tasks", 0)
        for cluster in ecs_inventory
    )
    total_ecs_services = sum(
        cluster.get("active_services", 0)
        for cluster in ecs_inventory
    )

    # Load balancer summary.
    load_balancers_by_type = {}
    for load_balancer in load_balancers:
        lb_type = load_balancer.get("type", "unknown")
        load_balancers_by_type[lb_type] = (
            load_balancers_by_type.get(lb_type, 0) + 1
        )

    # NAT gateway summary.
    nat_by_state = {}
    nat_by_connectivity = {}

    for gateway in nat_gateways:
        state = gateway.get("state", "unknown")
        nat_by_state[state] = nat_by_state.get(state, 0) + 1

        connectivity = gateway.get("connectivity_type", "unknown")
        nat_by_connectivity[connectivity] = (
            nat_by_connectivity.get(connectivity, 0) + 1
        )

    failed_nat_gateways = sum(
        gateway.get("state") == "failed"
        for gateway in nat_gateways
    )

    # VPC inventory summary.
    vpcs = vpc_inventory.get("vpcs", [])
    subnets = vpc_inventory.get("subnets", [])
    route_tables = vpc_inventory.get("route_tables", [])
    internet_gateways = vpc_inventory.get("internet_gateways", [])

    # Consolidated report.
    return {
        "generated_at_eat": generated_at_eat,
        "region": region,

        "ec2": {
            "total": len(ec2_instances),
            "by_state": ec2_by_state,
            "items": ec2_instances,
        },

        "rds": {
            "total": len(rds_instances),
            "by_status": rds_by_status,
            "items": rds_instances,
        },

        "s3": {
            "total": len(s3_buckets),
            "items": s3_buckets,
        },

        "lambda": {
            "total": len(lambda_functions),
            "by_state": lambda_by_state,
            "items": lambda_functions,
        },

        "ebs": {
            "total": len(ebs_volumes),
            "by_state": ebs_by_state,
            "unattached_count": unattached_volumes,
            "items": ebs_volumes,
        },

        "ecs": {
            "total_clusters": len(ecs_inventory),
            "running_tasks": total_ecs_running_tasks,
            "pending_tasks": total_ecs_pending_tasks,
            "total_services": total_ecs_services,
            "items": ecs_inventory,
        },

        "load_balancers": {
            "total": len(load_balancers),
            "by_type": load_balancers_by_type,
            "items": load_balancers,
        },

        "nat_gateways": {
            "total": len(nat_gateways),
            "by_state": nat_by_state,
            "by_connectivity_type": nat_by_connectivity,
            "failed_count": failed_nat_gateways,
            "items": nat_gateways,
        },

        "elastic_ips": {
            "total": sum(
                item.get("total", 0)
                for item in [elastic_ips]
            ),
            "associated_count": elastic_ips.get("associated_count", 0),
            "unassociated_count": elastic_ips.get("unassociated_count", 0),
            "failed_count": elastic_ips.get("failed_count", 0),
            "items": elastic_ips.get("items", []),
        },

        "vpc": {
            "total": len(vpcs),
            "subnet_count": len(subnets),
            "route_table_count": len(route_tables),
            "internet_gateway_count": len(internet_gateways),
            "detached_internet_gateway_count": (
                vpc_inventory.get("detached_internet_gateway_count", 0)
            ),
            "items": vpcs,
            "subnets": subnets,
            "route_tables": route_tables,
            "internet_gateways": internet_gateways,
        },

        "cloudwatch": {
            "region": cloudwatch_inventory["region"],
            "alarm_count": cloudwatch_inventory["alarm_count"],
            "alarms_in_alarm_state": (
                cloudwatch_inventory["alarms_in_alarm_state"]
            ),
            "composite_alarm_count": (
                cloudwatch_inventory["composite_alarm_count"]
            ),
            "log_group_count": cloudwatch_inventory["log_group_count"],
            "log_groups_without_retention": (
                cloudwatch_inventory["log_groups_without_retention"]
            ),
            "alarms": cloudwatch_inventory["alarms"],
            "composite_alarms": cloudwatch_inventory["composite_alarms"],
            "log_groups": cloudwatch_inventory["log_groups"],
        },

        "costs": costs,
    }


def main():
    """Print the report as JSON."""
    report = build_report()
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
