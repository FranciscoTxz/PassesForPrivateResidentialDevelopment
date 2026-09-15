from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware current UTC time."""
    return datetime.now(UTC)


def utcnow_naive() -> datetime:
    """Current UTC time as a naive datetime.

    MongoDB stores datetimes in UTC but returns naive values, so the whole
    application works with naive UTC datetimes to keep comparisons consistent.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def to_utc_naive(value: datetime) -> datetime:
    """Normalize any datetime to naive UTC."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
