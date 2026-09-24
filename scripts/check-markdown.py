#!/usr/bin/env python3
"""Catch lines pandoc reads as a list marker when prose was meant.

Reflowing a paragraph can push a token that *looks* like a list marker to
the start of a line, and pandoc then starts a list there. Nothing fails.
The page builds, the sentence is silently cut in two, and the marker
itself disappears from the text:

    5. **Measure distraction.** Hold retrieval fixed and vary only *k* from 1 to
       20. Plot accuracy. Find the point where adding context starts to cost you

renders as "...vary only k from 1 to" followed by an ordered list that
starts at 20. The reader sees a stray numbered item and never sees the
"20". The same happened to a Roman numeral at the start of a paragraph
(`VI. kısmın ...` became a `type="I"` list starting at 6) and to a
cross-reference in parentheses (`(@sec-...)` is pandoc's example-list
syntax, so the reference vanished and the sentence broke).

Two positions are dangerous, and only two:

  1. An indented continuation line inside a list item. Any marker shape
     starts a nested list there — digits, letters, Roman numerals, or
     `(@label)`.
  2. The first line of a paragraph, when the marker is a letter or a
     Roman numeral. The book never writes lists that way, so a match is
     always prose; digits are excluded here because a digit at the start
     of a block is how a real ordered list begins.

A plain mid-paragraph line at column zero is safe — pandoc does not
interrupt a paragraph there — so it is not reported. Fix a hit by
reflowing the line so the marker is not first, not by rewording.

    python3 scripts/check-markdown.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDITIONS = ("en", "tr")

FENCE_RE = re.compile(r"\s*(`{3,}|~{3,})")

# Inside a list item, every marker shape opens a nested list.
CONTINUATION_RE = re.compile(
    r"^\s{1,3}(?:\(@[^)\s]*\)|(?:\d{1,9}|[IVXLCivxlc]{1,7}|[A-Za-z])[.)])(\s|$)"
)

# At the start of a paragraph, only the shapes the book never uses as real
# list markers: a letter or a Roman numeral.
BLOCK_START_RE = re.compile(r"^\s{0,3}(?:[IVXLC]{1,7}|[A-Za-z])[.)]\s")


def offenders(text):
    """Yield (line number, what pandoc will do) for one file's source."""
    lines = text.split("\n")
    fence = None
    for i, line in enumerate(lines):
        marker = FENCE_RE.match(line)
        if fence is None:
            if marker:
                fence = marker.group(1)[0] * len(marker.group(1))
                continue
        else:
            if marker and marker.group(1).startswith(fence):
                fence = None
            continue

        if i == 0 or not lines[i - 1].strip():
            if BLOCK_START_RE.match(line):
                yield i + 1, "starts a list where a paragraph was meant"
        elif CONTINUATION_RE.match(line):
            yield i + 1, "opens a nested list inside the list item above"


def qmd_files(edition):
    base = ROOT / edition
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.qmd") if "_book" not in p.parts)


def main():
    problems = []
    for edition in EDITIONS:
        for path in qmd_files(edition):
            rel = path.relative_to(ROOT)
            text = path.read_text(encoding="utf-8")
            for num, effect in offenders(text):
                line = text.split("\n")[num - 1].strip()
                problems.append(f"{rel}:{num}: {effect} — {line[:60]}")

    if problems:
        print(f"check-markdown: {len(problems)} problem(s)\n", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print("\n  reflow the line so the marker is not first.", file=sys.stderr)
        return 1

    print("check-markdown: no line starts with an accidental list marker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
