"""
sync_labels.py -- share the (small) MLD label CSVs between the data tree and the repo.

Why: the human MLD labels (science + training) live in ~/ooi/<site>/metadata/annotations/, but
~/ooi is not in git. The files are tiny, so a copy lives in the repo at ~/argosy/shared_labels/.
Workflow:
    labeler:       python sync_labels.py push   ->  git add shared_labels && git commit && git push
    collaborator:  git pull  ->  python sync_labels.py pull   (then MLDTimeSeries.py sees them)

Files handled (per site, per labeler `who`):
    mld_labels_<site>_science_<who>.csv     dense month-block "science" labels
    mld_labels_<site>_block05_<who>.csv     1-in-45 training labels

MERGE, never blind overwrite. Each label row is keyed by (gpi, sensor, who). When the same key
exists on both sides, the row with the LATER `reviewed_at` wins (ties keep the destination, so
re-running is a no-op). Rows only on one side are added. A destination file is rewritten only if
something actually changed. Consequence: because filenames carry `who`, two labelers never touch
each other's files; and a label DELETED with "Clear pick" is not removed from the other side.

Direction:
    push : ~/ooi/<site>/metadata/annotations/   ->  ~/argosy/shared_labels/
    pull : ~/argosy/shared_labels/              ->  ~/ooi/<site>/metadata/annotations/

Usage:
    python ~/argosy/sync_labels.py push --dry-run
    python ~/argosy/sync_labels.py push
    python ~/argosy/sync_labels.py pull
    python ~/argosy/sync_labels.py pull --site sb --who R
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op  # noqa: E402

SHARED = op.ARGOSY_ROOT / "shared_labels"
KEY = ["gpi", "sensor", "who"]
NAME_RE = re.compile(r"^mld_labels_(?P<site>[a-z]{2})_(?P<kind>science|block05)_(?P<who>[A-Za-z0-9]+)\.csv$")


def candidates(src_dir, sites, who):
    """Label files in src_dir matching the naming pattern, filtered by site / who."""
    out = []
    for p in sorted(src_dir.glob("mld_labels_*.csv")):
        m = NAME_RE.match(p.name)
        if not m or m["site"] not in sites:
            continue
        if who and m["who"] != who:
            continue
        out.append((m["site"], p))
    return out


def merge(src, dst):
    """Merge src rows into dst by KEY, later reviewed_at wins, ties keep dst.
    Returns (merged_df or None if nothing changed, n_added, n_updated)."""
    s = pd.read_csv(src)
    if not dst.exists():
        return s, len(s), 0
    d = pd.read_csv(dst)
    cols = list(d.columns) + [c for c in s.columns if c not in d.columns]
    s["_prio"], d["_prio"] = 0, 1                      # 1 = destination wins ties
    both = pd.concat([s, d], ignore_index=True)
    both["_t"] = pd.to_datetime(both["reviewed_at"], utc=True, errors="coerce")
    both = both.sort_values(["_t", "_prio"], kind="stable")
    kept = both.drop_duplicates(subset=KEY, keep="last")
    from_src = kept[kept["_prio"] == 0]
    if from_src.empty:
        return None, 0, 0
    dst_keys = set(map(tuple, d[KEY].values))
    n_added = sum(1 for k in map(tuple, from_src[KEY].values) if k not in dst_keys)
    n_updated = len(from_src) - n_added
    merged = kept.sort_values(["gpi", "sensor"]).reset_index(drop=True)[cols]
    return merged, n_added, n_updated


def sync(direction, sites, who, dry):
    if direction == "push":
        pairs = [(site, p, SHARED / p.name)
                 for site in sites
                 for (_, p) in candidates(op.metadata_dir(site, "annotations"), [site], who)]
    else:
        pairs = []
        for site, p in candidates(SHARED, sites, who):
            pairs.append((site, p, op.metadata_dir(site, "annotations") / p.name))
    if not pairs:
        print("no matching label files found.")
        return
    for site, src, dst in pairs:
        merged, n_add, n_upd = merge(src, dst)
        if merged is None:
            print(f"  same     {dst.name}")
            continue
        print(f"  {'would write' if dry else 'write':11s}{dst.name}  (+{n_add} new, "
              f"{n_upd} updated)  -> {dst.parent}")
        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(src, dst)          # first copy: byte-identical
            else:
                merged.to_csv(dst, index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("direction", choices=("push", "pull"))
    ap.add_argument("--site", choices=op.SITES, default=None, help="one site (default all)")
    ap.add_argument("--who", default=None, help="one labeler, e.g. R (default all)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sites = [args.site] if args.site else list(op.SITES)
    SHARED.mkdir(parents=True, exist_ok=True)
    sync(args.direction, sites, args.who, args.dry_run)


if __name__ == "__main__":
    main()
