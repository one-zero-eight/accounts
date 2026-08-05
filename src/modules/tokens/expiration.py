__all__ = [
    "ServiceTokenExpiration",
    "nearest_14_august",
    "next_14_august",
    "resolve_service_token_expiration",
]

from datetime import UTC, datetime, timedelta
from enum import StrEnum

_ONE_MONTH = timedelta(days=30)


class ServiceTokenExpiration(StrEnum):
    auto = "auto"
    nearest_14_august = "nearest-14-august"
    next_14_august = "next-14-august"
    in_3_month = "in-3-month"


def _august_14(year: int) -> datetime:
    return datetime(year, 8, 14, tzinfo=UTC)


def nearest_14_august(now: datetime) -> datetime:
    """Upcoming Aug 14 (this year if still ahead, otherwise next year)."""
    this_year = _august_14(now.year)
    if now.date() < this_year.date():
        return this_year
    return _august_14(now.year + 1)


def next_14_august(now: datetime) -> datetime:
    """Aug 14 after the nearest one (skip nearest)."""
    nearest = nearest_14_august(now)
    return _august_14(nearest.year + 1)


def resolve_service_token_expiration(mode: ServiceTokenExpiration, *, now: datetime | None = None) -> datetime:
    """
    Resolve absolute JWT `exp` for a service token.

    - auto: nearest Aug 14 if more than a month away, otherwise next Aug 14
    - nearest-14-august / next-14-august: fixed Aug 14 targets
    - in-3-month: now + 90 days
    """
    now = now or datetime.now(UTC)
    if mode == ServiceTokenExpiration.in_3_month:
        return now + timedelta(days=90)

    nearest = nearest_14_august(now)
    if mode == ServiceTokenExpiration.nearest_14_august:
        return nearest
    if mode == ServiceTokenExpiration.next_14_august:
        return next_14_august(now)

    # auto
    if nearest - now > _ONE_MONTH:
        return nearest
    return next_14_august(now)
