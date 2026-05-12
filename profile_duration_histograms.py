"""
DataSharding notebook cell: Profile duration histograms + UTC noon/midnight verification
Oregon Slope Base shallow profiler (RS01SBPS)

Three histograms with 2-minute bin widths, x-axis fixed 0-250 minutes:
  1. Ascent duration  (start -> peak)
  2. Descent duration (peak -> end)
  3. Total duration   (start -> end)

Also writes:
  ~/argosy/profiles_midnight.csv
  ~/argosy/profiles_noon.csv

And prints a per-year summary table to stdout.
"""

import glob
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo

# ── Config ────────────────────────────────────────────────────────────────────
SITE_TZ             = ZoneInfo("America/Los_Angeles")
PROFILE_INDICES_DIR = "/home/rob/ooi/profileIndices"
SITE_PATTERN        = "RS01SBPS_profiles_*.csv"
OUTPUT_PNG          = "/home/rob/ooi/visualizations/SlopeBaseProfileHistograms.png"
OUT_MIDNIGHT        = "/home/rob/ooi/metadata/ooi_rca_sb_midnight_global_profile_indices.csv"
OUT_NOON            = "/home/rob/ooi/metadata/ooi_rca_sb_noon_global_profile_indices.csv"

MIN_GAP_HOURS = 20.0   # minimum separation between same-class profiles

# ── Load all RS01SBPS profileIndices files ────────────────────────────────────
files = sorted(glob.glob(f"{PROFILE_INDICES_DIR}/{SITE_PATTERN}"))
print(f"Found {len(files)} RS01SBPS profileIndices files:")
for f in files:
    print(f"  {f}")

frames = [pd.read_csv(f, parse_dates=["start", "peak", "end"]) for f in files]
pi = pd.concat(frames, ignore_index=True).sort_values("start").reset_index(drop=True)
print(f"\nTotal profiles loaded: {len(pi)}")
print(f"Date range: {pi['start'].min()} to {pi['end'].max()}")

# ── Compute durations ─────────────────────────────────────────────────────────
pi["ascent_min"]  = (pi["peak"]  - pi["start"]).dt.total_seconds() / 60.0
pi["descent_min"] = (pi["end"]   - pi["peak"] ).dt.total_seconds() / 60.0
pi["total_min"]   = (pi["end"]   - pi["start"]).dt.total_seconds() / 60.0

valid = pi[(pi["ascent_min"] > 0) & (pi["descent_min"] > 0)].copy()
print(f"Profiles with valid durations: {len(valid)}")

# ── Histogram helper ──────────────────────────────────────────────────────────
BIN_WIDTH = 2
X_MIN, X_MAX = 0, 250
BINS = np.arange(X_MIN, X_MAX + BIN_WIDTH, BIN_WIDTH)

def duration_histogram(ax, data, title, color):
    counts, edges, _ = ax.hist(data, bins=BINS, color=color,
                               edgecolor="white", linewidth=0.3)

    nonzero = [(c, e) for c, e in zip(counts, edges[:-1]) if c > 0]
    if nonzero:
        # 'm' above leftmost non-zero bin
        min_count, min_edge = min(nonzero, key=lambda x: x[1])
        ax.text(min_edge + BIN_WIDTH / 2, min_count, 'm',
                ha='center', va='bottom', fontsize=9, color='black')

        # 'M' above rightmost non-zero bin; 'M>' shifted left if beyond x-axis
        max_count, max_edge = max(nonzero, key=lambda x: x[1])
        max_center = max_edge + BIN_WIDTH / 2
        if max_center > X_MAX:
            ax.text(X_MAX - 4, max_count, 'M>', ha='center', va='bottom',
                    fontsize=9, color='black')
        else:
            ax.text(max_center, max_count, 'M', ha='center', va='bottom',
                    fontsize=9, color='black')

    ax.set_xlim(X_MIN, X_MAX)
    ax.set_title(title)
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Count")
    ax.xaxis.set_minor_locator(plt.MultipleLocator(BIN_WIDTH))
    ax.grid(axis="y", alpha=0.4)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Oregon Slope Base Shallow Profiler — Profile Durations (RS01SBPS)", fontsize=13)

duration_histogram(axes[0], valid["ascent_min"],  "Ascent Duration\n(start to peak)",  "#2196F3")
duration_histogram(axes[1], valid["descent_min"], "Descent Duration\n(peak to end)",   "#FF9800")
duration_histogram(axes[2], valid["total_min"],   "Total Duration\n(start to end)",    "#4CAF50")

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150)
print(f"\nChart saved to {OUTPUT_PNG}")

# ── Classify profiles ─────────────────────────────────────────────────────────
def classify_peak(utc_ts):
    h = utc_ts.tz_localize("UTC").astimezone(SITE_TZ).hour
    if 11 <= h <= 13:
        return "noon"
    elif h >= 23 or h <= 1:
        return "midnight"
    return "other"

valid["peak_class"] = valid["peak"].apply(classify_peak)

# ── Build filtered noon / midnight tables ─────────────────────────────────────
def build_special_profiles(df, label):
    """
    From profiles classified as `label` by local peak hour:
      - at least MIN_GAP_HOURS between consecutive retained entries
        (enforces one per day)
    Returns DataFrame with columns: profile, start, peak, end
    """
    subset = df[df["peak_class"] == label].sort_values("start").reset_index(drop=True)

    kept = []
    last_start = None
    for _, row in subset.iterrows():
        if last_start is None or (row["start"] - last_start).total_seconds() / 3600 >= MIN_GAP_HOURS:
            kept.append(row)
            last_start = row["start"]

    return pd.DataFrame(kept)[["profile", "start", "peak", "end"]].reset_index(drop=True)

midnight_df = build_special_profiles(valid, "midnight")
noon_df     = build_special_profiles(valid, "noon")

midnight_df.to_csv(OUT_MIDNIGHT, index=False)
noon_df.to_csv(OUT_NOON, index=False)
print(f"\nWrote {len(midnight_df)} midnight profiles to {OUT_MIDNIGHT}")
print(f"Wrote {len(noon_df)} noon profiles to {OUT_NOON}")

# ── Per-year summary table ────────────────────────────────────────────────────
midnight_df["year"] = pd.to_datetime(midnight_df["start"]).dt.year
noon_df["year"]     = pd.to_datetime(noon_df["start"]).dt.year

# Count active days per year: UTC days with at least one non-noon/non-midnight profile
other_profiles = valid[valid["peak_class"] == "other"].copy()
other_profiles["utc_date"] = other_profiles["start"].dt.date
other_profiles["year"]     = other_profiles["start"].dt.year
active_days = other_profiles.groupby("year")["utc_date"].nunique()

all_years = sorted(set(midnight_df["year"]) | set(noon_df["year"]) | set(active_days.index))

print("\n── Per-year midnight / noon profile counts ──────────────────────────────")
print(f"{'Year':>6}  {'Midnight':>10}  {'Noon':>8}  {'Active Days':>12}")
print(f"{'----':>6}  {'--------':>10}  {'----':>8}  {'-----------':>12}")
total_days = 0
for yr in all_years:
    n_mid  = int((midnight_df["year"] == yr).sum())
    n_noon = int((noon_df["year"]     == yr).sum())
    n_days = int(active_days.get(yr, 0))
    total_days += n_days
    print(f"{yr:>6}  {n_mid:>10}  {n_noon:>8}  {n_days:>12}")
print(f"{'Total':>6}  {len(midnight_df):>10}  {len(noon_df):>8}  {total_days:>12}")

# ── Summary with possible count ───────────────────────────────────────────────
total_days_possible = (valid["end"].max() - valid["start"].min()).days + 1
print(f"\nFound {len(midnight_df)} midnight profiles out of {total_days_possible} possible")
print(f"Found {len(noon_df)} noon profiles out of {total_days_possible} possible")
