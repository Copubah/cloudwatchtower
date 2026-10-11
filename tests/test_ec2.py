from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.collectors.ec2 import collect_ec2_instances


def test_collect_ec2_instances():
    session = MagicMock()
    session.region_name = "eu-west-1"

    ec2 = MagicMock()
    session.client.return_value = ec2

    launch_time = datetime(2026, 10, 1, tzinfo=timezone.utc)

    ec2.get_paginator.return_value.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-test123",
                            "InstanceType": "t3.micro",
                            "State": {"Name": "running"},
                            "LaunchTime": launch_time,
                            "Placement": {
                                "AvailabilityZone": "eu-west-1a"
                            },
                            "Tags": [
                                {"Key": "Name", "Value": "dev-server"}
                            ],
                        }
                    ]
                }
            ]
        }
    ]

    instances = collect_ec2_instances(session=session)

    assert len(instances) == 1
    assert instances[0]["instance_id"] == "i-test123"
    assert instances[0]["name"] == "dev-server"
    assert instances[0]["state"] == "running"
    assert instances[0]["region"] == "eu-west-1"

    session.client.assert_called_once_with(
        "ec2", region_name="eu-west-1"
    )