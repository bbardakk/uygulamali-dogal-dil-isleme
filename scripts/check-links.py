#!/usr/bin/env python3
"""Validate cross-references, citations and hard-coded chapter links.

Quarto is silent about four failure modes that this book is exposed to,
because chapters get renumbered as the outline changes:

  1. A hard-coded "14-prompting.html" href inside an OJS/HTML block. Quarto
     never resolves these, so a renamed chapter leaves a dead link that only
     a reader discovers.
  2. An @sec- cross-reference to an anchor nobody defines.
  3. An @citation key that is not in references.bib.
  4. An @sec- cross-reference *inside* a fenced block — a code comment, a
     ```text listing, an SVG label. The anchor exists, so check (2) passes,
     but Quarto does not resolve references inside code and the reader is
     shown the raw "@sec-bake-off" marker. Write the chapter or section out
     in prose there instead.

    python3 scripts/check-links.py          # report problems, exit 1 if any
    python3 scripts/check-links.py --strict # also fail on uncited bib entries
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDITIONS = ("en", "tr")

# Quarto reserves these prefixes for its own crossref machinery; everything
# else after an "@" is a bibliography key.
CROSSREF_PREFIXES = ("sec-", "fig-", "tbl-", "eq-", "lst-", "thm-", "exm-")

# Pandoc citation keys: start with a letter, then alphanumerics and internal
# punctuation. Kept deliberately greedy on digits so "goldberg2014word2vec"
# is captured whole rather than truncated at the year.
CITE_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_:.#$%&\-+?<>~/]*[A-Za-z0-9])")
ANCHOR_RE = re.compile(r"\{#((?:sec|fig|tbl|eq)-[A-Za-z0-9_-]+)[^}]*\}")
HREF_RE = re.compile(r"""(?:href\s*[:=]\s*|\]\()\s*["']?([0-9A-Za-z][^"'\s)]*\.html)""")
BIBKEY_RE = re.compile(r"^@\w+\{([^,]+),", re.MULTILINE)


def strip_code(text):
    """Blank out fenced blocks and inline code, preserving line numbering.

    Citations and anchors inside code are not references, and OJS blocks are
    full of "@" in other roles. Lines become empty rather than disappearing so
    that reported line numbers still match the file.
    """
    out, fence = [], None
    for line in text.split("\n"):
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = marker.group(1)[0] * len(marker.group(1))
            out.append("")
            continue
        if fence is not None:
            if marker and marker.group(1).startswith(fence):
                fence = None
            out.append("")
            continue
        out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def crossrefs_in_code(text):
    """Yield (line number, key) for crossrefs inside fenced blocks.

    The inverse of strip_code: everything it blanks out is what this looks
    at. Inline code spans are left alone — the only ones in this book are
    table cells whose backticks belong to a neighbouring column.
    """
    fence = None
    for num, line in enumerate(text.split("\n"), 1):
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if fence is None:
            if marker:
                fence = marker.group(1)[0] * len(marker.group(1))
            continue
        if marker and marker.group(1).startswith(fence):
            fence = None
            continue
        for key in CITE_RE.findall(line):
            if key.startswith(CROSSREF_PREFIXES):
                yield num, key


def qmd_files(edition):
    base = ROOT / edition
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.qmd") if "_book" not in p.parts)


def bib_keys():
    keys = set()
    for edition in EDITIONS:
        bib = ROOT / edition / "references.bib"
        if bib.exists():
            keys |= set(BIBKEY_RE.findall(bib.read_text(encoding="utf-8")))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="also fail when references.bib has uncited entries")
    args = ap.parse_args()

    problems, cited, known_bib = [], set(), bib_keys()

    for edition in EDITIONS:
        files = qmd_files(edition)
        if not files:
            continue

        anchors = set()
        for path in files:
            anchors |= set(ANCHOR_RE.findall(path.read_text(encoding="utf-8")))

        for path in files:
            rel = path.relative_to(ROOT)
            body = strip_code(path.read_text(encoding="utf-8"))
            raw = path.read_text(encoding="utf-8")

            for num, line in enumerate(body.split("\n"), 1):
                for key in CITE_RE.findall(line):
                    if key.startswith(CROSSREF_PREFIXES):
                        if key.startswith("sec-") and key not in anchors:
                            problems.append(
                                f"{rel}:{num}: @{key} — no such section anchor")
                        continue
                    cited.add(key)
                    if key not in known_bib:
                        problems.append(
                            f"{rel}:{num}: @{key} — not in references.bib")

            for num, key in crossrefs_in_code(raw):
                problems.append(
                    f"{rel}:{num}: @{key} inside a fenced block — Quarto "
                    f"leaves it unresolved; write it out in prose")

            # Hard-coded .html links are checked against the raw text, since
            # the ones this book actually has live inside OJS blocks.
            for num, line in enumerate(raw.split("\n"), 1):
                for href in HREF_RE.findall(line):
                    if "://" in href or href.startswith("#"):
                        continue
                    target = (path.parent / href).with_suffix(".qmd")
                    if not target.exists():
                        problems.append(
                            f"{rel}:{num}: href '{href}' — no matching "
                            f"{target.relative_to(ROOT)}")

    uncited = sorted(known_bib - cited)
    if uncited and args.strict:
        for key in uncited:
            problems.append(f"references.bib: {key} — defined but never cited")
    elif uncited:
        print(f"note: {len(uncited)} uncited bib entries "
              f"(run with --strict to treat as errors)", file=sys.stderr)

    if problems:
        print(f"check-links: {len(problems)} problem(s)\n", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print("check-links: all cross-references, citations and chapter links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
