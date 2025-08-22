import unittest
import datetime
from src.core.helpers import format_period_date

class TestFormatPeriodDate(unittest.TestCase):

    def test_format_with_timestamp(self):
        dt = datetime.datetime(2023, 10, 27, 10, 30, 0)
        ts = dt.timestamp()
        entry = {'timestamp': ts}
        self.assertEqual(format_period_date(entry, 'f'), "2023-10-27 10:30")
        self.assertEqual(format_period_date(entry, 'h'), "2023-10-27 10:00")
        self.assertEqual(format_period_date(entry, 'd'), "2023-10-27")
        self.assertEqual(format_period_date(entry, 't'), "2023-10-27")
        self.assertEqual(format_period_date(entry, 'm'), "2023-10")
        self.assertEqual(format_period_date(entry, 'y'), "2023")

    def test_format_with_full_date_object(self):
        entry = {
            'date': {'year': 2023, 'month': 10, 'day': 27},
            'time': {'hour': 14, 'minute': 30}
        }
        self.assertEqual(format_period_date(entry, 'f'), "2023-10-27 14:30")
        self.assertEqual(format_period_date(entry, 'h'), "2023-10-27 14:00")
        self.assertEqual(format_period_date(entry, 'd'), "2023-10-27")
        self.assertEqual(format_period_date(entry, 't'), "2023-10-27")
        self.assertEqual(format_period_date(entry, 'm'), "2023-10")
        self.assertEqual(format_period_date(entry, 'y'), "2023")

    def test_format_with_missing_day(self):
        entry = {'date': {'year': 2023, 'month': 10}}
        # These will not be called in practice for d, t, h, f but we test the behavior
        self.assertEqual(format_period_date(entry, 'd'), "2023-10")
        self.assertEqual(format_period_date(entry, 't'), "2023-10")
        self.assertEqual(format_period_date(entry, 'm'), "2023-10")
        self.assertEqual(format_period_date(entry, 'y'), "2023")

    def test_format_with_missing_month_and_day(self):
        entry = {'date': {'year': 2023}}
        self.assertEqual(format_period_date(entry, 'd'), "2023")
        self.assertEqual(format_period_date(entry, 't'), "2023")
        self.assertEqual(format_period_date(entry, 'm'), "2023")
        self.assertEqual(format_period_date(entry, 'y'), "2023")

    def test_invalid_period(self):
        entry = {'date': {'year': 2023}}
        self.assertEqual(format_period_date(entry, 'invalid'), "Invalid Period")

if __name__ == '__main__':
    unittest.main()