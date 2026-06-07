import datetime


def today_timestamps() -> tuple[int, int]:
    now = datetime.datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(start.timestamp() * 1000), int(now.timestamp() * 1000)


def yesterday_timestamps() -> tuple[int, int]:
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end   = yesterday.replace(hour=23, minute=59, second=59)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def day_timestamps(date: datetime.date) -> tuple[int, int]:
    start = datetime.datetime.combine(date, datetime.time.min)
    end   = datetime.datetime.combine(date, datetime.time.max)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def storage_status(days: int) -> str:
    if days >= 60:   return "paid"
    if days >= 57:   return "critical"
    if days >= 53:   return "warn"
    return "ok"


def format_money(n) -> str:
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return str(n)
