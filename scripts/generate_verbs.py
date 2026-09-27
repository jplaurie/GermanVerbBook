#!/usr/bin/env python3
"""Validate verbs/verbs.yaml and generate the LaTeX verb catalogue."""

from __future__ import annotations

import argparse
import sys

from verb_data import OUTPUT_FILE, ValidationError, iter_verbs, load_document, render_document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the generated LaTeX is missing or stale",
    )
    args = parser.parse_args()

    try:
        document = load_document()
        expected = render_document(document)
    except (OSError, ValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    count = sum(1 for _ in iter_verbs(document))
    if args.check:
        if not OUTPUT_FILE.exists() or OUTPUT_FILE.read_text(encoding="utf-8") != expected:
            print(f"error: stale generated file: {OUTPUT_FILE}", file=sys.stderr)
            return 1
        print(f"validated {count} verbs; generated LaTeX is current")
        return 0

    OUTPUT_FILE.write_text(expected, encoding="utf-8")
    print(f"generated {OUTPUT_FILE} from {count} validated verbs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
