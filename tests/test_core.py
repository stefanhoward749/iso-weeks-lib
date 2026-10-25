"""Tests for iso_weeks_lib.core.

Covers the boundary cases that make ISO weeks surprising.
"""

import datetime
import unittest

from iso_weeks_lib.core import (
    IsoWeekDate,
    date_to_iso_week,
    iso_week_to_date,
    iso_week_to_str,
    weeks_in_iso_year,
)


class TestDateToIsoWeek(unittest.TestCase):
    def test_midyear_weekday(self):
        # 2024-06-15 is a Saturday in ISO week 24 of ISO year 2024.
        d = datetime.date(2024, 6, 15)
        self.assertEqual(date_to_iso_week(d), (2024, 24, 6))

    def test_jan_1_in_previous_iso_year(self):
        # 2016-01-01 is a Friday, so it belongs to ISO week 53 of 2015.
        d = datetime.date(2016, 1, 1)
        self.assertEqual(date_to_iso_week(d), (2015, 53, 5))

    def test_dec_31_in_next_iso_year(self):
        # 2025-12-31 is a Wednesday, in ISO week 1 of 2026.
        d = datetime.date(2025, 12, 31)
        self.assertEqual(date_to_iso_week(d), (2026, 1, 3))

    def test_returns_plain_tuple_of_ints(self):
        d = datetime.date(2024, 1, 1)
        result = date_to_iso_week(d)
        self.assertIsInstance(result, tuple)
        for item in result:
            self.assertIsInstance(item, int)


class TestWeeksInIsoYear(unittest.TestCase):
    def test_2020_has_53_weeks(self):
        # 2020 is a 53-week ISO year.
        self.assertEqual(weeks_in_iso_year(2020), 53)

    def test_2021_has_52_weeks(self):
        self.assertEqual(weeks_in_iso_year(2021), 52)

    def test_2026_has_53_weeks(self):
        # 2026 is a 53-week ISO year.
        self.assertEqual(weeks_in_iso_year(2026), 53)

    def test_2027_has_52_weeks(self):
        self.assertEqual(weeks_in_iso_year(2027), 52)


class TestIsoWeekToDate(unittest.TestCase):
    def test_week_1_day_1_of_2024(self):
        self.assertEqual(
            iso_week_to_date(2024, 1, 1), datetime.date(2024, 1, 1)
        )

    def test_week_53_of_2020(self):
        # ISO 2020-W53-7 is Sunday 2021-01-03.
        self.assertEqual(
            iso_week_to_date(2020, 53, 7), datetime.date(2021, 1, 3)
        )

    def test_week_1_of_2026_is_in_dec_2025(self):
        # ISO 2026-W01-1 is Monday 2025-12-29.
        self.assertEqual(
            iso_week_to_date(2026, 1, 1), datetime.date(2025, 12, 29)
        )

    def test_invalid_weekday(self):
        with self.assertRaises(ValueError):
            iso_week_to_date(2024, 1, 0)
        with self.assertRaises(ValueError):
            iso_week_to_date(2024, 1, 8)

    def test_week_53_in_52_week_year(self):
        # 2021 has only 52 weeks; requesting week 53 must fail.
        with self.assertRaises(ValueError):
            iso_week_to_date(2021, 53, 1)

    def test_week_0_rejected(self):
        with self.assertRaises(ValueError):
            iso_week_to_date(2024, 0, 1)


class TestIsoWeekToStr(unittest.TestCase):
    def test_canonical_format(self):
        self.assertEqual(iso_week_to_str(2024, 1, 1), "2024-W01-1")

    def test_week_10_padded(self):
        self.assertEqual(iso_week_to_str(2024, 10, 7), "2024-W10-7")

    def test_str_validation(self):
        # Invalid week triggers ValueError before formatting.
        with self.assertRaises(ValueError):
            iso_week_to_str(2021, 53, 1)


class TestIsoWeekDate(unittest.TestCase):
    def test_construct_and_to_str(self):
        iwd = IsoWeekDate(2024, 1, 1)
        self.assertEqual(iwd.to_str(), "2024-W01-1")
        self.assertEqual(iwd.date, datetime.date(2024, 1, 1))

    def test_from_str_roundtrip(self):
        iwd = IsoWeekDate.from_str("2024-W01-1")
        self.assertEqual(iwd.iso_year, 2024)
        self.assertEqual(iwd.iso_week, 1)
        self.assertEqual(iwd.iso_weekday, 1)

    def test_from_str_roundtrip_week_53(self):
        iwd = IsoWeekDate.from_str("2020-W53-7")
        self.assertEqual(iwd.to_str(), "2020-W53-7")
        self.assertEqual(iwd.date, datetime.date(2021, 1, 3))

    def test_from_str_bad_format(self):
        with self.assertRaises(ValueError):
            IsoWeekDate.from_str("2024-W1-1")
        with self.assertRaises(ValueError):
            IsoWeekDate.from_str("2024W011")

    def test_construct_invalid_week(self):
        with self.assertRaises(ValueError):
            IsoWeekDate(2021, 53, 1)

    def test_default_weekday_is_monday(self):
        iwd = IsoWeekDate(2024, 1)
        self.assertEqual(iwd.iso_weekday, 1)
        self.assertEqual(iwd.date, datetime.date(2024, 1, 1))

    def test_immutable(self):
        iwd = IsoWeekDate(2024, 1, 1)
        with self.assertRaises(Exception):
            iwd.iso_week = 2  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
