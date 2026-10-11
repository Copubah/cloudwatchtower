
"""Read-only AWS IAM inventory for CloudWatchtower."""

from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


def collect_iam_inventory(session=None):
    """Collect IAM users, roles, customer-managed policies and key metadata."""
    session = session or boto3.Session()
    iam = session.client("iam")

    users = []
    user_paginator = iam.get_paginator("list_users")

    for page in user_paginator.paginate():
        for user in page.get("Users", []):
            username = user["UserName"]

            keys_response = iam.list_access_keys(UserName=username)
            access_keys = []

            for key in keys_response.get("AccessKeyMetadata", []):
                key_id = key.get("AccessKeyId")
                last_used_date = None
                last_used_service = None
                last_used_region = None

                if key_id:
                    try:
                        last_used = iam.get_access_key_last_used(
                            AccessKeyId=key_id
                        ).get("AccessKeyLastUsed", {})

                        last_used_date = last_used.get("LastUsedDate")
                        last_used_service = last_used.get("ServiceName")
                        last_used_region = last_used.get("Region")
                    except ClientError:
                        # Preserve the key metadata if last-used lookup fails.
                        pass

                access_keys.append(
                    {
                        "access_key_id": key_id,
                        "status": key.get("Status"),
                        "created_at": key.get("CreateDate"),
                        "last_used_at": last_used_date,
                        "last_used_service": last_used_service,
                        "last_used_region": last_used_region,
                    }
                )

            try:
                iam.get_login_profile(UserName=username)
                console_password_enabled = True
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") == "NoSuchEntity":
                    console_password_enabled = False
                else:
                    console_password_enabled = None

            mfa_response = iam.list_mfa_devices(UserName=username)

            users.append(
                {
                    "username": username,
                    "user_id": user.get("UserId"),
                    "arn": user.get("Arn"),
                    "created_at": user.get("CreateDate"),
                    "password_last_used": user.get("PasswordLastUsed"),
                    "console_password_enabled": console_password_enabled,
                    "mfa_enabled": bool(
                        mfa_response.get("MFADevices", [])
                    ),
                    "access_keys": access_keys,
                    "access_key_count": len(access_keys),
                    "active_access_key_count": sum(
                        key.get("status") == "Active"
                        for key in access_keys
                    ),
                }
            )

    roles = []
    role_paginator = iam.get_paginator("list_roles")

    for page in role_paginator.paginate():
        for role in page.get("Roles", []):
            roles.append(
                {
                    "role_name": role.get("RoleName"),
                    "role_id": role.get("RoleId"),
                    "arn": role.get("Arn"),
                    "created_at": role.get("CreateDate"),
                    "max_session_duration": role.get("MaxSessionDuration"),
                    "description": role.get("Description"),
                    "path": role.get("Path"),
                }
            )

    policies = []
    policy_paginator = iam.get_paginator("list_policies")

    for page in policy_paginator.paginate(Scope="Local"):
        for policy in page.get("Policies", []):
            policies.append(
                {
                    "policy_name": policy.get("PolicyName"),
                    "policy_id": policy.get("PolicyId"),
                    "arn": policy.get("Arn"),
                    "created_at": policy.get("CreateDate"),
                    "updated_at": policy.get("UpdateDate"),
                    "attachment_count": policy.get("AttachmentCount", 0),
                    "default_version_id": policy.get("DefaultVersionId"),
                    "is_attachable": policy.get("IsAttachable"),
                }
            )

    return {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "user_count": len(users),
        "users_without_mfa": sum(
            not user["mfa_enabled"] for user in users
        ),
        "users_with_console_password": sum(
            user["console_password_enabled"] is True for user in users
        ),
        "active_access_key_count": sum(
            user["active_access_key_count"] for user in users
        ),
        "role_count": len(roles),
        "customer_managed_policy_count": len(policies),
        "users": users,
        "roles": roles,
        "customer_managed_policies": policies,
    }


if __name__ == "__main__":
    import json

    inventory = collect_iam_inventory()
    print(json.dumps(inventory, indent=2, default=str))
