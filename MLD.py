"""
MLD.py — interactive MLD (mixed-layer depth) annotator for the training-dataset workflow.

Standalone TkAgg GUI (matplotlib) in the VisQCInspector.py lineage. Reads a site's BLESSED
candidate list (repo folder ~/argosy/mld_candidates/), shows one sensor's profile at a time,
and lets a human place an MLD by clicking the chart. Labels are written one row per
(gpi, sensor, who) to a per-who CSV in the data tree. Full design: MLDAnnotationPlan.md.

Key behaviors
  - Active sensor: temperature (default) / salinity / density / dissolvedoxygen. Only the
    active sensor's trace is shown; only one MLD is recorded per interaction. Density trace
    is the pp06 `density` shard (potential density deferred).
  - Display State 1 — filter: file data (default) OR file data with the active filter applied.
  - Display State 2 — raw overlay (only when a filter is applied): also draw the raw file data
    faintly in light blue behind the black filtered trace, or not.
  - Filters: None / savgol / adaptive_savgol_std / adaptive_savgol_mad, with sliders.
  - Advance Mode 1 (default, auto): click records depth for (gpi, sensor) and advances.
  - Advance Mode 2 (manual): click places a large blue dot (re-clickable); <Advance> commits;
    <Advance> with no point saves "no MLD recorded" and advances.
  - Navigation: prev/next, plus Forward-to-Null / Reverse-to-Null (jump to the next/previous
    candidate with no label for the ACTIVE sensor by the CURRENT who).
  - Session settings (active sensor, filter, sliders, display states, advance mode) persist
    across advances. who is fixed at launch by --who (no UI control).

Recorded per label: continuous click depth (interpolated), raw value AND filtered value at
that depth, sensor, who, filter key + structured params, no_mld_recorded flag, reviewed_at.

Display notes: depth axis runs 0 m (top) to 100 m (bottom). Returning to an already-labeled
(gpi, sensor) shows the committed MLD as a green dashed line plus a green dot on the trace, so
the User can see it is labeled and where.

Usage:
    python MLD.py                        # site sb, block 5, who C (Chuck), start at first
    python MLD.py --site oo --who R      # Rob labeling Oregon Offshore
    python MLD.py --site oo --year 2018  # start at first 2018 candidate, continue past
    python MLD.py --block-days 7         # use the block07 candidate list

Requires TkAgg + python3-tk (interactive; needs a display). See operational-recipes §3.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib
matplotlib.use("TkAgg")  # interactive backend; must precede pyplot import
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, CheckButtons, Slider

from scipy.signal import savgol_filter

# Repo root importable so `import ooipaths` works.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# ── Constants ─────────────────────────────────────────────────────────────────

MLD_SENSORS = ("temperature", "salinity", "density", "dissolvedoxygen")
SENSOR_LABELS = {
    "temperature": "Temperature (°C)",
    "salinity": "Salinity (PSU)",
    "density": "Density (kg/m³)",
    "dissolvedoxygen": "Dissolved O₂ (µmol/kg)",
}
SENSOR_COLORS = {
    "temperature": "red", "salinity": "blue",
    "density": "purple", "dissolvedoxygen": "green",
}
RADIO_TO_SENSOR = {"Temp": "temperature", "Sal": "salinity",
                   "Density": "density", "DO": "dissolvedoxygen"}

WHO_CODES = ("A", "C", "R", "X")  # C = Chuck (default), R = Rob

FILTERS = ("None", "savgol", "adaptive_savgol_std", "adaptive_savgol_mad")

MAX_DEPTH = 100.0  # depth-axis bottom for the annotation view (0 m top .. 100 m bottom)

LABEL_COLUMNS = [
    "site", "gpi", "timestamp", "sensor",
    "mld_depth", "value_raw", "value_filtered",
    "who", "filter_key", "filter_p1", "filter_p2",
    "no_mld_recorded", "reviewed_at",
]


# ── Candidate + label file locations ────────────────────────────────────────────

def blessed_candidates_path(site, block_days):
    return op.ARGOSY_ROOT / "mld_candidates" / f"mld_candidates_{site}_block{block_days:02d}.csv"


def labels_path(site, block_days, who):
    """Per-who label CSV in the data tree; block tag ties it to the candidate set."""
    return (op.metadata_dir(site, "annotations")
            / f"mld_labels_{site}_block{block_days:02d}_{who}.csv")


# ── Data loading ────────────────────────────────────────────────────────────────

def load_candidates(site, block_days, year=None):
    """Load the blessed candidate list; keep only rows with a selected gpi.

    Returns a DataFrame ordered by timestamp. `year` sets the START index (not a filter):
    the caller begins at the first candidate whose timestamp year >= year.
    """
    path = blessed_candidates_path(site, block_days)
    if not path.exists():
        raise SystemExit(
            f"Blessed candidate file not found: {path}\n"
            f"Generate + bless it first:  python PreSelectProfiles.py "
            f"--site {site} --block-days {block_days} ; ... --bless")
    df = pd.read_csv(path)
    df = df[df["gpi"].notna()].copy()
    df["gpi"] = df["gpi"].astype(int)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def build_gpi_file_index(site):
    """Map gpi -> {sensor: Path} across all pp06 years for the four MLD sensors."""
    idx = {}
    pp06_base = op.postproc_base(site) / "pp06"
    if not pp06_base.exists():
        return idx
    for year_dir in sorted(p for p in pp06_base.iterdir() if p.is_dir() and p.name.isdigit()):
        for sensor in MLD_SENSORS:
            for f in year_dir.glob(f"RCA_{site}_sp_{sensor}_*.nc"):
                parts = f.stem.split("_")
                try:
                    gpi = int(parts[6])
                except (IndexError, ValueError):
                    continue
                idx.setdefault(gpi, {})[sensor] = f
    return idx


def load_profile(gpi_files, gpi, sensor):
    """Load one sensor profile: returns (depth, values) sorted by depth, NaNs dropped.

    depth is positive-down (abs), matching VisQCInspector convention. (None, None) if
    the file is absent or unreadable.
    """
    entry = gpi_files.get(gpi)
    if not entry or sensor not in entry:
        return None, None
    try:
        ds = xr.open_dataset(entry[sensor])
        vals = ds[sensor].values
        depth = np.abs(ds["depth"].values)
        ds.close()
    except Exception:
        return None, None
    valid = ~(np.isnan(vals) | np.isnan(depth))
    vals, depth = vals[valid], depth[valid]
    order = np.argsort(depth)
    return depth[order], vals[order]


# ── Filters ──────────────────────────────────────────────────────────────────────

def _odd(n):
    n = int(round(n))
    return n if n % 2 == 1 else n + 1


def apply_filter(depth, vals, filter_key, p1, p2):
    """Return a filtered copy of `vals` on the same depth grid.

    p1/p2 meanings:
      savgol                : p1 = window length (odd), p2 = polyorder (1..5)
      adaptive_savgol_std   : p1 = base window (odd),   p2 = adaptivity (0..1)
      adaptive_savgol_mad   : p1 = base window (odd),   p2 = adaptivity (0..1)
    `None` returns vals unchanged. Any filter failure falls back to the raw values
    (never crashes the caller). Guards short/degenerate profiles.
    """
    if filter_key == "None" or vals is None or len(vals) < 5:
        return vals
    try:
        return _apply_filter_impl(vals, filter_key, p1, p2)
    except Exception:
        # A degenerate profile or bad param combo should never kill the interaction;
        # fall back to the unfiltered trace.
        return vals


def _apply_filter_impl(vals, filter_key, p1, p2):
    n = len(vals)
    win = _odd(p1)
    win = max(3, min(win, n if n % 2 == 1 else n - 1))
    poly = int(round(p2)) if filter_key == "savgol" else 2
    poly = max(1, min(poly, win - 1))

    if filter_key == "savgol":
        return savgol_filter(vals, win, poly)

    # Adaptive: blend a light (base) and heavy (wide) savgol per-point by local roughness.
    heavy_win = _odd(min(win * 3, n if n % 2 == 1 else n - 1))
    heavy_win = max(win, heavy_win)
    light = savgol_filter(vals, win, min(2, win - 1))
    heavy = savgol_filter(vals, heavy_win, min(2, heavy_win - 1))

    # Local roughness in a rolling window (std or MAD of the residual from `light`).
    resid = vals - light
    half = max(1, win // 2)
    rough = np.zeros(n)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        seg = resid[lo:hi]
        if filter_key == "adaptive_savgol_mad":
            med = np.median(seg)
            rough[i] = np.median(np.abs(seg - med)) * 1.4826
        else:  # std
            rough[i] = np.std(seg)

    # Normalize roughness to a 0..1 weight, THEN scale by adaptivity p2 in [0,1]:
    #   p2 = 0  -> weight 0 everywhere (pure light/base trace)
    #   p2 = 1  -> weight tracks normalized local roughness (full adaptive behavior)
    # (Previously p2 ran 1..5 and saturated the weight to ~1 everywhere, making the
    # adaptivity control a no-op — see slider range in _build_ui.)
    rmax = np.max(rough) if np.max(rough) > 0 else 1.0
    w = np.clip((rough / rmax) * float(p2), 0.0, 1.0)
    return (1.0 - w) * light + w * heavy


# ── Annotator ──────────────────────────────────────────────────────────────────

class MLDAnnotator:
    def __init__(self, site, block_days, who, start_year=None):
        self.site = site
        self.block_days = block_days
        self.who = who
        self.candidates = load_candidates(site, block_days, start_year)
        if self.candidates.empty:
            raise SystemExit(f"No candidate profiles with a selected gpi for site {site}.")
        self.gpi_files = build_gpi_file_index(site)
        self.labels_path = labels_path(site, block_days, who)
        self.labels = self._load_labels()

        # Session state (sticky across advances)
        self.active_sensor = "temperature"
        self.filter_key = "None"
        self.p1 = 11.0   # savgol window / adaptive base window
        self.p2 = 2.0    # savgol polyorder / adaptive adaptivity
        self.show_raw_overlay = True
        self.auto_advance = True  # Mode 1 default

        # Pending pick (Mode 2): (depth, value_raw, value_filtered) or None
        self.pending = None

        # Start index
        self.idx = self._start_index(start_year)

        self._build_ui()
        self.draw()

    # -- labels I/O --
    def _load_labels(self):
        if self.labels_path.exists():
            df = pd.read_csv(self.labels_path)
            for c in LABEL_COLUMNS:
                if c not in df.columns:
                    df[c] = np.nan
            return df[LABEL_COLUMNS]
        return pd.DataFrame(columns=LABEL_COLUMNS)

    def _save_labels(self):
        self.labels_path.parent.mkdir(parents=True, exist_ok=True)
        self.labels.to_csv(self.labels_path, index=False)

    def _has_label(self, gpi, sensor):
        if self.labels.empty:
            return False
        m = (self.labels["gpi"] == gpi) & (self.labels["sensor"] == sensor)
        return bool(m.any())

    def _start_index(self, start_year):
        if start_year is None:
            return 0
        yrs = self.candidates["timestamp"].dt.year.values
        hits = np.where(yrs >= int(start_year))[0]
        return int(hits[0]) if len(hits) else 0

    # -- current profile helpers --
    def _row(self):
        return self.candidates.iloc[self.idx]

    def _current_gpi(self):
        return int(self._row()["gpi"])

    def _load_active(self):
        """Return (depth, raw, filtered) for the active sensor at the current profile."""
        depth, raw = load_profile(self.gpi_files, self._current_gpi(), self.active_sensor)
        if depth is None:
            return None, None, None
        filt = apply_filter(depth, raw, self.filter_key, self.p1, self.p2)
        return depth, raw, filt

    # ── UI construction ──
    def _build_ui(self):
        self.fig = plt.figure(figsize=(14, 9))
        try:
            self.fig.canvas.manager.window.wm_geometry("+40+20")
        except Exception:
            pass

        self.ax = self.fig.add_axes([0.30, 0.30, 0.66, 0.62])

        # Sensor selector
        ax_sensor = self.fig.add_axes([0.02, 0.72, 0.20, 0.18])
        ax_sensor.set_title("Active sensor", fontsize=9)
        self.radio_sensor = RadioButtons(ax_sensor, ("Temp", "Sal", "Density", "DO"), active=0)
        self.radio_sensor.on_clicked(self._on_sensor)

        # Filter selector
        ax_filter = self.fig.add_axes([0.02, 0.50, 0.20, 0.20])
        ax_filter.set_title("Filter", fontsize=9)
        self.radio_filter = RadioButtons(ax_filter, FILTERS, active=0)
        self.radio_filter.on_clicked(self._on_filter)

        # Display-state toggles: raw overlay + advance mode
        ax_chk = self.fig.add_axes([0.02, 0.38, 0.20, 0.10])
        self.chk = CheckButtons(ax_chk, ["Raw overlay", "Auto-advance"],
                                [self.show_raw_overlay, self.auto_advance])
        self.chk.on_clicked(self._on_check)

        # Sliders for filter params. p2's meaning (and range) depends on the filter:
        #   savgol            -> polyorder, integer 1..5
        #   adaptive_savgol_* -> adaptivity, 0..1
        # _sync_slider_ranges() sets p2's range to match the active filter.
        ax_s1 = self.fig.add_axes([0.32, 0.20, 0.55, 0.03])
        ax_s2 = self.fig.add_axes([0.32, 0.15, 0.55, 0.03])
        self.slider_p1 = Slider(ax_s1, "window", 3, 51, valinit=self.p1, valstep=2)
        self.slider_p2 = Slider(ax_s2, "poly / adapt", 1, 5, valinit=self.p2)
        self.slider_p1.on_changed(self._on_slider)
        self.slider_p2.on_changed(self._on_slider)
        self._sync_slider_ranges()

        # Navigation + advance buttons
        def _btn(x, w, label):
            a = self.fig.add_axes([x, 0.05, w, 0.05])
            return Button(a, label)

        self.btn_prev = _btn(0.02, 0.07, "◀ Prev")
        self.btn_next = _btn(0.10, 0.07, "Next ▶")
        self.btn_rnull = _btn(0.19, 0.11, "◀ Rev-to-Null")
        self.btn_fnull = _btn(0.31, 0.11, "Fwd-to-Null ▶")
        self.btn_advance = _btn(0.44, 0.10, "Advance")
        self.btn_clear = _btn(0.55, 0.09, "Clear pick")

        self.btn_prev.on_clicked(lambda e: self._goto(self.idx - 1))
        self.btn_next.on_clicked(lambda e: self._goto(self.idx + 1))
        self.btn_rnull.on_clicked(lambda e: self._to_null(-1))
        self.btn_fnull.on_clicked(lambda e: self._to_null(+1))
        self.btn_advance.on_clicked(self._on_advance)
        self.btn_clear.on_clicked(self._on_clear)

        self.status = self.fig.text(0.02, 0.01, "", fontsize=8, color="#333")

        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    # ── Drawing ──
    def draw(self):
        self.ax.clear()
        depth, raw, filt = self._load_active()
        row = self._row()
        gpi = int(row["gpi"])
        ts = pd.Timestamp(row["timestamp"]).strftime("%Y-%m-%d")

        if depth is None or len(depth) == 0:
            self.ax.text(0.5, 0.5, f"No {self.active_sensor} data for GPI {gpi}",
                         ha="center", va="center", transform=self.ax.transAxes)
        else:
            color = SENSOR_COLORS[self.active_sensor]
            if self.filter_key == "None":
                self.ax.plot(raw, depth, color=color, lw=1.0)
            else:
                if self.show_raw_overlay:
                    self.ax.plot(raw, depth, color="lightblue", lw=1.0, zorder=1)
                self.ax.plot(filt, depth, color="black", lw=1.2, zorder=2)
            self.ax.set_xlabel(SENSOR_LABELS[self.active_sensor], color=color)

        self.ax.set_ylim(MAX_DEPTH, 0)
        self.ax.set_ylabel("Depth (m)")
        self.ax.grid(True, alpha=0.3)

        # Existing committed label for this (gpi, sensor)? Draw a green dashed line at the
        # recorded depth AND a green dot on the displayed trace, so a returning User can see
        # the profile has been labeled and where.
        if self._has_label(gpi, self.active_sensor):
            r = self.labels[(self.labels["gpi"] == gpi)
                            & (self.labels["sensor"] == self.active_sensor)].iloc[-1]
            if not bool(r.get("no_mld_recorded", False)) and pd.notna(r.get("mld_depth")):
                mld_d = float(r["mld_depth"])
                self.ax.axhline(mld_d, color="green", lw=1.4, ls="--", zorder=3)
                if depth is not None and len(depth) > 0:
                    trace = filt if (self.filter_key != "None" and filt is not None) else raw
                    xval = float(np.interp(mld_d, depth, trace))
                    self.ax.plot([xval], [mld_d], "o", color="green", markersize=6, zorder=4)

        # Pending (Mode-2) pick as a blue dot
        if self.pending is not None:
            d, vr, vf = self.pending
            xval = vf if (self.filter_key != "None") else vr
            self.ax.plot([xval], [d], "o", color="blue", markersize=6, zorder=5)

        labeled = "LABELED" if self._has_label(gpi, self.active_sensor) else "unlabeled"
        mode = "AUTO" if self.auto_advance else "MANUAL"
        self.fig.suptitle(
            f"MLD [{self.site}/{self.who}]  GPI {gpi}  {ts}  "
            f"[{self.idx + 1}/{len(self.candidates)}]  |  {self.active_sensor} ({labeled})  "
            f"|  filter={self.filter_key}  |  {mode}",
            fontsize=11, fontweight="bold")
        self.fig.canvas.draw_idle()

    def _set_status(self, msg):
        self.status.set_text(msg)
        self.fig.canvas.draw_idle()

    # ── Interpolation of a click depth to raw + filtered values ──
    def _values_at(self, depth, raw, filt, click_depth):
        if depth is None or len(depth) == 0:
            return np.nan, np.nan
        vr = float(np.interp(click_depth, depth, raw))
        vf = float(np.interp(click_depth, depth, filt)) if filt is not None else vr
        return vr, vf

    # ── Event handlers ──
    def _on_sensor(self, label):
        self.active_sensor = RADIO_TO_SENSOR[label]
        self.pending = None
        self.draw()

    def _on_filter(self, label):
        self.filter_key = label
        self._sync_slider_ranges()
        self.draw()

    def _sync_slider_ranges(self):
        """Re-range the p2 slider to match the active filter's parameter.

        savgol -> polyorder in [1, 5]; adaptive -> adaptivity in [0, 1]. Adjusts the
        slider bounds, its axis, its step, and reseats self.p2 into the valid range so
        the adaptivity control is actually effective (p2 saturated at >=1 previously).
        """
        s2 = self.slider_p2
        if self.filter_key in ("adaptive_savgol_std", "adaptive_savgol_mad"):
            lo, hi, default, step, label = 0.0, 1.0, 0.5, None, "adaptivity"
        else:  # savgol (or None; harmless when no filter shown)
            lo, hi, default, step, label = 1.0, 5.0, 2.0, 1.0, "polyorder"
        s2.valmin, s2.valmax = lo, hi
        s2.valstep = step
        s2.ax.set_xlim(lo, hi)
        s2.label.set_text(label)
        # Clamp/seat current value into the new range.
        newval = min(max(self.p2, lo), hi)
        if not (lo <= self.p2 <= hi):
            newval = default
        s2.set_val(newval)   # triggers _on_slider -> updates self.p2

    def _on_check(self, label):
        if label == "Raw overlay":
            self.show_raw_overlay = not self.show_raw_overlay
        elif label == "Auto-advance":
            self.auto_advance = not self.auto_advance
        self.draw()

    def _on_slider(self, _val):
        self.p1 = self.slider_p1.val
        self.p2 = self.slider_p2.val
        self.draw()

    def _on_click(self, event):
        if event.inaxes is not self.ax:
            return
        if event.ydata is None:
            return
        click_depth = float(event.ydata)
        depth, raw, filt = self._load_active()
        if depth is None or len(depth) == 0:
            # No trace to pick against — don't record a junk label (NaN values).
            self._set_status("no data for this sensor/profile — use Advance to skip "
                             "(records 'no MLD') or switch sensor")
            return
        vr, vf = self._values_at(depth, raw, filt, click_depth)

        if self.auto_advance:
            # Mode 1: record immediately, then advance.
            self._record(click_depth, vr, vf, no_mld=False)
            self._advance_after_commit()
        else:
            # Mode 2: stage the pick (re-clickable); commit on Advance.
            self.pending = (click_depth, vr, vf)
            self._set_status(f"pending pick @ {click_depth:.1f} m "
                             f"(raw={vr:.3f}, filt={vf:.3f}) — press Advance to commit")
            self.draw()

    def _on_clear(self, _e):
        self.pending = None
        self._set_status("pick cleared")
        self.draw()

    def _on_advance(self, _e):
        # Mode 2 commit; also usable in Mode 1 to advance without a pick.
        if self.pending is not None:
            d, vr, vf = self.pending
            self._record(d, vr, vf, no_mld=False)
        else:
            self._record(np.nan, np.nan, np.nan, no_mld=True)
        self._advance_after_commit()

    # ── Recording ──
    def _record(self, depth, value_raw, value_filtered, no_mld):
        gpi = self._current_gpi()
        row = self._row()
        p1 = "" if self.filter_key == "None" else round(float(self.p1), 3)
        p2 = "" if self.filter_key == "None" else round(float(self.p2), 3)
        new = {
            "site": self.site,
            "gpi": gpi,
            "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
            "sensor": self.active_sensor,
            "mld_depth": "" if no_mld else round(float(depth), 3),
            "value_raw": "" if no_mld else round(float(value_raw), 4),
            "value_filtered": "" if no_mld else round(float(value_filtered), 4),
            "who": self.who,
            "filter_key": self.filter_key,
            "filter_p1": p1,
            "filter_p2": p2,
            "no_mld_recorded": bool(no_mld),
            "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        # Overwrite any prior (gpi, sensor, who) row.
        if not self.labels.empty:
            keep = ~((self.labels["gpi"] == gpi)
                     & (self.labels["sensor"] == self.active_sensor)
                     & (self.labels["who"] == self.who))
            self.labels = self.labels[keep]
        self.labels = pd.concat([self.labels, pd.DataFrame([new])], ignore_index=True)
        self.labels = self.labels[LABEL_COLUMNS]
        self._save_labels()
        tag = "no-MLD" if no_mld else f"{depth:.1f} m"
        self._set_status(f"saved {self.active_sensor} {tag} for GPI {gpi} -> {self.labels_path.name}")

    def _advance_after_commit(self):
        self.pending = None
        if self.idx < len(self.candidates) - 1:
            self.idx += 1
        self.draw()

    # ── Navigation ──
    def _goto(self, new_idx):
        self.pending = None
        self.idx = max(0, min(new_idx, len(self.candidates) - 1))
        self.draw()

    def _to_null(self, direction):
        """Jump to the next/previous candidate with no label for the active sensor+who."""
        n = len(self.candidates)
        i = self.idx + direction
        while 0 <= i < n:
            gpi = int(self.candidates.iloc[i]["gpi"])
            if not self._has_label(gpi, self.active_sensor):
                self._goto(i)
                self._set_status(f"jumped to unlabeled {self.active_sensor} (idx {i + 1})")
                return
            i += direction
        self._set_status(f"no unlabeled {self.active_sensor} profiles in that direction")

    def run(self):
        plt.show()


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Interactive MLD annotator.")
    ap.add_argument("--site", choices=op.SITES, default="sb", help="Site (default sb).")
    ap.add_argument("--block-days", type=int, default=5,
                    help="Block width of the candidate list to load (default 5).")
    ap.add_argument("--who", choices=WHO_CODES, default="C",
                    help="Labeler identity, fixed for the session (default C = Chuck).")
    ap.add_argument("--year", type=int, default=None,
                    help="Start at the first candidate in this year (continues past it).")
    args = ap.parse_args()

    annot = MLDAnnotator(args.site, args.block_days, args.who, start_year=args.year)
    print(f"MLD annotator — site={args.site}, who={args.who}, block_days={args.block_days}, "
          f"candidates={len(annot.candidates)}, labels_file={annot.labels_path}")
    annot.run()


if __name__ == "__main__":
    main()
