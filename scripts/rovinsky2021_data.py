#!/usr/bin/env python3
"""Fetch the cranial landmark data of Rovinsky et al. (2021) and build the files the paper's scripts read.

The Modan2 paper demonstrates and assesses the software on the published data of

    Rovinsky, D. S., Evans, A. R., & Adams, J. W. (2021). Functional ecological
    convergence between the thylacine and small prey-focused canids. BMC Ecology
    and Evolution, 21, 58.

deposited on figshare under CC BY 4.0:

    Rovinsky, D. S., Evans, A. R., & Adams, J. W. (2021). Data and Code for
    Rovinsky et al., 2021 (Version 1). figshare.
    https://doi.org/10.6084/m9.figshare.14330759.v1

The data are not redistributed with Modan2. This script downloads the three files
it needs from that deposit, checks each against the MD5 checksum figshare
publishes for it, and writes two Morphologika files into the directory given
(default ``benchmarks/data/rovinsky2021``, which git ignores):

  neurocranium_222.txt
      ``Thylacine2021_NeuroGM.txt`` -- 222 specimens x 72 landmarks on the
      neurocranial surface patch -- with each specimen's classification from the
      ``Classifier_Total`` sheet of ``REA_2021_dataforR.xlsx`` attached as
      variables: Clade, Family, Genus, Species, DietFine (FeedCatgFine),
      DietCoarse (FeedCatgCoarse), and PreyCatg. The 16 thylacines are ``NA`` in
      the last three, as in the source.
  skull_thylacines_16.txt
      ``Thylacine2021_SkullGM.txt`` -- the whole-cranium scheme of 381 landmarks --
      restricted to its 16 thylacine specimens.

Coordinates, specimen names, and their order are copied unchanged; only the
section headers lose the trailing tabs of the source files. The workbook is read
with the standard library, since the analysis environment has no Excel reader.

Usage:
    python scripts/rovinsky2021_data.py
    python scripts/rovinsky2021_data.py --dest /some/other/directory
"""

import argparse
import hashlib
import sys
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
DEFAULT_DEST = HERE.parent / "benchmarks" / "data" / "rovinsky2021"

ARTICLE = "https://doi.org/10.6084/m9.figshare.14330759.v1"
DOWNLOAD = "https://ndownloader.figshare.com/files/{}"
# name -> (figshare file id, MD5 that figshare publishes for it)
SOURCES = {
    "Thylacine2021_NeuroGM.txt": (27332414, "67874394da3d73a3edce0c8e3c80429c"),
    "Thylacine2021_SkullGM.txt": (27332417, "03d9bed716968f391f4bfae07c7202c8"),
    "REA_2021_dataforR.xlsx": (27332429, "9c909ef6fa0908886f95c5bdf73de648"),
}
CLASSIFIER_SHEET = "Classifier_Total"
VARIABLES = {  # variable in the built file -> column of Classifier_Total
    "Clade": "Clade",
    "Family": "Family",
    "Genus": "Genus",
    "Species": "Species",
    "DietFine": "FeedCatgFine",
    "DietCoarse": "FeedCatgCoarse",
    "PreyCatg": "PreyCatg",
}
NEUROCRANIUM = "neurocranium_222.txt"
SKULL_THYLACINES = "skull_thylacines_16.txt"


def md5(path):
    digest = hashlib.md5()  # noqa: S324 -- matching figshare's published checksum, not security
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(dest):
    """Download each source file unless a copy with the right checksum is already there."""
    dest.mkdir(parents=True, exist_ok=True)
    for name, (file_id, expected) in SOURCES.items():
        path = dest / name
        if path.exists() and md5(path) == expected:
            print(f"  {name}: present, checksum ok")
            continue
        url = DOWNLOAD.format(file_id)
        with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 -- fixed https URL
            path.write_bytes(response.read())
        got = md5(path)
        if got != expected:
            path.unlink()
            raise RuntimeError(f"{name}: checksum {got} does not match figshare's {expected}")
        print(f"  {name}: downloaded, checksum ok")


def read_morphologika(path):
    """Sections of a Morphologika file as {name: [lines]}, trailing whitespace removed."""
    sections, current = {}, None
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].lower()
            sections[current] = []
        elif current is not None and line:
            sections[current].append(line)
    return sections


def specimens(sections):
    """Names and per-specimen coordinate rows from [names] and [rawpoints]."""
    names = sections["names"]
    rows, current = {}, None
    for line in sections["rawpoints"]:
        if line.startswith("'"):
            current = line[1:].strip()
            rows[current] = []
        else:
            rows[current].append(line)
    if list(rows) != names:
        raise ValueError("[rawpoints] does not list the specimens of [names] in the same order")
    return names, rows


def _parse_xml(data):
    # The workbook is read only after fetch() has matched it against figshare's
    # published checksum, so its content is fixed and known.
    return ElementTree.fromstring(data)  # noqa: S314


def read_sheet(path, sheet_name):
    """Rows of one worksheet of an .xlsx file, as lists of strings."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(path) as book:
        shared = [
            "".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t"))
            for si in _parse_xml(book.read("xl/sharedStrings.xml")).findall("m:si", ns)
        ]
        workbook = _parse_xml(book.read("xl/workbook.xml"))
        rels = _parse_xml(book.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels}
        sheet = next(s for s in workbook.iter(f"{{{ns['m']}}}sheet") if s.get("name") == sheet_name)
        target = targets[sheet.get(rel_ns)].lstrip("/")
        xml = book.read(target if target.startswith("xl/") else f"xl/{target}")

    def value(cell):
        v = cell.find("m:v", ns)
        if v is None:
            return ""
        return shared[int(v.text)] if cell.get("t") == "s" else v.text

    return [[value(c) for c in row.findall("m:c", ns)] for row in _parse_xml(xml).iter(f"{{{ns['m']}}}row")]


def write_morphologika(path, sections, names, rows, labels=None, values=None):
    out = ["[individuals]", str(len(names)), "[landmarks]", sections["landmarks"][0]]
    out += ["[dimensions]", sections["dimensions"][0], "[names]", *names]
    if labels:
        out += ["[labels]", "\t".join(labels), "[labelvalues]", *("\t".join(v) for v in values)]
    out.append("[rawpoints]")
    for name in names:
        out += [f"'{name}", *rows[name]]
    if sections.get("wireframe"):
        out += ["[wireframe]", *(" ".join(line.split()) for line in sections["wireframe"])]
    path.write_text("\n".join(out) + "\n")


def build(dest):
    table = read_sheet(dest / "REA_2021_dataforR.xlsx", CLASSIFIER_SHEET)
    header, body = table[0], table[1:]
    by_specimen = {row[header.index("Specimen")]: row for row in body}

    neuro = read_morphologika(dest / "Thylacine2021_NeuroGM.txt")
    names, rows = specimens(neuro)
    if set(names) != set(by_specimen):
        raise ValueError(f"{CLASSIFIER_SHEET} does not classify exactly the specimens of the NeuroGM file")
    values = [[by_specimen[n][header.index(col)] for col in VARIABLES.values()] for n in names]
    write_morphologika(dest / NEUROCRANIUM, neuro, names, rows, list(VARIABLES), values)
    print(f"  {NEUROCRANIUM}: {len(names)} specimens, variables {', '.join(VARIABLES)}")

    skull = read_morphologika(dest / "Thylacine2021_SkullGM.txt")
    names, rows = specimens(skull)
    thylacines = [n for n in names if by_specimen[n][header.index("IsThylacine")] == "Yes"]
    write_morphologika(dest / SKULL_THYLACINES, skull, thylacines, rows)
    print(f"  {SKULL_THYLACINES}: {len(thylacines)} thylacine specimens")


def main():
    ap = argparse.ArgumentParser(description="Fetch and prepare the Rovinsky et al. (2021) cranial data.")
    ap.add_argument("--dest", default=str(DEFAULT_DEST), help=f"directory to work in (default: {DEFAULT_DEST})")
    args = ap.parse_args()
    dest = Path(args.dest)
    print(f"# Rovinsky et al. (2021), {ARTICLE}, CC BY 4.0")
    fetch(dest)
    build(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
