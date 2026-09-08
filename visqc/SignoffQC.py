# SignoffQC.py — Standalone scalar-data QC "sign-off" tool (Phase 1, interactive GUI).
#
# Purpose: a human first pass to SIGN OFF on the 11 scalar sensors, profile by profile —
# marking any that look suspect as Discard. NOT cline estimation (that's VisQCInspector).
#
# Run:  python ~/argosy/visqc/SignoffQC.py --site <sb|oo|ab> --year <yyyy>
#   Site also honors ARGOSY_SITE if --site omitted. Reads pp06 shards.
#   Interactive matplotlib TkAgg GUI — needs a display + `sudo apt install python3-tk`.
#
# Window: 4 charts on one row, each with multiple auto-scaled x-axes:
#   Chart 1: temperature, salinity, density
#   Chart 2: dissolvedoxygen, cdom, chlora
#   Chart 3: backscatter, nitrate, par
#   Chart 4: ph, pco2
# Title: GMT->local (America/Los_Angeles) time-of-day, tagged midnight/noon for those profiles.
# Controls: Advance/Back; Julian-day + Go To; 11 tri-state sensor buttons (Ok/None/Discard);
#   11 display toggles (declutter).
#
# Output (one row per GPI): metadata/annotations/scalar_signoff_<site>_<year>.csv
#   columns: gpi, visits, <11 sensor state cols>. State in {Ok, None (expected),
#   None (missing), Discard}. `visits` increments each time the tool lands on the GPI.
#   Resume/merge: relaunching a year loads the table and continues (no overwrite).
#
# Role: the discard decisions here feed the (TBD) pp07 construction. See BR.md + VisQC.md.

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, TextBox

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# == Configuration =============================================================

OREGON_TZ = ZoneInfo("America/Los_Angeles")

# The 11 scalar sensors, grouped into the 4 charts, with plot colors.
# (PAR was 'gold' — invisible on white; use a dark olive.)
CHART_SENSORS = [
    [("temperature", "red"), ("salinity", "blue"), ("density", "black")],
    [("dissolvedoxygen", "darkblue"), ("cdom", "darkcyan"), ("chlora", "green")],
    [("backscatter", "gray"), ("nitrate", "darkgreen"), ("par", "#8B4513")],
    [("ph", "purple"), ("pco2", "orange")],
]
SENSORS = [s for chart in CHART_SENSORS for (s, _c) in chart]   # flat list of 11, in order
SENSOR_COLOR = {s: c for chart in CHART_SENSORS for (s, c) in chart}

# LSD (restricted) sensors: only run on daily index 4 & 9 (noon/midnight). Their absence
# on OTHER profiles is expected, not a problem.
LSD_SENSORS = {"ph", "pco2", "nitrate"}

# Fixed x-axis ranges (override autoscale) — from sensortable.csv xlow/xhigh. PAR MUST be
# fixed: at night PAR ~0 and autoscale blows up the noise. Others can be added here later.
FIXED_RANGE = {}
try:
    _st = pd.read_csv(op.ARGOSY_ROOT / "sensortable.csv")
    for _, _r in _st.iterrows():
        _shard = str(_r.get("shard", "")).strip()
        if _shard and not pd.isna(_r.get("xlow")) and not pd.isna(_r.get("xhigh")):
            FIXED_RANGE[_shard] = (float(_r["xlow"]), float(_r["xhigh"]))
except Exception:
    pass
# For now apply fixed ranges only to PAR (per user); keep others autoscaled.
USE_FIXED_RANGE = {"par"}

# State tokens
OK = "Ok"
NONE_EXP = "None (expected)"
NONE_MISS = "None (missing)"
DISCARD = "Discard"

STATE_COLORS = {
    OK: "#c8e6c9",         # green
    NONE_EXP: "#e0e0e0",   # gray
    NONE_MISS: "#ffe0b2",  # amber (absent where it should be present)
    DISCARD: "#ef9a9a",    # red
}


def parse_args():
    ap = argparse.ArgumentParser(description="Scalar QC sign-off tool (Phase 1).")
    ap.add_argument("--site", default=op.DEFAULT_SITE, help="site code (sb/oo/ab)")
    ap.add_argument("--year", type=int, required=True, help="year to review, e.g. 2022")
    ap.add_argument("--reset", default=False, type=lambda v: str(v).lower() in ("1", "true", "yes", "y"),
                    help="reset the sign-off table for this site/year (default False)")
    return ap.parse_args()


ARGS = parse_args()
SITE = ARGS.site
if SITE not in op.SITES:
    print(f"Unknown site {SITE!r}; expected one of {op.SITES}")
    sys.exit(1)
YEAR = ARGS.year
PP06_YEAR_DIR = op.postproc_dir("pp06", YEAR, SITE)
SIGNOFF_CSV = op.metadata_dir(SITE, "annotations") / f"scalar_signoff_{SITE}_{YEAR}.csv"


# == Build the GPI -> {sensor: filepath} index for the year ====================

def build_index():
    """Scan pp06/<year> for shard files; return (gpi_files, sorted_gpis).
    gpi_files: {gpi: {sensor: Path}}."""
    gpi_files = {}
    if not PP06_YEAR_DIR.exists():
        print(f"ERROR: pp06 year dir not found: {PP06_YEAR_DIR}")
        print(f"       (run the pipeline for {SITE} {YEAR}, or sync pp06 from S3)")
        sys.exit(1)
    for sensor in SENSORS:
        for f in PP06_YEAR_DIR.glob(f"*_{sensor}_*.nc"):
            parts = f.stem.split("_")
            # RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc
            try:
                gpi = int(parts[6])
            except (IndexError, ValueError):
                continue
            gpi_files.setdefault(gpi, {})[sensor] = f
    gpis = sorted(gpi_files.keys())
    if not gpis:
        print(f"ERROR: no pp06 shards found under {PP06_YEAR_DIR}")
        sys.exit(1)
    return gpi_files, gpis


GPI_FILES, GPIS = build_index()
print(f"SignoffQC: site={SITE} year={YEAR} — {len(GPIS)} profiles "
      f"(GPI {GPIS[0]}..{GPIS[-1]})")


# == Daily index / noon-midnight ===============================================

def daily_index_of(gpi):
    """The 1-9 daily index for a GPI, read from any present shard's filename."""
    files = GPI_FILES.get(gpi, {})
    for f in files.values():
        parts = f.stem.split("_")
        try:
            return int(parts[7])
        except (IndexError, ValueError):
            pass
    return None


def profile_time_and_tag(gpi):
    """Return (local_peak_time, tag) where tag in {'MIDNIGHT','NOON',None}, using any
    present shard's time axis. Falls back to (None, None)."""
    files = GPI_FILES.get(gpi, {})
    for f in files.values():
        try:
            ds = xr.open_dataset(f)
            times = ds.time.values
            ds.close()
            if len(times) == 0:
                continue
            start = pd.to_datetime(times[0]).tz_localize("UTC").astimezone(OREGON_TZ)
            end = pd.to_datetime(times[-1]).tz_localize("UTC").astimezone(OREGON_TZ)
            peak = pd.to_datetime(times[len(times) // 2]).tz_localize("UTC").astimezone(OREGON_TZ)
            w0, w1 = start - timedelta(minutes=30), end + timedelta(minutes=30)
            midnight = start.replace(hour=0, minute=0, second=0, microsecond=0)
            noon = start.replace(hour=12, minute=0, second=0, microsecond=0)
            if w0 <= midnight <= w1:
                return peak, "MIDNIGHT"
            if w0 <= noon <= w1:
                return peak, "NOON"
            return peak, None
        except Exception:
            continue
    return None, None


def is_noon_or_midnight(gpi):
    # Authoritative: daily index 4 (midnight) or 9 (post-noon ~13:40). This governs whether
    # a missing LSD sensor is "expected" (off-index) or "missing" (on the noon/midnight profile).
    return daily_index_of(gpi) in (4, 9)


# == State table (one row per GPI) =============================================

STATE_COLUMNS = ["gpi", "visits"] + SENSORS


def default_state_for(gpi):
    """Compute the baseline (pre-user) state row for a GPI from what's present."""
    present = GPI_FILES.get(gpi, {})
    nm = is_noon_or_midnight(gpi)
    row = {"gpi": gpi, "visits": 0}
    for s in SENSORS:
        if s in present:
            row[s] = OK
        elif s in LSD_SENSORS and not nm:
            row[s] = NONE_EXP     # restricted sensor, non-noon/midnight → expected absence
        else:
            row[s] = NONE_MISS    # absent where it should have been present
    return row


def load_or_init_table():
    """Load the existing sign-off CSV (merge) or initialize a fresh table for all GPIs.
    With --reset, ignore (and overwrite) any existing CSV — a clean table."""
    table = {gpi: default_state_for(gpi) for gpi in GPIS}
    if ARGS.reset:
        print(f"--reset: starting a FRESH sign-off table (prior {SIGNOFF_CSV.name} will be overwritten).")
        return table
    if SIGNOFF_CSV.exists():
        prior = pd.read_csv(SIGNOFF_CSV)
        for _, r in prior.iterrows():
            gpi = int(r["gpi"])
            if gpi not in table:
                continue  # GPI no longer present (shouldn't happen for a fixed year)
            table[gpi]["visits"] = int(r.get("visits", 0))
            for s in SENSORS:
                prior_val = r.get(s)
                # Preserve a prior human Discard; otherwise trust the freshly-computed
                # presence state (data on disk is the source of truth for Ok/None).
                if prior_val == DISCARD and table[gpi][s] == OK:
                    table[gpi][s] = DISCARD
        print(f"Resumed from {SIGNOFF_CSV.name} ({len(prior)} rows).")
    else:
        print(f"New sign-off table → {SIGNOFF_CSV.name}")
    return table


def save_table(table):
    SIGNOFF_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = [table[g] for g in GPIS]
    pd.DataFrame(rows, columns=STATE_COLUMNS).to_csv(SIGNOFF_CSV, index=False)


TABLE = load_or_init_table()


# == GUI =======================================================================

cur = 0  # index into GPIS

fig = plt.figure(figsize=(22, 10.0))
mng = plt.get_current_fig_manager()
try:
    mng.window.wm_geometry("+30+10")
except Exception:
    pass

# Four charts across the top. Each is a base axis + extra twiny axes per sensor.
CHART_LEFTS = [0.05, 0.28, 0.51, 0.74]
CHART_W = 0.20
CHART_BOTTOM = 0.34
CHART_H = 0.52
chart_axes = []          # list of base axes
for left in CHART_LEFTS:
    ax = fig.add_axes([left, CHART_BOTTOM, CHART_W, CHART_H])
    chart_axes.append(ax)

show_sensor = {s: True for s in SENSORS}   # display toggles

# Twiny axes created for the extra sensors, tracked so we can DELETE them each redraw
# (ax.clear() alone leaves stale twins whose traces would persist — the "ghost trace" bug).
_twin_axes = []


def draw():
    """Render the four charts for the current GPI."""
    gpi = GPIS[cur]
    present = GPI_FILES.get(gpi, {})

    # Remove all twin axes from the previous draw, then clear the base axes.
    global _twin_axes
    for tax in _twin_axes:
        try:
            tax.remove()
        except Exception:
            pass
    _twin_axes = []
    for ax in chart_axes:
        ax.clear()

    for ci, ax in enumerate(chart_axes):
        ax.set_ylim(200, 0)
        ax.grid(True, alpha=0.3)
        if ci == 0:
            ax.set_ylabel("Depth (m)")
        sensors = CHART_SENSORS[ci]
        n_extra = 0
        for (sensor, color) in sensors:
            if not show_sensor[sensor] or sensor not in present:
                continue
            try:
                ds = xr.open_dataset(present[sensor])
                vals = ds[sensor].values
                depth = np.abs(ds["depth"].values)
                ds.close()
            except Exception:
                continue
            valid = ~(np.isnan(vals) | np.isnan(depth))
            if valid.sum() < 1:
                continue
            vals, depth = vals[valid], depth[valid]
            # First shown sensor uses the base axis; others get stacked twiny axes.
            if n_extra == 0:
                target = ax
            else:
                target = ax.twiny()
                _twin_axes.append(target)
            target.plot(vals, depth, "-", color=color, linewidth=1.0)
            if n_extra == 0:
                target.set_ylim(200, 0)
            # Fixed range (e.g. PAR) if configured, else autoscale to the data.
            if sensor in USE_FIXED_RANGE and sensor in FIXED_RANGE:
                target.set_xlim(*FIXED_RANGE[sensor])
            else:
                vmin, vmax = np.nanmin(vals), np.nanmax(vals)
                pad = (vmax - vmin) * 0.05 if vmax > vmin else 1.0
                target.set_xlim(vmin - pad, vmax + pad)
            target.set_xlabel(sensor, color=color, fontsize=9)
            target.tick_params(axis="x", labelcolor=color, labelsize=7)
            if n_extra > 0:
                target.xaxis.set_label_position("top")
                target.xaxis.tick_top()
                target.spines["top"].set_position(("outward", 28 * (n_extra - 1)))
            n_extra += 1
        if n_extra == 0:
            ax.text(0.5, 0.5, "(no shown data)", ha="center", va="center",
                    transform=ax.transAxes, color="gray", fontsize=9)

    # Title: local time + noon/midnight tag. The AUTHORITATIVE tag is the daily index
    # (4 = midnight, 9 = post-noon ~13:40 local) per project convention — the clock-window
    # test would miss index 9 since it's ~13:40, not local noon. Tag follows "local".
    peak, _ = profile_time_and_tag(gpi)
    di = daily_index_of(gpi)
    tag = {4: "midnight", 9: "noon"}.get(di)
    ttl = f"{SITE}  {YEAR}  |  GPI {gpi}  |  profile {cur+1}/{len(GPIS)}  |  daily {di}"
    if peak is not None:
        ttl += f"  |  {peak.strftime('%Y-%m-%d %H:%M')} local"
    if tag:
        ttl += f"  [{tag}]"
    ttl += f"  |  visits={TABLE[gpi]['visits']}"
    fig.suptitle(ttl, fontsize=14, fontweight="bold", y=0.97)

    refresh_state_buttons()
    fig.canvas.draw_idle()


# --- Sensor state buttons (11 tri-state) + display toggles --------------------

state_btn_axes = {}
state_btns = {}
toggle_btns = {}

# Lay the 11 sensor controls in a row near the bottom: each = [state button][toggle].
_n = len(SENSORS)
_slot_w = 0.085
_row_left = 0.03
for i, sensor in enumerate(SENSORS):
    x = _row_left + i * _slot_w
    ax_state = fig.add_axes([x, 0.16, _slot_w - 0.008, 0.05])
    b = Button(ax_state, sensor, color="#eeeeee")
    b.label.set_fontsize(7)
    state_btn_axes[sensor] = ax_state
    state_btns[sensor] = b

    ax_tog = fig.add_axes([x, 0.10, _slot_w - 0.008, 0.045])
    tog = Button(ax_tog, "shown", color="#d0e8ff")
    tog.label.set_fontsize(7)
    toggle_btns[sensor] = tog


def refresh_state_buttons():
    gpi = GPIS[cur]
    for sensor in SENSORS:
        st = TABLE[gpi][sensor]
        b = state_btns[sensor]
        col = STATE_COLORS.get(st, "#eeeeee")
        # Set the button's RESTING + HOVER color (not just facecolor); matplotlib Button
        # repaints from b.color / b.hovercolor on mouse enter/leave, so facecolor alone
        # would revert when the cursor moves off. Set both so the state color persists.
        b.color = col
        b.hovercolor = col
        b.ax.set_facecolor(col)
        short = {OK: "Ok", NONE_EXP: "None(exp)", NONE_MISS: "None(miss)", DISCARD: "DISCARD"}[st]
        b.label.set_text(f"{sensor}\n{short}")
        tog = toggle_btns[sensor]
        tog.label.set_text(f"{sensor}\n{'shown' if show_sensor[sensor] else 'hidden'}")
        tcol = "#d0e8ff" if show_sensor[sensor] else "#f0f0f0"
        tog.color = tcol
        tog.hovercolor = tcol
        tog.ax.set_facecolor(tcol)


def make_state_cb(sensor):
    def cb(event):
        gpi = GPIS[cur]
        st = TABLE[gpi][sensor]
        # Only Ok<->Discard toggles; None states do nothing.
        if st == OK:
            TABLE[gpi][sensor] = DISCARD
        elif st == DISCARD:
            TABLE[gpi][sensor] = OK
        else:
            return
        save_table(TABLE)
        refresh_state_buttons()
        fig.canvas.draw_idle()
    return cb


def make_toggle_cb(sensor):
    def cb(event):
        show_sensor[sensor] = not show_sensor[sensor]
        draw()
    return cb


for sensor in SENSORS:
    state_btns[sensor].on_clicked(make_state_cb(sensor))
    toggle_btns[sensor].on_clicked(make_toggle_cb(sensor))


# --- Navigation ---------------------------------------------------------------

def visit_current():
    """Increment the visit counter for the current GPI and persist."""
    gpi = GPIS[cur]
    TABLE[gpi]["visits"] = int(TABLE[gpi]["visits"]) + 1
    save_table(TABLE)


def go_to_index(new_idx):
    global cur
    new_idx = max(0, min(len(GPIS) - 1, new_idx))
    cur = new_idx
    visit_current()
    draw()


ax_back = fig.add_axes([0.03, 0.03, 0.06, 0.05])
ax_adv = fig.add_axes([0.10, 0.03, 0.06, 0.05])
btn_back = Button(ax_back, "< Back")
btn_adv = Button(ax_adv, "Advance >")
btn_back.on_clicked(lambda e: go_to_index(cur - 1))
btn_adv.on_clicked(lambda e: go_to_index(cur + 1))

# Julian-day Go To
fig.text(0.20, 0.055, "Julian day:", fontsize=9)
ax_jday = fig.add_axes([0.26, 0.03, 0.05, 0.05])
tb_jday = TextBox(ax_jday, "", initial="")
ax_goto = fig.add_axes([0.32, 0.03, 0.05, 0.05])
btn_goto = Button(ax_goto, "Go To")


def jday_of_gpi(gpi):
    files = GPI_FILES.get(gpi, {})
    for f in files.values():
        parts = f.stem.split("_")
        try:
            return int(parts[5])
        except (IndexError, ValueError):
            pass
    return None


def on_goto(event):
    txt = tb_jday.text.strip()
    if not txt:
        return
    try:
        target = int(txt)
    except ValueError:
        return
    # Find the first GPI whose Julian day >= target.
    best = None
    for i, gpi in enumerate(GPIS):
        jd = jday_of_gpi(gpi)
        if jd is not None and jd >= target:
            best = i
            break
    if best is not None:
        go_to_index(best)


btn_goto.on_clicked(on_goto)


# Initial visit + draw
visit_current()
draw()
plt.show()
