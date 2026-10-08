"""Usage: python cli.py AMOUNT FROM TO   e.g. python cli.py 100 usd eur"""
import argparse
import logging
import sys

from converter import convert


def main(argv=None) -> int:
    logging.basicConfig(
        filename="converter.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Offline currency converter (fixed rates).")
    parser.add_argument("amount", nargs="?", default="")
    parser.add_argument("source", nargs="?", default="")
    parser.add_argument("target", nargs="?", default="")
    args = parser.parse_args(argv)
    result = convert(args.amount, args.source, args.target)
    print(result.message if result.ok else f"Error: {result.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
