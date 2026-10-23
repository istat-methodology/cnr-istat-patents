#!/usr/bin/env python3
"""
build_ipc_titles.py
===================

Turn the official WIPO IPC scheme (XML master file) into one flat CSV that
maps every IPC symbol to its English title.

Why this script exists
----------------------
Our patent files only contain IPC *codes* (e.g. ``G06N3/08``).  To read the
results of an analysis we also need to know what a code *means*
(``G06N`` = "Computing arrangements based on specific computational models").
WIPO distributes the titles as a deeply nested XML file; this script flattens
it so that notebooks can simply read a CSV.

Input
-----
``ipc/EN_ipc_scheme_20260101.xml``
    English IPC scheme, edition 2026.01.
    Downloaded from the WIPO "IPC master files" folder (``ipc_scheme_20260101.zip``):
    https://www.wipo.int/classifications/data/ipc/ITSupport_and_download_area/20260101/MasterFiles/

Output
------
``ipc/ipc_titles.csv`` with one row per IPC symbol and these columns:

=============  ==============================================================
column         meaning
=============  ==============================================================
symbol         IPC symbol in the same format as the patent data
               (``A``, ``A01``, ``A01B``, ``G06N3/00``, ``G01N33/48``)
level          ``section`` | ``class`` | ``subclass`` | ``main_group`` | ``subgroup``
title          Title as published by WIPO (sections, classes and subclasses
               are in capital letters; several title parts are joined by "; ")
short_title    Readable short version: first title part only, in sentence case
               when the published title is mostly in capitals (used for plot labels)
full_title     Only for main groups and subgroups: the chain of titles from
               the main group down to the symbol, joined by " > ".  Subgroup
               titles are often fragments ("of liquid biological material"),
               so they only make sense together with their parents.
depth          0 for sections ... 5 for subclasses/main groups; for subgroups,
               the number of dots in the IPC scheme (1 = "-", 2 = "--", ...)
parent         Symbol of the parent entry (same format as ``symbol``)
source         ``scheme_2026.01`` or ``hardcoded`` (see below)
=============  ==============================================================

Known gap: H01L
---------------
IPC 2026.01 no longer contains subclass ``H01L``: its content was moved to
``H10`` in 2023.  The WIPO technology concordance (March 2026) and the patent
data still use ``H01L`` (field 8, Semiconductors).  We therefore add ONE
hardcoded row for the subclass ``H01L``, marked ``source = hardcoded``.
Titles of ``H01L`` groups (e.g. ``H01L21/52``) are NOT available.

Symbol format
-------------
The XML stores symbols as 14 characters: ``G01N0033480000``
= subclass ``G01N`` + main group ``0033`` + subgroup ``480000``.
We convert it to ``G01N33/48``: leading zeros of the main group are dropped,
trailing zeros of the subgroup are dropped (but at least 2 digits are kept,
so ``A01B0001000000`` becomes ``A01B1/00``).

Usage
-----
    python src/build_ipc_titles.py
    python src/build_ipc_titles.py --xml ipc/EN_ipc_scheme_20260101.xml --out ipc/ipc_titles.csv

Only the Python standard library is needed.
"""

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.wipo.int/classifications/ipc/masterfiles}"

# <ipcEntry kind="..."> values we keep. Digits "1".."9" are subgroups (number of dots).
KIND_TO_LEVEL = {"s": "section", "c": "class", "u": "subclass", "m": "main_group"}

# Symbols missing from the 2026.01 scheme but still used in the patent data.
HARDCODED = [
    {
        "symbol": "H01L",
        "level": "subclass",
        "title": "SEMICONDUCTOR DEVICES NOT OTHERWISE PROVIDED FOR",
        "short_title": "Semiconductor devices not otherwise provided for",
        "full_title": "",
        "depth": 5,
        "parent": "H01",
        "source": "hardcoded",
    }
]

COLUMNS = ["symbol", "level", "title", "short_title", "full_title", "depth", "parent", "source"]

LONG_SYMBOL = re.compile(r"^([A-H]\d\d[A-Z])(\d{4})(\d{6})$")


def format_symbol(raw: str) -> str:
    """Convert a 14-character XML symbol to the format used in the patent data.

    ``G01N0033480000`` -> ``G01N33/48``;  ``A01B`` and ``A01`` stay unchanged.
    """
    m = LONG_SYMBOL.match(raw)
    if not m:
        return raw
    subclass, main, sub = m.groups()
    sub = sub.rstrip("0").ljust(2, "0")
    return f"{subclass}{int(main)}/{sub}"


def text_of(text_el) -> str:
    """Text of a <text> element, rendering <mref> cross references readably.

    ``groups <mref ref="G01N0001000000" endRef="G01N0031000000"/>``
    becomes ``groups G01N1/00 - G01N31/00``.
    """
    parts = [text_el.text or ""]
    for child in text_el:
        if child.tag == NS + "mref":
            start = format_symbol(child.get("ref", ""))
            end = child.get("endRef")
            parts.append(f"{start} - {format_symbol(end)}" if end else start)
        else:  # any other inline tag: keep its text
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def title_parts(entry) -> list:
    """List of title parts of an <ipcEntry> (notes and 'entryReference' are ignored)."""
    body = entry.find(NS + "textBody")
    title = body.find(NS + "title") if body is not None else None
    if title is None:
        return []
    out = []
    for part in title.findall(NS + "titlePart"):
        t = part.find(NS + "text")
        if t is not None:
            out.append(text_of(t))
    return [p for p in out if p]


def short_title(parts: list) -> str:
    """First title part, in sentence case when it is mostly written in capitals.

    Sections, classes and subclasses are published in capitals ("COMPUTING ARRANGEMENTS BASED ON ...");
    some mix capitals and lower case ("TRANSMISSION OF DIGITAL INFORMATION, e.g. TELEGRAPHIC ...").
    If more than 60% of the letters are capitals we convert to lower case and capitalise the first letter.
    Acronyms inside such titles are lowered too (a known, minor limitation).
    """
    if not parts:
        return ""
    first = parts[0].rstrip(" ,;")
    letters = [ch for ch in first if ch.isalpha()]
    if letters and sum(ch.isupper() for ch in letters) / len(letters) > 0.6:
        first = first.lower()
        first = first[:1].upper() + first[1:]
    return first


def walk(entry, parent_symbol, ancestors, rows):
    """Depth-first walk over nested <ipcEntry> elements.

    parent_symbol : symbol of the closest kept ancestor
    ancestors     : titles from the current main group down to the parent
                    (used to build ``full_title`` for subgroups)
    """
    kind = entry.get("kind")
    is_subgroup = bool(kind) and kind.isdigit()
    keep = kind in KIND_TO_LEVEL or is_subgroup

    if keep:
        symbol = format_symbol(entry.get("symbol"))
        parts = title_parts(entry)
        title = "; ".join(parts)
        level = KIND_TO_LEVEL.get(kind, "subgroup")
        depth = int(kind) if is_subgroup else {"s": 0, "c": 2, "u": 4, "m": 5}[kind]

        if level == "main_group":
            chain = [title]
        elif level == "subgroup":
            chain = ancestors + [title]
        else:
            chain = []

        rows.append(
            {
                "symbol": symbol,
                "level": level,
                "title": title,
                "short_title": short_title(parts),
                "full_title": " > ".join(chain) if chain else "",
                "depth": depth,
                "parent": parent_symbol or "",
                "source": "scheme_2026.01",
            }
        )
        next_parent, next_anc = symbol, chain
    else:
        next_parent, next_anc = parent_symbol, ancestors

    for child in entry.findall(NS + "ipcEntry"):
        walk(child, next_parent, next_anc, rows)


def build(xml_path: Path) -> list:
    root = ET.parse(xml_path).getroot()
    rows = []
    for top in root.findall(NS + "ipcEntry"):
        walk(top, None, [], rows)

    # A symbol can appear twice if WIPO lists it under several editions: keep the first.
    seen, unique = set(), []
    for r in rows:
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            unique.append(r)

    for extra in HARDCODED:
        if extra["symbol"] not in seen:
            unique.append(dict(extra))
    return unique


def main(argv=None):
    here = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Flatten the WIPO IPC scheme XML into a CSV of titles.")
    ap.add_argument("--xml", type=Path, default=here / "ipc" / "EN_ipc_scheme_20260101.xml")
    ap.add_argument("--out", type=Path, default=here / "ipc" / "ipc_titles.csv")
    args = ap.parse_args(argv)

    if not args.xml.exists():
        sys.exit(f"XML file not found: {args.xml}")

    rows = build(args.xml)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["level"]] = counts.get(r["level"], 0) + 1
    print(f"Wrote {len(rows)} rows to {args.out}")
    for level in ["section", "class", "subclass", "main_group", "subgroup"]:
        print(f"  {level:<11} {counts.get(level, 0)}")


if __name__ == "__main__":
    main()
