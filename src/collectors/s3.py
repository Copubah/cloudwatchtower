
"""Read-only S3 bucket inventory collector."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError
def collect_s3_buckets(session=None):
    """Collect S3 bucket metadata without modifying resources."""
    session = session or boto3.Session()
    s3 = session.client("s3")
    buckets = []

    response = s3.list_buckets()

    for bucket in response.get("Buckets", []):
        name = bucket["Name"]

        try:
            location = s3.get_bucket_location(Bucket=name)
            region = location.get("LocationConstraint") or "us-east-1"

            versioning_response = s3.get_bucket_versioning(
                Bucket=name
            )
            versioning = versioning_response.get("Status", "Disabled")

            encryption = "Not configured"
            encryption_error = None

            try:
                encryption_response = (
                    s3.get_bucket_encryption(Bucket=name)
                )
                rules = encryption_response.get(
                    "ServerSideEncryptionConfiguration", {}
                ).get("Rules", [])

                algorithms = sorted({
                    rule.get(
                        "ApplyServerSideEncryptionByDefault", {}
                    ).get("SSEAlgorithm", "Unknown")
                    for rule in rules
                })

                encryption = (
                    ", ".join(algorithms) if algorithms
                    else "Not configured"
                )

            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")

                if code in (
                    "ServerSideEncryptionConfigurationNotFoundError",
                    "NoSuchEncryptionConfiguration",
                ):
                    encryption = "Not configured"
                else:
                    encryption = "Unknown"
                    encryption_error = code or "ClientError"

            buckets.append({
                "name": name,
                "creation_date": (
                    bucket.get("CreationDate").isoformat()
                    if bucket.get("CreationDate")
                    else None
                ),
                "region": region,
                "versioning": versioning,
                "encryption": encryption,
                "encryption_error": encryption_error,
            })

        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")

            buckets.append({
                "name": name,
                "creation_date": (
                    bucket.get("CreationDate").isoformat()
                    if bucket.get("CreationDate")
                    else None
                ),
                "region": "Unknown",
                "versioning": "Unknown",
                "encryption": "Unknown",
                "encryption_error": code or "ClientError",
            })

    return buckets


def main():
    try:
        buckets = collect_s3_buckets()

        print(f"S3 buckets found: {len(buckets)}")
        print("-" * 100)

        for bucket in buckets:
            print(
                f'{bucket["name"]} | '
                f'{bucket["region"]} | '
                f'Versioning: {bucket["versioning"]} | '
                f'Encryption: {bucket["encryption"]}'
            )

            if bucket["encryption_error"]:
                print(
                    "  Encryption inspection issue: "
                    f'{bucket["encryption_error"]}'
                )

    except (BotoCoreError, ClientError) as exc:
        print(f"S3 scan failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
