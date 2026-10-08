"""Offline currency converter using a fixed local rate table.

Every failure becomes a ConversionResult with a friendly message for the user.
Technical details go to the log only, never to the user.
"""
import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Optional

log = logging.getLogger("currency_converter")

# Fixed table: units of each currency per 1 USD. Not live data.
RATES_PER_USD = {
    "USD": Decimal("1"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "JPY": Decimal("149.50"),
    "CAD": Decimal("1.36"),
    "NGN": Decimal("1550"),
}
MAX_INPUT_LENGTH = 50
MAX_CODE_LENGTH = 10
MAX_AMOUNT = Decimal("1000000000")


class InputError(Exception):
    """A problem with user input. `user_message` is safe to show."""

    def __init__(self, code: str, user_message: str, field: str, raw: Any):
        super().__init__(code)
        self.code = code
        self.user_message = user_message
        self.field = field
        self.raw = raw


@dataclass
class ConversionResult:
    ok: bool
    message: str
    value: Optional[Decimal] = None


def _safe_repr(raw: Any, limit: int = 40) -> str:
    """Short, bounded description of an input for the log."""
    try:
        text = repr(raw)
    except Exception:
        text = "<unrepresentable>"
    if len(text) > limit:
        text = f"{text[:limit]}...(truncated, {len(text)} chars)"
    return f"{type(raw).__name__}:{text}"


def parse_amount(raw: Any) -> Decimal:
    field = "amount"
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float, Decimal)):
        raise InputError("E_TYPE", "The amount must be a number, like 25 or 19.99.", field, raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise InputError("E_EMPTY", "Please enter an amount, like 25 or 19.99.", field, raw)
        if len(text) > MAX_INPUT_LENGTH:
            raise InputError("E_TOO_LONG", f"That amount is too long. Use at most {MAX_INPUT_LENGTH} characters.", field, raw)
        text = text.replace(",", "")
    else:
        text = str(raw) if not isinstance(raw, int) else None
    try:
        amount = Decimal(raw if text is None else text)
    except (InvalidOperation, ValueError):
        raise InputError("E_NOT_NUMBER", "That doesn't look like a number. Try something like 25 or 19.99.", field, raw)
    if not amount.is_finite():
        raise InputError("E_NOT_FINITE", "Please enter a regular number, not infinity or NaN.", field, raw)
    if amount < 0:
        raise InputError("E_NEGATIVE", "The amount can't be negative. Enter 0 or more.", field, raw)
    if amount > MAX_AMOUNT:
        raise InputError("E_TOO_LARGE", f"That amount is too large. The maximum is {MAX_AMOUNT:,}.", field, raw)
    return amount


def parse_currency(raw: Any, field: str) -> str:
    label = "source" if field == "from" else "target"
    if not isinstance(raw, str):
        raise InputError("E_TYPE", f"The {label} currency must be text, like USD.", field, raw)
    code = raw.strip().upper()
    if not code:
        raise InputError("E_EMPTY", f"Please enter a {label} currency code, like USD.", field, raw)
    if len(code) > MAX_CODE_LENGTH:
        raise InputError("E_TOO_LONG", f"That {label} currency is too long. Use a 3-letter code like USD.", field, raw)
    if code not in RATES_PER_USD:
        supported = ", ".join(sorted(RATES_PER_USD))
        raise InputError("E_UNKNOWN_CURRENCY", f"We don't support that {label} currency. Supported: {supported}.", field, raw)
    return code


def convert(amount: Any, source: Any, target: Any) -> ConversionResult:
    """Convert amount from source to target. Never raises."""
    try:
        value = parse_amount(amount)
        src = parse_currency(source, "from")
        dst = parse_currency(target, "to")
        result = (value / RATES_PER_USD[src] * RATES_PER_USD[dst]).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return ConversionResult(True, f"{value:,.2f} {src} = {result:,.2f} {dst}", result)
    except InputError as err:
        log.warning("code=%s field=%s input=%s", err.code, err.field, _safe_repr(err.raw))
        return ConversionResult(False, err.user_message)
    except Exception:
        log.exception("code=E_INTERNAL unexpected failure")
        return ConversionResult(False, "Something went wrong on our side. Please try again.")
