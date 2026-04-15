from datetime import datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

PST = ZoneInfo("America/Los_Angeles")


def returning_caller_lookup_cutoff_utc(
    now_utc: Optional[datetime] = None,
) -> datetime:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    elif now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)
    now_local = now_utc.astimezone(PST)
    cutoff_24h = now_utc - timedelta(hours=24)
    if now_local.weekday() == 0:
        friday_date = now_local.date() - timedelta(days=3)
        friday_start_local = datetime.combine(friday_date, time.min, tzinfo=PST)
        friday_start_utc = friday_start_local.astimezone(timezone.utc)
        return min(cutoff_24h, friday_start_utc)
    return cutoff_24h


def is_off_hours() -> bool:
    now = datetime.now(PST)
    weekday = now.weekday()
    hour = now.hour

    if weekday in (5, 6):
        return True

    if weekday == 4 and hour >= 17:
        return True

    if weekday == 0 and hour < 8:
        return True

    if hour < 8 or hour >= 17:
        return True

    return False
