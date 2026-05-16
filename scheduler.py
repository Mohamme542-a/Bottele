"""فحص ما إذا كان الرد التلقائي مفعّلاً حالياً حسب الجدولة."""
from datetime import datetime
import pytz


def is_active_now(schedule):
    if not schedule or not schedule.get("enabled"):
        return True
    tz_name = schedule.get("timezone", "UTC")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.UTC
    now = datetime.now(tz)
    weekday = (now.weekday() + 1) % 7  # python: Mon=0; we want Sun=0
    if weekday not in (schedule.get("active_days") or []):
        return False
    cur = now.strftime("%H:%M")
    start = schedule.get("start_time", "00:00")[:5]
    end = schedule.get("end_time", "23:59")[:5]
    if start <= end:
        return start <= cur <= end
    return cur >= start or cur <= end
