import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import converter
from converter import convert

LEAK_WORDS = ("Traceback", "Exception", "Error:", "InvalidOperation", "Decimal(", "File \"")


class FailureCases(unittest.TestCase):
    def check(self, args, code, expected_text):
        with self.assertLogs("currency_converter", level="WARNING") as logs:
            res = convert(*args)
        self.assertFalse(res.ok)
        self.assertIn(expected_text, res.message)
        for word in LEAK_WORDS:
            self.assertNotIn(word, res.message)
        self.assertIn(f"code={code}", logs.output[0])
        return logs.output[0]

    def test_empty_amount(self):
        self.check(("", "USD", "EUR"), "E_EMPTY", "enter an amount")

    def test_whitespace_amount(self):
        self.check(("   ", "USD", "EUR"), "E_EMPTY", "enter an amount")

    def test_empty_currency(self):
        self.check(("10", "", "EUR"), "E_EMPTY", "source currency")

    def test_very_long_amount(self):
        line = self.check(("9" * 100_000, "USD", "EUR"), "E_TOO_LONG", "too long")
        self.assertLess(len(line), 300)  # log stays bounded

    def test_very_long_currency(self):
        self.check(("10", "USD", "X" * 5000), "E_TOO_LONG", "target currency is too long")

    def test_unexpected_types_amount(self):
        for bad in (None, [1], {"a": 1}, (1,), True, object()):
            with self.subTest(bad=bad):
                self.check((bad, "USD", "EUR"), "E_TYPE", "must be a number")

    def test_unexpected_types_currency(self):
        for bad in (None, 5, ["USD"]):
            with self.subTest(bad=bad):
                self.check(("10", bad, "EUR"), "E_TYPE", "must be text")

    def test_not_a_number(self):
        self.check(("abc", "USD", "EUR"), "E_NOT_NUMBER", "doesn't look like a number")

    def test_nan_and_infinity(self):
        for bad in ("NaN", "Infinity", "-inf", float("nan"), float("inf")):
            with self.subTest(bad=bad):
                self.check((bad, "USD", "EUR"), "E_NOT_FINITE", "regular number")

    def test_negative(self):
        self.check(("-5", "USD", "EUR"), "E_NEGATIVE", "can't be negative")

    def test_too_large(self):
        self.check(("1e12", "USD", "EUR"), "E_TOO_LARGE", "too large")
        self.check((10**30, "USD", "EUR"), "E_TOO_LARGE", "too large")

    def test_unknown_currency_lists_supported(self):
        self.check(("10", "XYZ", "EUR"), "E_UNKNOWN_CURRENCY", "Supported: CAD, EUR")

    def test_unexpected_internal_error_is_hidden(self):
        original = converter.RATES_PER_USD
        converter.RATES_PER_USD = {"USD": Decimal("0"), "EUR": Decimal("1")}  # divide by zero
        try:
            with self.assertLogs("currency_converter", level="ERROR") as logs:
                res = convert("10", "USD", "EUR")
        finally:
            converter.RATES_PER_USD = original
        self.assertFalse(res.ok)
        self.assertEqual(res.message, "Something went wrong on our side. Please try again.")
        self.assertIn("E_INTERNAL", logs.output[0])
        self.assertIn("Traceback", logs.output[0])  # details only in log


class HappyPath(unittest.TestCase):
    def test_basic(self):
        res = convert("100", "usd", " eur ")
        self.assertTrue(res.ok)
        self.assertEqual(res.value, Decimal("92.00"))
        self.assertEqual(res.message, "100.00 USD = 92.00 EUR")

    def test_commas_and_numbers(self):
        self.assertEqual(convert("1,000.50", "USD", "USD").value, Decimal("1000.50"))
        self.assertTrue(convert(25, "GBP", "JPY").ok)
        self.assertTrue(convert(0, "USD", "EUR").ok)


if __name__ == "__main__":
    unittest.main()
