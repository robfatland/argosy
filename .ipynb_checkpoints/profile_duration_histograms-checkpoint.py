"""
DataSharding notebook cell: Profile duration histograms + UTC noon/midnight verification
Oregon Slope Base shallow profiler (RS01SBPS)

Three histograms with 2-minute bin widths:
  1. Ascent duration  (start -> peak)
  2. Descent duration (peak -> end)
  3. Total duration   (start -> end)

Plus: verify that UTC times in profileIndices correspond to local noon and midnight
for the Oregon Slope Base site (longitude -125.39, UTC-8 standard / UTC-7 DST).
"""

import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo

# ── Site / timezone ──────────────────────────────────────────────────────────
SITE_TZ = ZoneInfo("America/Los_Angeles")   # handles PST/PDT automatically
PROFILE_INDICES_DIR = "/home/rob/ooi/profileIndices"
SITE_PATTERN = "RS01SBPS_profiles_*.csv"

# ── Load all RS01SBPS profileIndices files ───────────────────────────────────
files = sorted(glob.glob(f"{PROFILE_INDICES_DIR}/{SITE_PATTERN}"))
print(f"Found {len(files)} RS01SBPS profileIndices files:")
for f in files:
    print(f"  {f}")

frames = []
for f in files:
    df = pd.read_csv(f, parse_dates=["start", "peak", "end"])
    frames.append(df)

pi = pd.concat(frames, ignore_index=True)
pi = pi.sort_values("start").reset_index(drop=True)
print(f"\nTotal profiles loaded: {len(pi)}")
print(f"Date range: {pi['start'].min()} → {pi['end'].max()}")

# ── Compute durations in minutes ─────────────────────────────────────────────
pi["ascent_min"]  = (pi["peak"]  - pi["start"]).dt.total_seconds() / 60.0
pi["descent_min"] = (pi["end"]   - pi["peak"] ).dt.total_seconds() / 60.0
pi["total_min"]   = (pi["end"]   - pi["start"]).dt.total_seconds() / 60.0

# Drop any rows with non-positive durations (data quality guard)
valid = pi[(pi["ascent_min"] > 0) & (pi["descent_min"] > 0)]
print(f"Profiles with valid durations: {len(valid)}")

# ── Histogram helper ─────────────────────────────────────────────────────────
def duration_histogram(ax, data, title, color):
    bin_width = 2  # minutes
    lo = np.floor(data.min() / bin_width) * bin_width
    hi = np.ceil( data.max() / bin_width) * bin_width
    bins = np.arange(lo, hi + bin_width, bin_width)
    ax.hist(data, bins=bins, color=color, edgecolor="white", linewidth=0.3)
    ax.set_title(title)
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Count")
    ax.xaxis.set_minor_locator(plt.MultipleLocator(2))
    ax.grid(axis="y", alpha=0.4)

# ── Plot ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Oregon Slope Base Shallow Profiler — Profile Durations (RS01SBPS)", fontsize=13)

duration_histogram(axes[0], valid["ascent_min"],  "Ascent Duration\n(start → peak)",          "#2196F3")
duration_histogram(axes[1], valid["descent_min"], "Descent Duration\n(peak → end)",            "#FF9800")
duration_histogram(axes[2], valid["total_min"],   "Total Duration\n(start → end)",             "#4CAF50")

plt.tight_layout()
plt.show()

# ── UTC noon/midnight verification ───────────────────────────────────────────
# Oregon Slope Base longitude: -125.39°
# Solar noon offset from UTC: longitude / 15 ≈ -8.36 hours
# But we use the legal timezone (America/Los_Angeles) as specified in the project.

print("\n── UTC noon/midnight verification ──────────────────────────────────────")
print("Site: Oregon Slope Base  |  Longitude: -125.39°  |  TZ: America/Los_Angeles")
print("(UTC-8 standard time, UTC-7 daylight saving time)\n")

# Classify each profile's peak time as noon, midnight, or other
# A profile is 'noon' if local peak hour is 11–13; 'midnight' if 23 or 0–1
def classify_peak(utc_ts):
    local_ts = utc_ts.tz_localize("UTC").astimezone(SITE_TZ)
    h = local_ts.hour
    if 11 <= h <= 13:
        return "noon"
    elif h >= 23 or h <= 1:
        return "midnight"
    else:
        return "other"

valid = valid.copy()
valid["peak_class"] = valid["peak"].apply(classify_peak)

counts = valid["peak_class"].value_counts()
print("Peak-time classification (local time):")
for label in ["noon", "midnight", "other"]:
    print(f"  {label:>10}: {counts.get(label, 0):>6} profiles")

# Show a sample of noon and midnight profiles with their local peak times
print("\nSample noon profiles (local peak time):")
noon_sample = valid[valid["peak_class"] == "noon"].head(5)
for _, row in noon_sample.iterrows():
    local_peak = row["peak"].tz_localize("UTC").astimezone(SITE_TZ)
    utc_offset = local_peak.utcoffset().total_seconds() / 3600
    print(f"  profile {row['profile']:>6}  UTC peak: {row['peak']}  "
          f"local: {local_peak.strftime('%Y-%m-%d %H:%M')}  (UTC{utc_offset:+.0f})")

print("\nSample midnight profiles (local peak time):")
mid_sample = valid[valid["peak_class"] == "midnight"].head(5)
for _, row in mid_sample.iterrows():
    local_peak = row["peak"].tz_localize("UTC").astimezone(SITE_TZ)
    utc_offset = local_peak.utcoffset().total_seconds() / 3600
    print(f"  profile {row['profile']:>6}  UTC peak: {row['peak']}  "
          f"local: {local_peak.strftime('%Y-%m-%d %H:%M')}  (UTC{utc_offset:+.0f})")
