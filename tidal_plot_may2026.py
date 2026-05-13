"""
tidal_plot_may2026.py

Plot predicted tidal height for the 3 OOI/RCA shallow profiler sites
for May 2026 (30 days). Uses constituents from tidal_constituents.json.

Output: tidal_height_may2026.png
"""

import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
from pathlib import Path


def predict_tide(constituents_dict, times):
    """Predict tidal height from extracted constituents."""
    t0 = datetime(2000, 1, 1, tzinfo=timezone.utc)
    hours = np.array([(t - t0).total_seconds() / 3600.0 for t in times])
    heights = np.zeros(len(hours))
    for const_name, params in constituents_dict.items():
        amp = params["amplitude_m"]
        phase = np.radians(params["phase_deg"])
        omega = np.radians(params["omega_deg_per_hr"])
        heights += amp * np.cos(omega * hours - phase)
    return heights


# Load constituents
json_path = Path(__file__).parent / "tidal_constituents.json"
with open(json_path) as f:
    data = json.load(f)

# Time array: May 1-30, 2026, hourly
t_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
n_hours = 30 * 24
times = [t_start + timedelta(hours=h) for h in range(n_hours + 1)]

# Predict for each site
sites = {
    "Oregon Offshore":   {"color": "#1f77b4"},  # blue
    "Oregon Slope Base": {"color": "#d62728"},  # red
    "Axial Base":        {"color": "#2ca02c"},  # green
}

fig, ax = plt.subplots(figsize=(14, 5))

for site_name, style in sites.items():
    h = predict_tide(data[site_name]["constituents"], times)
    days = np.array([(t - t_start).total_seconds() / 86400.0 for t in times])
    ax.plot(days, h, color=style["color"], linewidth=0.8, label=site_name)

ax.set_xlabel("Day of May 2026")
ax.set_ylabel("Tidal Height (m, relative to MSL)")
ax.set_title("Predicted Tidal Height — OOI/RCA Shallow Profiler Sites — May 2026")
ax.legend(loc="upper right")
ax.set_xlim(0, 30)
ax.grid(True, alpha=0.3)
ax.axhline(0, color='k', linewidth=0.5)

plt.tight_layout()
out_path = Path(__file__).parent / "tidal_height_may2026.png"
plt.savefig(out_path, dpi=150)
print(f"Saved: {out_path}")
