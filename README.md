# Offline Currency Converter

A tiny Python program that converts between currencies using a **fixed local rate table** (no network, no live service). It exists to show how to fail gracefully: every bad input gives the user a clear, fixable message, while the technical detail goes to a log file.

## Run it

```bash
python cli.py 100 usd eur      # 100.00 USD = 92.00 EUR
python cli.py abc usd eur      # Error: That doesn't look like a number...
```

Requires Python 3.8+ and nothing else. Logs are written to `converter.log`.

## Test it

```bash
python -m unittest discover -s tests -v
```

## Supported currencies

USD, EUR, GBP, JPY, CAD, NGN. Rates are illustrative and fixed in `converter.py`.

## Failure cases

| # | Bad input | Code | What the user sees | What is logged |
|---|-----------|------|--------------------|----------------|
| 1 | Empty or whitespace amount (`""`, `"   "`) | `E_EMPTY` | Please enter an amount, like 25 or 19.99. | `WARNING code=E_EMPTY field=amount input=str:'   '` |
| 2 | Empty currency (`""`) | `E_EMPTY` | Please enter a source/target currency code, like USD. | `WARNING code=E_EMPTY field=from input=str:''` |
| 3 | Very long amount (100,000 digits) | `E_TOO_LONG` | That amount is too long. Use at most 50 characters. | `WARNING code=E_TOO_LONG field=amount input=str:'999...'...(truncated, N chars)` (input cut to 40 chars) |
| 4 | Very long currency (5,000 chars) | `E_TOO_LONG` | That target currency is too long. Use a 3-letter code like USD. | Same shape, truncated |
| 5 | Unexpected type for amount (`None`, list, dict, tuple, `True`, object) | `E_TYPE` | The amount must be a number, like 25 or 19.99. | `WARNING code=E_TYPE field=amount input=list:'[1]'` |
| 6 | Unexpected type for currency (`None`, `5`, list) | `E_TYPE` | The source/target currency must be text, like USD. | `WARNING code=E_TYPE field=from input=int:'5'` |
| 7 | Not a number (`"abc"`) | `E_NOT_NUMBER` | That doesn't look like a number. Try something like 25 or 19.99. | `WARNING code=E_NOT_NUMBER field=amount input=str:'abc'` |
| 8 | `NaN`, `Infinity`, `-inf` | `E_NOT_FINITE` | Please enter a regular number, not infinity or NaN. | `WARNING code=E_NOT_FINITE ...` |
| 9 | Negative amount (`"-5"`) | `E_NEGATIVE` | The amount can't be negative. Enter 0 or more. | `WARNING code=E_NEGATIVE ...` |
| 10 | Huge amount (`"1e12"`, `10**30`) | `E_TOO_LARGE` | That amount is too large. The maximum is 1,000,000,000. | `WARNING code=E_TOO_LARGE ...` |
| 11 | Unknown currency (`"XYZ"`) | `E_UNKNOWN_CURRENCY` | We don't support that source/target currency. Supported: CAD, EUR, GBP, JPY, NGN, USD. | `WARNING code=E_UNKNOWN_CURRENCY field=to input=str:'XYZ'` |
| 12 | Anything unexpected (a bug, e.g. divide by zero) | `E_INTERNAL` | Something went wrong on our side. Please try again. | `ERROR code=E_INTERNAL unexpected failure` plus the full traceback |

## Design notes

- **No internals leak.** User messages never include exception names, tracebacks, file paths or raw input. Tests assert this.
- **Messages say how to fix it.** Each one gives an example or the allowed range/list.
- **Logs are bounded.** Input is cut to 40 characters before logging, so a huge input can't flood the log. Each entry has a stable `code` for searching.
- **`convert()` never raises.** All errors are caught and returned as a result object. A catch-all handles unforeseen bugs.
- **Length is checked before parsing**, so a giant string is never fed to the number parser.
- **Money uses `Decimal`**, not floats, with rounding to 2 places (half up).

## Files

- `converter.py` – conversion and validation logic
- `cli.py` – command-line interface
- `tests/test_converter.py` – tests covering every case above
