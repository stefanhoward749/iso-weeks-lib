"""Core ISO-8601 week-date logic.

ISO-8601 defines weeks that start on Monday and assigns week 1 of a year
to the week containing the first Thursday. This means:

  * January 1st can fall in week 52, 53, or week 1 of the adjacent ISO year.
  * December 31st can likewise belong to the *next* ISO year.

These boundary cases are the reason this library exists.

Design decisions (stated plainly so the tests match the code):

  1. We use CPython's ``datetime.date.isocalendar()`` for the heavy lifting.
     Its output is a 3-tuple ``(iso_year, iso_week, iso_weekday)``. We rely
     on the standard library's battle-tested implementation rather than
     re-deriving ISO calendar arithmetic from scratch.

  2. We accept and return only ``datetime.date`` and ``int`` — no string
     parsing of arbitrary formats. ``iso_week_to_str`` produces the canonical
     "YYYY-Www-D" string; ``iso_week_to_date`` consumes it. We do not parse
     partial strings (e.g. bare "2024-W01"). One format, one parser.

  3. ``iso_week_to_date`` raises ``ValueError`` for out-of-range week numbers
     or weekdays, and for weeks that do not exist in a given ISO year
     (a year with 52 weeks does not have week 53). This is a stricter check
     than many libraries, which silently clamp. We prefer loud failures.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass

# Canonical ISO week-date string: 4-digit year, 2-digit week, 1-digit day.
_ISO_WEEK_STR_RE = re.compile(r"^(\d{4})-W(\d{2})-(\d)$")


def date_to_iso_week(d: datetime.date) -> tuple[int, int, int]:
    """Return the ISO-8601 ``(iso_year, iso_week, iso_weekday)`` for *d*.

    A thin wrapper around ``date.isocalendar()`` that returns a plain tuple
    of plain ints (not ``datetime.IsoCalendarDate``), so callers on older
    Python versions and newer ones see identical types.
    """
    iso_year, iso_week, iso_weekday = d.isocalendar()
    return (int(iso_year), int(iso_week), int(iso_weekday))


def iso_week_to_date(
    iso_year: int, iso_week: int, iso_weekday: int = 1
) -> datetime.date:
    """Return the ``date`` for a given ISO week and weekday.

    ``iso_weekday`` uses ISO-8601 numbering: Monday = 1 ... Sunday = 7.

    Raises ``ValueError`` if the week or day is out of range, including
    requesting week 53 in a year that only has 52 weeks.
    """
    if not 1 <= iso_weekday <= 7:
        raise ValueError(
            f"iso_weekday must be 1-7 (Monday-Sunday); got {iso_weekday}"
        )

    max_weeks = weeks_in_iso_year(iso_year)
    if not 1 <= iso_week <= max_weeks:
        raise ValueError(
            f"iso_week must be 1-{max_weeks} for ISO year {iso_year}; "
            f"got {iso_week}"
        )

    # fromisocalendar validates range, but since we already checked, call it
    # directly. It is available on Python 3.8+.
    return datetime.date.fromisocalendar(iso_year, iso_week, iso_weekday)


def iso_week_to_str(
    iso_year: int, iso_week: int, iso_weekday: int = 1
) -> str:
    """Return the canonical ISO-8601 string ``YYYY-Www-D``.

    Calls ``iso_week_to_date`` first so the same validation applies.
    """
    # Reuse the validation logic.
    iso_week_to_date(iso_year, iso_week, iso_weekday)
    return f"{iso_year:04d}-W{iso_week:02d}-{iso_weekday}"


def weeks_in_iso_year(iso_year: int) -> int:
    """Return the number of weeks in an ISO year: 52 or 53.

    An ISO year has 53 weeks if, and only if, January 1st of that year
    falls on a Thursday, or — equivalently — January 1st falls on a
    Wednesday in a leap year. We check January 1st's weekday directly.
    """
    jan1 = datetime.date(iso_year, 1, 1)
    is_leap = (
        iso_year % 4 == 0 and (iso_year % 100 != 0 or iso_year % 400 == 0)
    )
    if jan1.weekday() == 3:  # Thursday
        return 53
    if jan1.weekday() == 2 and is_leap:  # Wednesday in a leap year
        return 53
    return 52


@dataclass(frozen=True)
class IsoWeekDate:
    """An immutable ISO-8601 week date.

    Fields are pre-validated on construction so that an ``IsoWeekDate``
    instance is always a real, representable date.
    """

    iso_year: int
    iso_week: int
    iso_weekday: int = 1

    def __post_init__(self) -> None:
        # Validate by constructing the underlying date; if it raises, we
        # propagate the ValueError to the caller immediately.
        iso_week_to_date(self.iso_year, self.iso_week, self.iso_weekday)

    @property
    def date(self) -> datetime.date:
        """The Gregorian ``date`` this ISO week date refers to."""
        return iso_week_to_date(self.iso_year, self.iso_week, self.iso_weekday)

    def to_str(self) -> str:
        """Canonical ``YYYY-Www-D`` representation."""
        return iso_week_to_str(self.iso_year, self.iso_week, self.iso_weekday)

    @classmethod
    def from_str(cls, s: str) -> "IsoWeekDate":
        """Parse a canonical ``YYYY-Www-D`` string.

        Only the exact format produced by ``to_str`` is accepted.
        """
        m = _ISO_WEEK_STR_RE.match(s)
        if m is None:
            raise ValueError(
                f"expected 'YYYY-Www-D' (e.g. 2024-W01-1); got {s!r}"
            )
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))
