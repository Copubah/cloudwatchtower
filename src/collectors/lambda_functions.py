
"""Read-only AWS Lambda inventory collector."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def collect_lambda_functions(region=None, session=None):
    """Collect Lambda function metadata without modifying resources."""
    session = session or boto3.Session()
    region = region or session.region_name

    if not region:
        raise ValueError(
            "No AWS region configured. Set AWS_DEFAULT_REGION "
            "or pass region explicitly."
        )

    client = session.client("lambda", region_name=region)
    paginator = client.get_paginator("list_functions")
    functions = []

    for page in paginator.paginate():
        for function in page.get("Functions", []):
            functions.append({
                "function_name": function["FunctionName"],
                "function_arn": function.get("FunctionArn"),
                "runtime": function.get("Runtime", "Not specified"),
                "package_type": function.get("PackageType", "Zip"),
                "state": function.get("State", "Unknown"),
                "last_update_status": function.get(
                    "LastUpdateStatus", "Unknown"
                ),
                "memory_mb": function.get("MemorySize"),
                "timeout_seconds": function.get("Timeout"),
                "architecture": ", ".join(
                    function.get("Architectures", [])
                ),
                "region": region,
                "last_modified": function.get("LastModified"),
                "role": function.get("Role"),
            })

    return functions


def main():
    try:
        functions = collect_lambda_functions()

        print(f"Lambda functions found: {len(functions)}")
        print("-" * 110)

        for function in functions:
            print(
                f'{function["function_name"]} | '
                f'{function["runtime"]} | '
                f'{function["state"]} | '
                f'Memory: {function["memory_mb"]} MB | '
                f'Timeout: {function["timeout_seconds"]} seconds | '
                f'{function["region"]}'
            )

    except (BotoCoreError, ClientError, ValueError) as exc:
        print(f"Lambda scan failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
