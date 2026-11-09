"""
check_refs.py -- keep argosy's cross-references honest while files move.

It finds references that no longer resolve, and (before a move) reports everything that mentions a
file. Read-only: it never edits anything.

WHAT COUNTS AS A REFERENCE
  - a file or path named in text (`foo.py`, `sga/sga_module1.py`, `~/argosy/images/x.png`)
  - a markdown link target, a `%run` target, a `file:` entry in _toc.yml, a backticked `folder/`
  - a Python import of a module that lives in this repo, with a check that it would still be found
    when the script runs (it must sit beside the module or set sys.path)
HISTORICAL files (SessionState.md, DevelopmentLog.md) describe the past: their stale references are
listed separately and never fail the check.

MODES
  python tools/check_refs.py                  compare with tools/refs_baseline.json; exit 1 if NEW dangling refs
  python tools/check_refs.py --baseline       record the current state as the baseline (do this first)
  python tools/check_refs.py --all            list every dangling reference, ignoring the baseline
  python tools/check_refs.py --impact NAME    blast radius of moving/renaming NAME (a file name or path):
                                              every line that mentions it (live vs historical), who imports
                                              it, and the sys.path hazard of moving a .py file

NOISE CONTROL
  - bare names are checked only for code/doc files (.py .md .ipynb .yml .sh .tex); data-looking names
    (.csv .png ...) are checked only when written with a path that starts at a real repo folder
  - tools/refs_ignore.txt: one regex per line for tokens to skip (examples, other repos)
  - when you retire a folder, add its name to RETIRED_DIRS below so stale mentions are caught

Usage from the repo root:  python tools/check_refs.py --baseline   then, after each change,  python tools/check_refs.py
"""
import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
BASELINE = TOOLS / "refs_baseline.json"
IGNORE_FILE = TOOLS / "refs_ignore.txt"

SKIP_DIRS = {".git", "_build", "__pycache__", ".ipynb_checkpoints", "cdk.out", "node_modules"}
TEXT_EXT = {".md", ".py", ".ipynb", ".yml", ".yaml", ".sh", ".tex", ".html", ".txt"}
SKIP_FILES = {"slides.html", "download_link_list.txt", "downlinklist_completed.txt", "environment.yml",
              "refs_baseline.json"}
HISTORICAL = {"SessionState.md", "DevelopmentLog.md"}
CODE_DOC_EXT = {".py", ".md", ".ipynb", ".yml", ".yaml", ".sh", ".tex"}
ABS_PREFIXES = ("~/argosy/", "/home/rob/argosy/")
RETIRED_DIRS = {"NDBC"}          # folders removed on purpose (add yours here)
MAX_BYTES = 3_000_000
DEFAULT_IGNORE = [
    r"^(X|foo|bar|baz|name|file|dosomething|yourfigure|example|abc|xyz|my\w*)\.\w+$",
    r"(^|/)_build(/|$)", r"(^|/)\.git(/|$)", r"__pycache__", r"\.ipynb_checkpoints",
]

PATH_RE = re.compile(
    r"(?<![\w/.~$<{-])"
    r"((?:~/argosy/|/home/rob/argosy/|\.\./|\./)?(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-][A-Za-z0-9_.-]*"
    r"\.(?:py|md|ipynb|ya?ml|sh|csv|json|png|jpe?g|tex|bib|txt|pdf|html))(?![\w/-])")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
RUN_RE = re.compile(r"%run\s+(?:-\w+\s+)*([^\s\"']+)")
DIR_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_-]*)/`")
TOC_RE = re.compile(r"^\s*-?\s*file:\s*([^\s#]+)", re.M)


# --------------------------------------------------------------------------- repo index
def walk_repo():
    rels = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            rels.append((Path(dp) / f).relative_to(ROOT).as_posix())
    return rels


ALL_LIST = walk_repo()
ALL = set(ALL_LIST)
DIRS = {str(Path(p).parent.as_posix()) for p in ALL_LIST}
for _d in list(DIRS):               # add every ancestor directory
    parts = _d.split("/")
    for i in range(1, len(parts) + 1):
        DIRS.add("/".join(parts[:i]))
DIRS.discard(".")
BY_NAME = defaultdict(list)
for _p in ALL_LIST:
    BY_NAME[_p.rsplit("/", 1)[-1]].append(_p)
TOP_DIRS = {d for d in DIRS if "/" not in d}
ROOT_PY_STEMS = {p[:-3] for p in ALL_LIST if "/" not in p and p.endswith(".py")}
LOCAL_TOP = ROOT_PY_STEMS | {d for d in TOP_DIRS if any(p.startswith(d + "/") and p.endswith(".py") for p in ALL_LIST)}


def read_text(rel):
    p = ROOT / rel
    try:
        if p.stat().st_size > MAX_BYTES:
            return ""
        raw = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if p.suffix == ".ipynb":
        try:
            nb = json.loads(raw)
            out = []
            for c in nb.get("cells", []):
                s = c.get("source", "")
                out.append("".join(s) if isinstance(s, list) else str(s))
            return "\n".join(out)
        except Exception:
            return ""
    return raw


def load_ignores():
    pats = list(DEFAULT_IGNORE)
    if IGNORE_FILE.exists():
        for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pats.append(line)
    return [re.compile(p) for p in pats]


# --------------------------------------------------------------------------- resolution
def norm(path_str):
    return os.path.normpath(path_str).replace("\\", "/")


def exists(rel):
    return rel in ALL or rel.rstrip("/") in DIRS


def resolve(token, src_rel):
    t = token
    for pre in ABS_PREFIXES:
        if t.startswith(pre):
            return exists(norm(t[len(pre):]))
    srcdir = Path(src_rel).parent.as_posix()
    if t.startswith(("../", "./")):
        return exists(norm((srcdir + "/" + t) if srcdir != "." else t))
    if exists(norm(t)):
        return True
    cand = norm((srcdir + "/" + t) if srcdir != "." else t)
    if exists(cand):
        return True
    if "/" not in t:
        return t in BY_NAME
    return any(f.endswith("/" + t) for f in ALL)


def should_check(token, known_dirs):
    if token.startswith(ABS_PREFIXES) or token.startswith(("../", "./")):
        return True
    if "/" in token:
        return token.split("/")[0] in known_dirs
    return ("." + token.rsplit(".", 1)[-1].lower()) in CODE_DOC_EXT


def extract(rel, text):
    toks = []
    if Path(rel).name == "_toc.yml":
        return [("toc", m.group(1)) for m in TOC_RE.finditer(text)]
    for m in PATH_RE.finditer(text):
        toks.append(("path", m.group(1)))
    for m in LINK_RE.finditer(text):
        t = m.group(1).split("#")[0]
        if t and not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", t) and "{" not in t:
            toks.append(("link", t))
    for m in RUN_RE.finditer(text):
        toks.append(("run", m.group(1)))
    for m in DIR_RE.finditer(text):
        toks.append(("dir", m.group(1)))
    return toks


def check_python(rel, text):
    """Import problems: a repo-local module that is missing, or not findable from where the script sits."""
    problems = []
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return [("syntax", f"line {e.lineno}: {e.msg}")]
    sets_path = "sys.path" in text
    here = Path(rel).parent.as_posix()
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods = [node.module]
        for m in mods:
            top = m.split(".")[0]
            if top not in LOCAL_TOP:
                continue
            parts = m.split(".")
            base = "/".join(parts)
            if not (base + ".py" in ALL or base + "/__init__.py" in ALL or base in DIRS):
                problems.append(("import-missing", f"import {m}: no such module under the repo root"))
                continue
            beside = here == "." or (here + "/" + top + ".py") in ALL or (here + "/" + top) in DIRS
            if not beside and not sets_path:
                problems.append(("import-path", f"import {m}: lives at the repo root but this script sets no sys.path"))
    return problems


# --------------------------------------------------------------------------- scan
def scan(known_dirs, ignores):
    live, hist, texts = [], [], {}
    abs_count = 0
    for rel in ALL_LIST:
        p = Path(rel)
        if p.suffix not in TEXT_EXT or p.name in SKIP_FILES:
            continue
        text = read_text(rel)
        if not text:
            continue
        texts[rel] = text
        if "/home/rob/argosy" in text and rel != "tools/check_refs.py":
            abs_count += 1
        target = hist if p.name in HISTORICAL else live
        seen = set()
        for kind, tok in extract(rel, text):
            if tok in seen or any(r.search(tok) for r in ignores):
                continue
            seen.add(tok)
            if kind == "dir":
                if tok in RETIRED_DIRS or (tok in known_dirs and tok not in TOP_DIRS):
                    target.append((rel, tok + "/", "retired-folder mention"))
                continue
            if kind == "toc":
                ok = any(exists(norm(tok + e)) for e in ("", ".md", ".ipynb", ".rst"))
            elif not should_check(tok, known_dirs):
                continue
            else:
                ok = resolve(tok, rel)
            if not ok:
                target.append((rel, tok, kind))
        if p.suffix == ".py" and p.name not in HISTORICAL:
            for kind, detail in check_python(rel, text):
                target.append((rel, detail, kind))
    return live, hist, texts, abs_count


def keyset(items):
    return {f"{r}|{k}|{t}" for r, t, k in items}


# --------------------------------------------------------------------------- impact
def impact(name, texts):
    needle = name.replace("\\", "/")
    stem = Path(needle).stem
    targets = [f for f in ALL_LIST if f == needle or f.endswith("/" + needle)]
    print(f"IMPACT of moving/renaming: {needle}")
    print("  found at: " + (", ".join(targets) if targets else "(not in repo; reporting text mentions only)"))
    live, hist = defaultdict(list), defaultdict(list)
    for rel, text in texts.items():
        if rel in targets:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if needle in line:
                (hist if Path(rel).name in HISTORICAL else live)[rel].append((i, line.strip()))
    for title, grp in (("LIVE (must be updated if it moves)", live), ("HISTORICAL (leave alone)", hist)):
        n = sum(len(v) for v in grp.values())
        print(f"\n{title}: {len(grp)} files, {n} lines")
        for rel in sorted(grp):
            print(f"  {rel}")
            for i, line in grp[rel][:3]:
                print(f"      {i}: {line[:110]}")
            if len(grp[rel]) > 3:
                print(f"      ... {len(grp[rel]) - 3} more")
    for tgt in targets:
        if not tgt.endswith(".py"):
            continue
        text = texts.get(tgt) or read_text(tgt)
        print(f"\nIF {tgt} MOVES (python hazards):")
        print("  sets sys.path itself: " + ("yes" if "sys.path" in text else "NO"))
        local = [m for m in re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][\w]*)", text, re.M) if m in LOCAL_TOP]
        print("  imports repo-local modules: " + (", ".join(sorted(set(local))) or "none"))
        if local and "sys.path" not in text:
            print("  -> HAZARD: these imports work today only because the script sits at the repo root;")
            print("     add a sys.path line before moving it.")
        importers = [r for r, t in texts.items() if r not in targets and
                     re.search(rf"^\s*(?:from|import)\s+{re.escape(stem)}\b", t, re.M)]
        print("  imported by: " + (", ".join(sorted(importers)) or "nobody"))
        shells = [r for r, t in texts.items() if r.endswith(".sh") and Path(tgt).name in t]
        print("  called from shell scripts: " + (", ".join(sorted(shells)) or "none"))


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", action="store_true", help="record the current state as the baseline")
    ap.add_argument("--all", action="store_true", help="list every dangling reference (ignore the baseline)")
    ap.add_argument("--impact", metavar="NAME", help="blast radius of moving NAME")
    args = ap.parse_args()

    base = {}
    if BASELINE.exists():
        try:
            base = json.loads(BASELINE.read_text(encoding="utf-8"))
        except Exception:
            base = {}
    known_dirs = set(TOP_DIRS) | RETIRED_DIRS | set(base.get("top_dirs", []))
    ignores = load_ignores()
    live, hist, texts, abs_count = scan(known_dirs, ignores)

    if args.impact:
        impact(args.impact, texts)
        return 0

    cur_live, cur_hist = keyset(live), keyset(hist)
    if args.baseline:
        BASELINE.write_text(json.dumps({
            "generated": date.today().isoformat(),
            "top_dirs": sorted(TOP_DIRS),
            "live": sorted(cur_live),
            "historical": sorted(cur_hist),
        }, indent=1), encoding="utf-8")
        print(f"baseline written: {BASELINE}  ({len(cur_live)} live, {len(cur_hist)} historical)")
        return 0

    old = set(base.get("live", []))
    new = sorted(cur_live - old) if not args.all else sorted(cur_live)
    fixed = sorted(old - cur_live)
    print(f"files scanned: {len(texts)}   dangling now: {len(cur_live)} live, {len(cur_hist)} historical"
          f"   baseline: {len(old)}" + ("" if base else "   (NO BASELINE: run with --baseline)"))
    print(f"files that hard-code /home/rob/argosy (not portable): {abs_count}")
    label = "ALL dangling references" if args.all else "NEW dangling references (not in baseline)"
    print(f"\n{label}: {len(new)}")
    for k in new:
        r, kind, tok = k.split("|", 2)
        print(f"  {r}: {tok}   [{kind}]")
    if not args.all and fixed:
        print(f"\nFIXED since baseline: {len(fixed)}")
        for k in fixed:
            r, kind, tok = k.split("|", 2)
            print(f"  {r}: {tok}")
    return 1 if (new and not args.all) else 0


if __name__ == "__main__":
    sys.exit(main())
