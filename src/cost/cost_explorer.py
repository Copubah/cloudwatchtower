"""Read-only AWS Cost Explorer data collector."""
from datetime import date, timedelta
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def collect_costs(session=None, end_date=None):
    """Return month-to-date cost and daily service breakdowns.

    Cost Explorer uses an exclusive End date.
    """
    session = session or boto3.Session()
    client = session.client("ce", region_name="us-east-1")

    today = end_date or date.today()
    start = today.replace(day=1)
    end = today + timedelta(days=1)

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start.isoformat(),
            "End": end.isoformat(),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"}
        ],
    )

    daily_costs = []

    for period in response.get("ResultsByTime", []):
        services = []

        for group in period.get("Groups", []):
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            services.append({
                "service": group["Keys"][0],
                "amount": round(amount, 6),
                "unit": group["Metrics"]["UnblendedCost"]["Unit"],
            })

        daily_costs.append({
            "date": period["TimePeriod"]["Start"],
            "total": round(
                sum(item["amount"] for item in services), 6
            ),
            "services": sorted(
                services,
                key=lambda item: item["amount"],
                reverse=True,
            ),
        })

    currency = next(
        (
            group["Metrics"]["UnblendedCost"]["Unit"]
            for period in response.get("ResultsByTime", [])
            for group in period.get("Groups", [])
        ),
        "USD",
    )

    return {
        "period_start": start.isoformat(),
        "period_end_exclusive": end.isoformat(),
        "currency": currency,
        "daily_costs": daily_costs,
        "month_to_date": round(
            sum(day["total"] for day in daily_costs), 6
        ),
    }


def main():
    try:
        report = collect_costs()

        print("AWS COST REPORT")
        print("=" * 60)
        print(f"Period: {report['period_start']} to "
              f"{report['period_end_exclusive']} (exclusive)")
        print(f"Month-to-date: {report['currency']} "
              f"{report['month_to_date']:.2f}")

        for day in report["daily_costs"]:
            print(f"\nDate: {day['date']}")
            print(f"Total: {report['currency']} {day['total']:.2f}")

            for service in day["services"]:
                print(
                    f"  {service['service']}: "
                    f"{service['amount']:.2f} {service['unit']}"
                )

    except (BotoCoreError, ClientError) as exc:
        print(f"Cost collection failed: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()