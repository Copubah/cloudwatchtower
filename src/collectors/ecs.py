
"""Collect read-only Amazon ECS cluster and service inventory."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError

def collect_ecs_inventory(region=None, session=None):
    """Return ECS clusters and their services in one AWS region."""
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
        client = session.client("ecs", region_name=current_region)

        try:
            cluster_arns = []
            paginator = client.get_paginator("list_clusters")

            for page in paginator.paginate():
                cluster_arns.extend(page.get("clusterArns", []))

            if not cluster_arns:
                continue

            for start in range(0, len(cluster_arns), 100):
                batch = cluster_arns[start:start + 100]
                response = client.describe_clusters(
                    clusters=batch,
                    include=["STATISTICS", "TAGS"],
                )

                for cluster in response.get("clusters", []):
                    services = []
                    service_paginator = client.get_paginator(
                        "list_services"
                    )

                    for page in service_paginator.paginate(
                        cluster=cluster["clusterArn"]
                    ):
                        services.extend(page.get("serviceArns", []))

                    service_details = []

                    for service_start in range(0, len(services), 10):
                        service_batch = services[
                            service_start:service_start + 10
                        ]

                        if not service_batch:
                            continue

                        service_response = client.describe_services(
                            cluster=cluster["clusterArn"],
                            services=service_batch,
                        )

                        for service in service_response.get(
                            "services", []
                        ):
                            service_details.append({
                                "service_name": service.get("serviceName"),
                                "status": service.get("status"),
                                "desired_count": service.get(
                                    "desiredCount", 0
                                ),
                                "running_count": service.get(
                                    "runningCount", 0
                                ),
                                "pending_count": service.get(
                                    "pendingCount", 0
                                ),
                                "launch_type": service.get(
                                    "launchType", "Unknown"
                                ),
                                "scheduling_strategy": service.get(
                                    "schedulingStrategy", "Unknown"
                                ),
                            })

                    inventory.append({
                        "cluster_name": cluster.get("clusterName"),
                        "cluster_arn": cluster.get("clusterArn"),
                        "status": cluster.get("status"),
                        "region": current_region,
                        "registered_container_instances": cluster.get(
                            "registeredContainerInstancesCount", 0
                        ),
                        "running_tasks": cluster.get(
                            "runningTasksCount", 0
                        ),
                        "pending_tasks": cluster.get(
                            "pendingTasksCount", 0
                        ),
                        "active_services": cluster.get(
                            "activeServicesCount", 0
                        ),
                        "services": service_details,
                    })

        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"Failed to collect ECS inventory in "
                f"{current_region}: {exc}"
            ) from exc

    return inventory


def main():
    clusters = collect_ecs_inventory()

    print(f"ECS clusters found: {len(clusters)}")

    for cluster in clusters:
        print(
            f"{cluster['cluster_name']}: "
            f"status={cluster['status']}, "
            f"running_tasks={cluster['running_tasks']}, "
            f"services={len(cluster['services'])}"
        )


if __name__ == "__main__":
    main()
