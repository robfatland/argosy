"""
mld_label_gaps.py -- which profiles of one site-year still lack an MLD label?

For every profile in the OOI profile index (RS01SBPS etc.) and each of temperature / salinity /
dissolved oxygen, report whether a label row exists for (gpi, sensor) in the training
(block05) or science label CSV. A label of any kind counts: an MLD value, No MLD, or
No Usable Data. A profile with no pp06 shard for that sensor is counted as a data gap
(outage), not as unlabeled.

Usage (headless):
    python ~/argosy/vis/mld_label_gaps.py                      # sb 2024
    python ~/argosy/vis/mld_label_gaps.py --site oo --year 2023

Output: summary on screen, plus the unlabeled list in
    ~/ooi/<site>/analysis/mld_label_gaps_<site>_<year>.csv
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ooipaths as op

WHO = "R"
SENSORS = ("temperature", "salinity", "dissolvedoxygen")
DESIGNATOR = {"sb": "RS01SBPS", "oo": "CE04OSPS", "ab": "RS03AXPS"}
SHARD_RE = re.compile(r"^RCA_[a-z]{2}_sp_(\w+?)_\d{4}_\d{3}_(\d+)_\d+_V\d+\.nc$")


def load_labels(site):
    frames = []
    for kind in ("block05", "science"):
        p = op.metadata_dir(site, "annotations") / f"mld_labels_{site}_{kind}_{WHO}.csv"
        if p.exists():
            df = pd.read_csv(p)
            if "who" in df.columns:
                df = df[df["who"].astype(str) == WHO]
            df["source"] = kind
            frames.append(df[["gpi", "sensor", "source"]])
        else:
            print(f"  (no {p.name})")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["gpi", "sensor", "source"])


def shard_gpis(site, year):
    """{sensor: set(gpi)} for the pp06 shards of one year."""
    have = {s: set() for s in SENSORS}
    root = op.postproc_dir("pp06", year, site)
    for f in Path(root).rglob("*.nc"):
        m = SHARD_RE.match(f.name)
        if m and m.group(1) in have:
            have[m.group(1)].add(int(m.group(2)))
    return have


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="sb", choices=sorted(DESIGNATOR))
    ap.add_argument("--year", type=int, default=2024)
    a = ap.parse_args()

    idx = op.profile_index_dir(a.site) / f"{DESIGNATOR[a.site]}_profiles_{a.year}.csv"
    prof = pd.read_csv(idx, parse_dates=["start"])
    prof = prof.rename(columns={"profile": "gpi"})
    print(f"{a.site} {a.year}: {len(prof)} profiles in {idx.name} "
          f"({prof['start'].min():%Y-%m-%d} to {prof['start'].max():%Y-%m-%d})")

    lab = load_labels(a.site)
    lab_keys = {s: set(lab.loc[lab["sensor"] == s, "gpi"].astype(int)) for s in SENSORS}
    have = shard_gpis(a.site, a.year)
    print(f"pp06 shards found: " + ", ".join(f"{s}={len(have[s])}" for s in SENSORS))

    rows, missing = [], []
    for s in SENSORS:
        gp = set(prof["gpi"].astype(int))
        n_data = len(gp & have[s])
        n_lab = len(gp & lab_keys[s])
        n_lab_data = len(gp & have[s] & lab_keys[s])
        unl = sorted((gp & have[s]) - lab_keys[s])
        rows.append((s, len(gp), len(gp) - n_data, n_data, n_lab_data, len(unl)))
        missing += [(g, s) for g in unl]
        if n_lab - n_lab_data:
            print(f"  note: {s}: {n_lab - n_lab_data} labels point at profiles with no pp06 shard")

    print(f"\n{'sensor':16s}{'profiles':>9s}{'no data':>9s}{'w/ data':>9s}{'labeled':>9s}{'MISSING':>9s}")
    for r in rows:
        print(f"{r[0]:16s}{r[1]:9d}{r[2]:9d}{r[3]:9d}{r[4]:9d}{r[5]:9d}")

    if missing:
        out = pd.DataFrame(missing, columns=["gpi", "sensor"]).merge(prof, on="gpi", how="left")
        out = out.sort_values(["sensor", "gpi"])
        d = op.metadata_dir(a.site).parent / "analysis"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"mld_label_gaps_{a.site}_{a.year}.csv"
        out.to_csv(p, index=False)
        out["month"] = out["start"].dt.strftime("%Y-%m")
        print("\nUnlabeled (profile with data, no label) by month:")
        print(out.pivot_table(index="month", columns="sensor", values="gpi", aggfunc="count", fill_value=0))
        print(f"\nWrote {len(out)} rows to {p}")
    else:
        print("\nEvery profile with data has a label for all three sensors.")


if __name__ == "__main__":
    main()
