# iso-weeks-lib

ISO-8601 week-date helpers for Python: convert between `datetime.date` and `(iso_year, iso_week, iso_weekday)`, with validation that catches the boundary cases that surprise people.

## Usage

```python
from iso_weeks_lib import (
    IsoWeekDate,
    date_to_iso_week,
    iso_week_to_date,
    iso_week_to_str,
    weeks_in_iso_year,
)
import datetime

# A date late in December can belong to the NEXT ISO year.
assert date_to_iso_week(datetime.date(2025, 12, 31)) == (2026, 1, 3)

# A date on January 1st can belong to the PREVIOUS ISO year.
assert date_to_iso_week(datetime.date(2016, 1, 1)) == (2015, 53, 5)

# Not every ISO year has a week 53.
assert weeks_in_iso_year(2021) == 52
assert weeks_in_iso_year(2020) == 53

# Convert back and forth, with validation.
d = iso_week_to_date(2026, 1, 1)
assert d == datetime.date(2025, 12, 29)

# Canonical string format (YYYY-Www-D).
assert iso_week_to_str(2024, 1, 1) == "2024-W01-1"

# Immutable value object.
iwd = IsoWeekDate.from_str("2020-W53-7")
assert iwd.date == datetime.date(2021, 1, 3)
assert iwd.to_str() == "2020-W53-7"
```

## Why this exists

ISO-8601 weeks start on Monday, and week 1 of an ISO year is the week containing the first Thursday. Because of that rule, January 1st and December 31st of a Gregorian year frequently belong to the *adjacent* ISO year. Code that assumes the ISO year equals the Gregorian year is wrong about one or two days per year, and wrong by a full week near the boundaries.

This library wraps the standard library's `date.isocalendar()` and `date.fromisocalendar()` with a small, strict layer: plain-int return types, an immutable `IsoWeekDate` value object, and validation that rejects week 53 in years that only have 52 weeks. The trade-off is that we refuse to guess — if you ask for a week that does not exist, you get a `ValueError`, not a clamped or shifted date.

## The edge you will hit

`2020-12-31` is in ISO week 2020-W53, but `2021-12-31` is in ISO week `2021-W52`. Both December 31sts look identical on the calendar; only one has a week 53. If your downstream code assumes "last week of the year is 53," it will break on 52-week years like 2021. `weeks_in_iso_year` exists so you can check before you index.

## API

All names below are exported from `iso_weeks_lib`:

- `date_to_iso_week(d: datetime.date) -> tuple[int, int, int]` — returns `(iso_year, iso_week, iso_weekday)`.
- `iso_week_to_date(iso_year: int, iso_week: int, iso_weekday: int = 1) -> datetime.date` — validates ranges and raises `ValueError` for non-existent weeks.
- `iso_week_to_str(iso_year: int, iso_week: int, iso_weekday: int = 1) -> str` — canonical `YYYY-Www-D` string; validates first.
- `weeks_in_iso_year(iso_year: int) -> int` — returns 52 or 53.
- `IsoWeekDate(iso_year, iso_week, iso_weekday=1)` — frozen dataclass; validates on construction. Has `.date` (property), `.to_str()`, and `.from_str(s)`.

No third-party dependencies. Python 3.8+ (uses `date.fromisocalendar`).
