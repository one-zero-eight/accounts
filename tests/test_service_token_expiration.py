from datetime import UTC, datetime, timedelta

import pytest

from src.modules.tokens.expiration import (
    ServiceTokenExpiration,
    nearest_14_august,
    next_14_august,
    resolve_service_token_expiration,
)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 8, 14, tzinfo=UTC)),
        (datetime(2026, 8, 13, tzinfo=UTC), datetime(2026, 8, 14, tzinfo=UTC)),
        (datetime(2026, 8, 14, tzinfo=UTC), datetime(2027, 8, 14, tzinfo=UTC)),
        (datetime(2026, 8, 15, tzinfo=UTC), datetime(2027, 8, 14, tzinfo=UTC)),
        (datetime(2026, 12, 31, tzinfo=UTC), datetime(2027, 8, 14, tzinfo=UTC)),
    ],
)
def test_nearest_14_august(now: datetime, expected: datetime):
    assert nearest_14_august(now) == expected


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 1, 1, tzinfo=UTC), datetime(2027, 8, 14, tzinfo=UTC)),
        (datetime(2026, 8, 14, tzinfo=UTC), datetime(2028, 8, 14, tzinfo=UTC)),
        (datetime(2026, 8, 15, tzinfo=UTC), datetime(2028, 8, 14, tzinfo=UTC)),
    ],
)
def test_next_14_august(now: datetime, expected: datetime):
    assert next_14_august(now) == expected


def test_auto_uses_nearest_when_more_than_a_month_away():
    now = datetime(2026, 6, 1, tzinfo=UTC)  # ~74 days before Aug 14
    assert resolve_service_token_expiration(ServiceTokenExpiration.auto, now=now) == datetime(2026, 8, 14, tzinfo=UTC)


def test_auto_uses_next_when_within_a_month():
    now = datetime(2026, 7, 20, tzinfo=UTC)  # ~25 days before Aug 14
    assert resolve_service_token_expiration(ServiceTokenExpiration.auto, now=now) == datetime(2027, 8, 14, tzinfo=UTC)


def test_explicit_modes():
    now = datetime(2026, 7, 20, tzinfo=UTC)
    assert resolve_service_token_expiration(ServiceTokenExpiration.nearest_14_august, now=now) == datetime(
        2026, 8, 14, tzinfo=UTC
    )
    assert resolve_service_token_expiration(ServiceTokenExpiration.next_14_august, now=now) == datetime(
        2027, 8, 14, tzinfo=UTC
    )


def test_in_3_month():
    now = datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC)
    assert resolve_service_token_expiration(ServiceTokenExpiration.in_3_month, now=now) == now + timedelta(days=90)
