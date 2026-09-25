#!/usr/bin/env python3
"""Check (and optionally fix) Turkish case suffixes written after @sec- cross-references.

In the Turkish edition a reference such as `@sec-erisim'de` renders as
"Bölüm 19'da": the reader sees the *printed label*, not the anchor slug, so the
suffix has to harmonise with how the label is read aloud ("on dokuz" → -da).
Writers naturally harmonise with the slug instead, which is wrong most of the
time. This script computes every anchor's printed label from tr/_quarto.yml and
the heading structure, reads its last component aloud, and checks that the
suffix after the apostrophe agrees in vowel harmony, consonant hardening and
buffer consonants.

    python3 scripts/check-suffixes.py          # report, exit 1 on problems
    python3 scripts/check-suffixes.py --fix    # rewrite suffixes in place

Only the Turkish edition is checked; English needs no suffixes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TR = ROOT / "tr"

# ---------------------------------------------------------------- labels

def book_files():
    """Chapters and appendices in _quarto.yml order, as (path, kind)."""
    yml = (TR / "_quarto.yml").read_text(encoding="utf-8")
    chapters, appendices, in_app = [], [], False
    for line in yml.splitlines():
        if re.match(r"^\s*appendices:\s*$", line):
            in_app = True
            continue
        m = re.match(r"^\s*-\s+((?:chapters|appendices)/[\w.-]+\.qmd|[\w.-]+\.qmd)\s*$", line)
        if not m:
            continue
        (appendices if in_app else chapters).append(m.group(1))
    return chapters, appendices


def is_unnumbered(attrs):
    return bool(re.search(r"(^|\s)(\.unnumbered|-)(\s|$)", attrs or ""))


HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(?:\{([^}]*)\})?\s*$")


def headings(text):
    """Yield (level, title, attrs) for headings Quarto numbers or labels.

    Skips fenced code, and a heading that is the first thing inside a callout
    (Quarto turns it into the callout's title).
    """
    fence = None
    callout_title_pending = False
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^(`{3,}|~{3,})", s)
        if m:
            if fence is None:
                fence = m.group(1)
            elif s.startswith(fence) and s.strip("`~") == "":
                fence = None
            continue
        if fence:
            continue
        if re.match(r"^:{3,}\s*\{[^}]*\.callout", s):
            callout_title_pending = True
            continue
        if callout_title_pending:
            if s == "":
                continue
            callout_title_pending = False
            if s.startswith("#"):
                continue
        m = HEADING.match(line)
        if m:
            yield len(m.group(1)), m.group(2), m.group(3) or ""


def label_table():
    """anchor -> printed label ("19", "10.5", "E", "E.2") or None if unnumbered."""
    chapters, appendices = book_files()
    labels, files = {}, {}
    num = 0
    for rel in chapters:
        path = TR / rel
        text = path.read_text(encoding="utf-8")
        head = text.split("\n---", 2)[0] if text.startswith("---") else ""
        numbered_page = "number-sections: false" not in head
        first = True
        counters = []
        chap_label = None
        for level, title, attrs in headings(text):
            anchor = re.search(r"#(sec-[\w-]+)", attrs)
            if level == 1 and first:
                first = False
                if numbered_page and not is_unnumbered(attrs) and rel.startswith("chapters/"):
                    num += 1
                    chap_label = str(num)
                if anchor:
                    labels[anchor.group(1)] = chap_label
                    files[anchor.group(1)] = rel
                continue
            if chap_label is None or is_unnumbered(attrs):
                if anchor:
                    labels[anchor.group(1)] = None
                continue
            depth = level - 1
            while len(counters) < depth:
                counters.append(0)
            counters = counters[:depth]
            counters[-1] += 1
            if anchor:
                labels[anchor.group(1)] = chap_label + "." + ".".join(map(str, counters))
    for i, rel in enumerate(appendices):
        letter = "ABCDEFGHIJ"[i]
        text = (TR / rel).read_text(encoding="utf-8")
        first, counters = True, []
        for level, title, attrs in headings(text):
            anchor = re.search(r"#(sec-[\w-]+)", attrs)
            if level == 1 and first:
                first = False
                if anchor:
                    labels[anchor.group(1)] = letter
                continue
            if is_unnumbered(attrs):
                if anchor:
                    labels[anchor.group(1)] = None
                continue
            depth = level - 1
            while len(counters) < depth:
                counters.append(0)
            counters = counters[:depth]
            counters[-1] += 1
            if anchor:
                labels[anchor.group(1)] = letter + "." + ".".join(map(str, counters))
    return labels

# ---------------------------------------------------------------- reading

ONES = ["sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
TENS = {1: "on", 2: "yirmi", 3: "otuz", 4: "kırk", 5: "elli",
        6: "altmış", 7: "yetmiş", 8: "seksen", 9: "doksan"}
LETTERS = {"A": "a", "B": "be", "C": "ce", "D": "de", "E": "e", "F": "fe",
           "G": "ge", "H": "he", "I": "ı", "J": "je"}


def last_word(label):
    comp = label.split(".")[-1]
    if comp in LETTERS:
        return LETTERS[comp]
    n = int(comp)
    if n == 0:
        return "sıfır"
    if n % 100 == 0:
        return "yüz"
    if n % 10:
        return ONES[n % 10]
    return TENS[(n // 10) % 10]

# ---------------------------------------------------------------- harmony

VOWELS = "aeıioöuüâîû"
BACK = set("aıouâû")
ROUND = set("oöuü")
HARD = set("fstkçşhp")


def last_vowel(word):
    for ch in reversed(word):
        if ch in VOWELS:
            return {"â": "a", "î": "i", "û": "u"}.get(ch, ch)
    return "e"


def v2(v):
    return "a" if v in BACK else "e"


def v4(v):
    if v in BACK:
        return "u" if v in ROUND else "ı"
    return "ü" if v in ROUND else "i"


def harmonise(word, suffix):
    """Return the suffix rewritten for `word`, or None if not recognised."""
    vowel_final = word[-1] in VOWELS
    hard = word[-1] in HARD
    v = last_vowel(word)
    D = "t" if hard else "d"

    m = re.fullmatch(r"n?[ıiuü]n(.*)", suffix)                   # genitive
    if m:
        core = ("n" if vowel_final else "") + v4(v) + "n"
        return core + (harmonise_after(core, m.group(1)) if m.group(1) else "")
    m = re.fullmatch(r"n?[dt]([ae])(n|ki.*)?", suffix)            # loc / abl / -DAki
    if m:
        core = D + v2(v)
        rest = m.group(2) or ""
        return core + rest
    m = re.fullmatch(r"[dt][ıiuü]r", suffix)                      # copula -DIr
    if m:
        return D + v4(v) + "r"
    m = re.fullmatch(r"y?l[ae]", suffix)                          # instrumental
    if m:
        return ("y" if vowel_final else "") + "l" + v2(v)
    m = re.fullmatch(r"[yn]?[ıiuü]", suffix)                      # accusative
    if m:
        return ("y" if vowel_final else "") + v4(v)
    m = re.fullmatch(r"[yn]?[ae]", suffix)                        # dative
    if m:
        return ("y" if vowel_final else "") + v2(v)
    m = re.fullmatch(r"l[ae]r(.*)", suffix)                       # plural (+rest)
    if m:
        core = "l" + v2(v) + "r"
        return core + (harmonise_after(core, m.group(1)) if m.group(1) else "")
    return None


def harmonise_after(core, rest):
    """Harmonise the tail of a suffix chain to the syllable before it."""
    if rest.startswith("ki"):
        return rest
    out = harmonise(core, rest)
    return out if out is not None else rest

# ---------------------------------------------------------------- scan

REF = re.compile(r"(@sec-[\w-]*\w)'([a-zçğıöşüâîû]+)")


def prose_spans(text):
    """Yield (start, end) offsets of text outside fenced code blocks."""
    pos, fence, start = 0, None, 0
    for line in text.splitlines(keepends=True):
        s = line.strip()
        m = re.match(r"^(`{3,}|~{3,})", s)
        if m:
            if fence is None:
                yield start, pos
                fence = m.group(1)
            elif s.startswith(fence) and s.strip("`~") == "":
                fence = None
                start = pos + len(line)
        pos += len(line)
    if fence is None:
        yield start, pos


def main():
    fix = "--fix" in sys.argv
    labels = label_table()
    targets = sorted((TR / "chapters").glob("*.qmd")) + sorted((TR / "appendices").glob("*.qmd")) \
        + [TR / n for n in ("index.qmd", "preface.qmd", "cite.qmd", "references.qmd") if (TR / n).exists()]
    problems = unknown = 0
    for path in targets:
        text = path.read_text(encoding="utf-8")
        edits = []
        for a, b in prose_spans(text):
            for m in REF.finditer(text, a, b):
                anchor = m.group(1)[1:]
                suffix = m.group(2)
                label = labels.get(anchor, "missing")
                if label == "missing":
                    continue  # check-links reports dead refs
                if label is None:
                    unknown += 1
                    print(f"{path.relative_to(ROOT)}: @{anchor}'{suffix} — target is unnumbered; check by hand")
                    continue
                want = harmonise(last_word(label), suffix)
                if want is None:
                    unknown += 1
                    print(f"{path.relative_to(ROOT)}: @{anchor}'{suffix} — unrecognised suffix (label {label})")
                    continue
                if want != suffix:
                    problems += 1
                    line = text.count("\n", 0, m.start()) + 1
                    print(f"{path.relative_to(ROOT)}:{line}: @{anchor}'{suffix} → '{want}  (prints {label})")
                    edits.append((m.start(2), m.end(2), want))
        if fix and edits:
            for s, e, w in reversed(edits):
                text = text[:s] + w + text[e:]
            path.write_text(text, encoding="utf-8")
    verb = "fixed" if fix else "found"
    print(f"check-suffixes: {problems} suffix(es) {verb}; {unknown} to check by hand.")
    return 1 if problems and not fix else 0


if __name__ == "__main__":
    sys.exit(main())
