"""
gen_manifest.py -- build the project manifest (a table of sub-project folders) from the folder READMEs,
so it is generated, not hand-maintained.

Each folder README carries three bullet lines near the top:
    - **Status:** active | paused | stub (reviewed Nov 2026)
    - **Purpose:** one line
    - **Next:** one line
The folders are listed in a logical order (ORDER below), grouped by role, not alphabetically.
Folders that have a README or Python files but are missing from ORDER are reported under UNLISTED, and
READMEs with no Status line are flagged, so nothing slips through.

Usage (from the repo root):
    python tools/gen_manifest.py                      # print the manifest to the screen
    python tools/gen_manifest.py --next               # include the Next column
    python tools/gen_manifest.py --write poster/agumemo.md
        # replaces the text between <!-- MANIFEST:START --> and <!-- MANIFEST:END --> in that file
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALID = ("active", "paused", "stub")
SKIP = {".git", "_build", "__pycache__", ".ipynb_checkpoints", ".kiro", "cdk.out", "node_modules"}

ORDER = [
    ("A. Get the data (Phase 1)", ["pipeline", "cloud", "visqc"]),
    ("B. Look at the data", ["vis", "chapters", "images"]),
    ("C. Interpret the data (Phase 2)", ["mld", "mld_candidates", "shared_labels", "som", "iw", "sga"]),
    ("D. Compare with the outside world", ["seastate", "argo", "plume"]),
    ("E. Share and communicate", ["poster", "reference"]),
    ("F. Support and archive", ["tools", "LegacyCode"]),
]
START, END = "<!-- MANIFEST:START -->", "<!-- MANIFEST:END -->"


def field(text, name):
    m = re.search(rf"^\s*[-*]?\s*\*\*{name}:\*\*\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def info(folder):
    p = ROOT / folder / "README.md"
    if not p.exists():
        return {"folder": folder, "status": "?", "purpose": "(no README)", "next": "", "problem": "no README"}
    text = p.read_text(encoding="utf-8", errors="replace")
    status = field(text, "Status")
    word = (re.match(r"[A-Za-z]+", status).group(0).lower() if status else "")
    problem = "" if word in VALID else ("no Status line" if not status else f"unknown status '{word}'")
    return {"folder": folder, "status": word or "?", "purpose": field(text, "Purpose") or "(no Purpose line)",
            "next": field(text, "Next"), "problem": problem}


def cell(s):
    return s.replace("|", "/").replace("\n", " ")


def build(show_next):
    out, problems, listed = [], [], set()
    for title, folders in ORDER:
        out.append(f"**{title}**")
        out.append("")
        head = "| Folder | Status | Purpose |" + (" Next |" if show_next else "")
        # dash counts set the relative column widths when pandoc builds the PDF
        sep = "|" + "-" * 14 + "|" + "-" * 8 + "|" + "-" * 60 + "|" + (("-" * 40 + "|") if show_next else "")
        out += [head, sep]
        for f in folders:
            listed.add(f)
            d = info(f)
            if d["problem"]:
                problems.append(f"{f}: {d['problem']}")
            row = f"| `{f}/` | {d['status']} | {cell(d['purpose'])} |"
            if show_next:
                row += f" {cell(d['next'])} |"
            out.append(row)
        out.append("")
    extra = []
    for name in sorted(os.listdir(ROOT)):
        p = ROOT / name
        if p.is_dir() and name not in SKIP and name not in listed:
            if (p / "README.md").exists() or any(p.glob("*.py")):
                extra.append(name)
    if extra:
        problems.append("UNLISTED folders (add to ORDER): " + ", ".join(extra))
    return "\n".join(out).rstrip() + "\n", problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--next", action="store_true", help="include the Next column")
    ap.add_argument("--write", metavar="FILE", help="rewrite the marked MANIFEST block in FILE")
    args = ap.parse_args()
    table, problems = build(args.next)
    if args.write:
        fp = (ROOT / args.write) if not Path(args.write).is_absolute() else Path(args.write)
        text = fp.read_text(encoding="utf-8")
        if START not in text or END not in text:
            print(f"markers {START} ... {END} not found in {fp}")
            return 2
        block = START + "\n\n" + table + "\n" + END
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, text, flags=re.S)
        fp.write_text(new, encoding="utf-8")
        print(f"manifest written into {fp}")
    else:
        print(table)
    if problems:
        print("\nPROBLEMS:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
