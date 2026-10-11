
"""Generate the combined CloudWatchtower AWS report."""

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
from src.cost.cost_explorer import collect_costs


def count_by(items, key):
    counts = {}
    for item in items:
        value = item.get(key) or "Unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


def generate_report(region=None):
    """Collect AWS costs and resource inventory without modifying resources."""

    ec2_instances = collect_ec2_instances(region=region)
    rds_instances = collect_rds_instances(region=region)
    s3_buckets = collect_s3_buckets()
    lambda_functions = collect_lambda_functions(region=region)
    ebs_volumes = collect_ebs_volumes(region=region)
    ecs_inventory = collect_ecs_inventory(region=region)
    load_balancers = collect_load_balancers(region=region)
    nat_gateways = collect_nat_gateways(region=region)
    elastic_ips = collect_elastic_ips(region=region)
    costs = collect_costs()

    ec2_state_counts = count_by(ec2_instances, "state")
    rds_state_counts = count_by(rds_instances, "status")
    lambda_state_counts = count_by(lambda_functions, "state")
    ebs_state_counts = count_by(ebs_volumes, "state")
    elb_type_counts = count_by(load_balancers, "type")
    nat_state_counts = count_by(nat_gateways, "state")
    nat_connectivity_counts = count_by(
        nat_gateways, "connectivity_type"
    )

    unattached_ebs_count = sum(
        1 for volume in ebs_volumes
        if not volume.get("attachments")
    )

    failed_nat_count = sum(
        1 for gateway in nat_gateways
        if gateway.get("state") == "failed"
    )

    running_tasks = sum(
        cluster.get("running_tasks", 0)
        for cluster in ecs_inventory
    )
    pending_tasks = sum(
        cluster.get("pending_tasks", 0)
        for cluster in ecs_inventory
    )
    total_services = sum(
        cluster.get("active_services", 0)
        for cluster in ecs_inventory
    )

    return {
        "generated_at_eat": datetime.now(
            ZoneInfo("Africa/Nairobi")
        ).isoformat(),
        "region": region or "default AWS region",
        "ec2": {
            "total": len(ec2_instances),
            "by_state": ec2_state_counts,
            "items": ec2_instances,
        },
        "rds": {
            "total": len(rds_instances),
            "by_status": rds_state_counts,
            "items": rds_instances,
        },
        "s3": {
            "total": len(s3_buckets),
            "items": s3_buckets,
        },
        "lambda": {
            "total": len(lambda_functions),
            "by_state": lambda_state_counts,
            "items": lambda_functions,
        },
        "ebs": {
            "total": len(ebs_volumes),
            "by_state": ebs_state_counts,
            "unattached_count": unattached_ebs_count,
            "items": ebs_volumes,
        },
        "ecs": {
            "total_clusters": len(ecs_inventory),
            "running_tasks": running_tasks,
            "pending_tasks": pending_tasks,
            "total_services": total_services,
            "items": ecs_inventory,
        },
        "load_balancers": {
            "total": len(load_balancers),
            "by_type": elb_type_counts,
            "items": load_balancers,
        },
        "nat_gateways": {
            "total": len(nat_gateways),
            "by_state": nat_state_counts,
            "by_connectivity_type": nat_connectivity_counts,
            "failed_count": failed_nat_count,
            "items": nat_gateways,
        },
        "elastic_ips": {
            "total": elastic_ips["total"],
            "associated_count": elastic_ips["associated_count"],
            "unassociated_count": elastic_ips["unassociated_count"],
            "failed_count": elastic_ips["failed_count"],
            "items": elastic_ips["items"],
        },
        "costs": costs,
    }


def main():
    report = generate_report()
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
