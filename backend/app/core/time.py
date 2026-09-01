"""
time.py — Real-time Indian Standard Time (IST, UTC+05:30) and UTC utilities.
Ensures all database records, telemetry timestamps, and normalized event timestamps
reflect exact real-time execution in IST.
"""
from datetime import datetime, timezone, timedelta

# Indian Standard Time offset: UTC+05:30
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


def ist_now() -> datetime:
    """Return timezone-aware current Indian Standard Time (IST)."""
    return datetime.now(IST)


def to_ist_iso(dt: datetime | None = None) -> str:
    """
    Format a datetime object to an ISO 8601 string in IST (+05:30).
    If dt is None, uses current real-time.
    """
    if dt is None:
        dt = datetime.now(IST)
    elif dt.tzinfo is None:
        # Naive datetime from SQLite/Postgres assumed to be UTC baseline
        dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
    else:
        dt = dt.astimezone(IST)
    return dt.isoformat()


def to_utc_iso(dt: datetime | None = None) -> str:
    """
    Format a datetime object to an ISO 8601 string in UTC (ending with Z).
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
