import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal
from app.services.analytics_report_service import AnalyticsReportService


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await AnalyticsReportService(db).send_test_month_to_date_report()
        print("Report sent.", result)


if __name__ == "__main__":
    asyncio.run(main())
