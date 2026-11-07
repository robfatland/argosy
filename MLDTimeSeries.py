"""
MLDTimeSeries.py -- interactive time-series viewer for human-labeled MLD.

Two stacked charts sharing one time axis, with sliders to pan / zoom the time range:
  UPPER : MLD depth (m, axis inverted) for temperature (red), salinity (green), DO (blue)
  LOWER : the sensor VALUE at the MLD -- T at MLD (left axis, red), S at MLD (right axis,
          green), DO at MLD (second right axis, blue)

Data come from the label CSVs written by MLD.py (value_raw = sensor value at the labeled depth):
  SCIENCE  (dense month blocks)  ~/ooi/<site>/metadata/annotations/mld_labels_<site>_science_<who>.csv
           drawn as filled CIRCLES joined by lines
  TRAINING (1 profile in ~45)    ~/ooi/<site>/metadata/annotations/mld_labels_<site>_block05_<who>.csv
           drawn as TRIANGLES (markers only, no lines), toggled by the "Training" checkbox.
           Training rows whose (gpi, sensor) are already in the science file are skipped
           (the science set was seeded from training, so they would just overlap).
Spec: MLDAnnotationPlan.md section 4.

Controls (bottom of window)
  start coarse : global window start over 2014-2027 (continuous; spans year boundaries)
  start fine   : offset in days ADDED to the coarse start (0 .. FINE_MAX_DAYS)
                 window start = coarse + fine
  width (d)    : window width in days (0.25 .. 400)
  Checkboxes:
    Adaptive y   : ON (default) = y axes re-fit to the visible window on every pan/zoom;
                   OFF = fixed "wide" limits (full range of all loaded labels, all times) so
                   charts at any start time are directly comparable
    Training (^) : show / hide training labels
    Faux No-MLD  : OFF (default) = a profile labeled "No MLD" for a sensor is shown as an X
                   near the TOP of the lower chart (one row per sensor).
                   ON = read that profile's pp06 shard, take its SHALLOWEST valid sample, and
                   plot it as an OPEN marker (circle for science, triangle for training) in
                   that sensor's series (the science line connects through it)
    Local time   : OFF (default) = time axis and day gridlines in UTC;
                   ON = Pacific local time (America/Los_Angeles). Gridlines fall at midnight
                   of the displayed zone. The window keeps the same instant when toggled.
  Profiles flagged unusable (xud) are never plotted.

Lines are NOT drawn between successive science points more than 1 day apart.

Usage:
    python ~/argosy/MLDTimeSeries.py
    python ~/argosy/MLDTimeSeries.py --site sb --start 2024-08-01 --end 2024-08-31
    python ~/argosy/MLDTimeSeries.py --local --size 1500x850
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")  # interactive backend; must precede pyplot import
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons, Slider

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op  # noqa: E402
import MLD  # noqa: E402  (reuse build_gpi_file_index, load_profile, label path helpers)

SENSORS = ("temperature", "salinity", "dissolvedoxygen")
COLORS = {"temperature": "red", "salinity": "green", "dissolvedoxygen": "blue"}
SHORT = {"temperature": "T", "salinity": "S", "dissolvedoxygen": "DO"}
X_ROW = {"temperature": 0.97, "salinity": 0.93, "dissolvedoxygen": 0.89}  # axes-fraction rows
GAP_DAYS = 1.0          # no connector line across a gap longer than this
WIDTH_MAX_DAYS = 400.0
FINE_MAX_DAYS = 45.0    # "start fine" offset range; must exceed one coarse-slider pixel step
COARSE_START = pd.Timestamp("2014-01-01")
COARSE_END = pd.Timestamp("2027-12-31")
LOCAL_TZ = "America/Los_Angeles"
CHECK_LABELS = ["Adaptive y", "Training (^)", "Faux No-MLD", "Local time"]


def _true(s):
    return s.astype(str).str.strip().str.lower().eq("true")


def load_labels(path):
    """Read a label CSV. `time` is UTC (naive); `time_loc` is Pacific local (naive)."""
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["timestamp"], format="ISO8601")
    df["time_loc"] = (df["time"].dt.tz_localize("UTC")
                      .dt.tz_convert(LOCAL_TZ).dt.tz_localize(None))
    df = df[df["sensor"].isin(SENSORS)]
    df = df[~_true(df["xud_recorded"])]                 # unusable data: never plotted
    df["nomld"] = _true(df["no_mld_recorded"])
    df["mld"] = pd.to_numeric(df["mld_depth"], errors="coerce")
    df["val"] = pd.to_numeric(df["value_raw"], errors="coerce")
    return df.sort_values("time").reset_index(drop=True)


def split_by_sensor(df):
    """Per-sensor arrays. Times are matplotlib date numbers: t/t_no (UTC), tl/tl_no (local)."""
    out = {}
    for s in SENSORS:
        g = df[df["sensor"] == s]
        real = g[(~g["nomld"]) & g["mld"].notna() & g["val"].notna()]
        nom = g[g["nomld"]]
        out[s] = {
            "t": mdates.date2num(real["time"].values),
            "tl": mdates.date2num(real["time_loc"].values),
            "mld": real["mld"].values,
            "val": real["val"].values,
            "t_no": mdates.date2num(nom["time"].values),
            "tl_no": mdates.date2num(nom["time_loc"].values),
            "gpi_no": nom["gpi"].values,
        }
    return out


def with_gaps(x, y, gap=GAP_DAYS):
    """Sort by x and insert NaN where successive x differ by more than `gap` days,
    so matplotlib breaks the connector line there."""
    if len(x) == 0:
        return x, y
    o = np.argsort(x)
    x, y = x[o], y[o]
    brk = np.where(np.diff(x) > gap)[0] + 1
    return np.insert(x, brk, np.nan), np.insert(y, brk, np.nan)


class Viewer:
    def __init__(self, site, who, sci, tr, start, end, local, size=None):
        self.site, self.who, self.local = site, who, local
        self.mode = "X"             # "X" (default) or "O" (= Faux No-MLD checked)
        self.show_training = tr is not None
        self.adaptive = True
        self._shallow = {}          # (gpi, sensor) -> shallowest raw value (cache)
        self._gpi_files = None      # built lazily on first Faux No-MLD
        self.lower_artists, self.upper_artists = [], []

        self.d = split_by_sensor(sci)
        self.dt = split_by_sensor(tr) if tr is not None else None

        self.c0, self.c1 = mdates.date2num(COARSE_START), mdates.date2num(COARSE_END)
        self.start = mdates.date2num(start)      # = coarse + fine (displayed time zone)
        w0 = mdates.date2num(end) - self.start

        # --- figure + axes ---
        self.fig = plt.figure(figsize=(15.6, 9))
        self._fit_to_screen(size)
        self.ax_up = self.fig.add_axes([0.08, 0.60, 0.74, 0.32])
        self.ax_lo = self.fig.add_axes([0.08, 0.32, 0.74, 0.26], sharex=self.ax_up)
        self.ax_s = self.ax_lo.twinx()
        self.ax_do = self.ax_lo.twinx()
        self.ax_do.spines["right"].set_position(("axes", 1.10))
        self.ax_by = {"temperature": self.ax_lo, "salinity": self.ax_s,
                      "dissolvedoxygen": self.ax_do}
        self.ax_up.tick_params(labelbottom=False)
        self.ax_up.invert_yaxis()
        self.ax_up.set_ylabel("MLD (m)")
        self.ax_up.grid(alpha=0.3)
        labels = {"temperature": "T at MLD (C)", "salinity": "S at MLD (PSU)",
                  "dissolvedoxygen": "DO at MLD (umol/kg)"}
        for s, ax in self.ax_by.items():
            ax.set_ylabel(labels[s], color=COLORS[s])
            ax.tick_params(axis="y", colors=COLORS[s])
        self.ax_lo.grid(alpha=0.3)
        loc = mdates.AutoDateLocator()
        self.ax_lo.xaxis.set_major_locator(loc)
        self.ax_lo.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))

        # --- sliders (left) + one compact checkbox panel (right of the sliders) ---
        a_c = self.fig.add_axes([0.12, 0.20, 0.50, 0.03])
        a_f = self.fig.add_axes([0.12, 0.145, 0.50, 0.03])
        a_w = self.fig.add_axes([0.12, 0.09, 0.50, 0.03])
        self.sl_coarse = Slider(a_c, "start coarse", self.c0, self.c1,
                                valinit=float(np.clip(self.start, self.c0, self.c1)))
        self.sl_fine = Slider(a_f, "start fine (+d)", 0.0, FINE_MAX_DAYS, valinit=0.0)
        self.sl_width = Slider(a_w, "width (d)", 0.25, WIDTH_MAX_DAYS,
                               valinit=float(np.clip(w0, 0.25, WIDTH_MAX_DAYS)))
        for sl in (self.sl_coarse, self.sl_fine, self.sl_width):
            sl.on_changed(self._on_time)

        ac = self.fig.add_axes([0.745, 0.075, 0.115, 0.165])
        self.chk = CheckButtons(ac, CHECK_LABELS,
                                [self.adaptive, self.show_training, False, self.local])
        for t in self.chk.labels:
            t.set_fontsize(8)
        self.chk.on_clicked(self._on_check)

        self._draw_upper()
        self._redraw_lower()
        self._apply()

    # ---- window sizing ---------------------------------------------------
    def _fit_to_screen(self, size):
        """Start the window at a size that fits the screen. All axes are placed in figure
        fractions, so the layout scales with the window. `size` = (w_px, h_px) overrides."""
        try:
            dpi = self.fig.dpi
            if size:
                w_in, h_in = size[0] / dpi, size[1] / dpi
            else:
                win = self.fig.canvas.manager.window
                sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
                w_in = min(self.fig.get_figwidth(), 0.92 * sw / dpi)
                h_in = min(self.fig.get_figheight(), 0.85 * sh / dpi)
            self.fig.set_size_inches(w_in, h_in, forward=True)
        except Exception as e:                     # never let sizing stop the viewer
            print(f"(could not size window to screen: {e})")

    # ---- time-zone aware accessors ----------------------------------------
    def _t(self, dd):
        return dd["tl" if self.local else "t"]

    def _tno(self, dd):
        return dd["tl_no" if self.local else "t_no"]

    # ---- Faux No-MLD support -------------------------------------------------
    def _shallowest(self, gpi, s):
        key = (int(gpi), s)
        if key not in self._shallow:
            if self._gpi_files is None:
                print("Indexing pp06 shards (first use of Faux No-MLD)...")
                self._gpi_files = MLD.build_gpi_file_index(self.site)
            depth, vals = MLD.load_profile(self._gpi_files, int(gpi), s)
            self._shallow[key] = (np.nan if depth is None or len(vals) == 0
                                  else float(vals[0]))   # arrays are depth-sorted ascending
        return self._shallow[key]

    def _open_points(self, dd, s):
        """(t, shallowest value) for the No-MLD profiles of one sensor (finite only)."""
        tno = self._tno(dd)
        if not len(tno):
            return np.array([]), np.array([])
        ov = np.array([self._shallowest(g, s) for g in dd["gpi_no"]])
        ok = np.isfinite(ov)
        return tno[ok], ov[ok]

    # ---- drawing --------------------------------------------------------
    def _clear(self, artists):
        for a in artists:
            try:
                a.remove()
            except Exception:
                pass
        artists.clear()

    def _draw_upper(self):
        self._clear(self.upper_artists)
        handles = []
        for s in SENSORS:
            x, y = with_gaps(self._t(self.d[s]), self.d[s]["mld"])
            ln = self.ax_up.plot(x, y, "o-", color=COLORS[s], ms=4, lw=1, label=SHORT[s])
            self.upper_artists += ln
            handles += ln
            if self.show_training and self.dt is not None:
                self.upper_artists += self.ax_up.plot(
                    self._t(self.dt[s]), self.dt[s]["mld"], "^", color=COLORS[s], ms=6,
                    mec="k", mew=0.5, ls="none")
        if self.show_training and self.dt is not None:
            handles.append(Line2D([], [], marker="^", color="gray", ls="none", ms=6,
                                  label="training"))
        self.ax_up.legend(handles=handles, loc="lower right", ncol=4, fontsize=8)

    def _redraw_lower(self):
        self._clear(self.lower_artists)
        self.cur = {}
        blend = mtransforms.blended_transform_factory(self.ax_lo.transData,
                                                      self.ax_lo.transAxes)
        for s in SENSORS:
            ax, c, d = self.ax_by[s], COLORS[s], self.d[s]
            # ---- science: circles joined by lines ----
            x, y = self._t(d), d["val"]
            is_open = np.zeros(len(x), bool)
            if self.mode == "O":
                ox, oy = self._open_points(d, s)
                x, y = np.concatenate([x, ox]), np.concatenate([y, oy])
                is_open = np.concatenate([is_open, np.ones(len(ox), bool)])
            o = np.argsort(x)
            x, y, is_open = x[o], y[o], is_open[o]
            xl, yl = with_gaps(x, y)
            self.lower_artists += ax.plot(xl, yl, "-", color=c, lw=1)
            self.lower_artists += ax.plot(x[~is_open], y[~is_open], "o", color=c, ms=4)
            if is_open.any():
                self.lower_artists += ax.plot(x[is_open], y[is_open], "o", mfc="white",
                                              mec=c, ms=5)
            if self.mode == "X" and len(self._tno(d)):
                self.lower_artists += self.ax_lo.plot(
                    self._tno(d), np.full(len(self._tno(d)), X_ROW[s]), "x", color=c, ms=6,
                    transform=blend, scalex=False, scaley=False)
            allx, ally = [x], [y]
            # ---- training: triangles, markers only ----
            if self.show_training and self.dt is not None:
                dt = self.dt[s]
                tx, ty = self._t(dt), dt["val"]
                self.lower_artists += ax.plot(tx, ty, "^", color=c, ms=6, mec="k", mew=0.5,
                                              ls="none")
                allx.append(tx)
                ally.append(ty)
                if self.mode == "O":
                    ox, oy = self._open_points(dt, s)
                    if len(ox):
                        self.lower_artists += ax.plot(ox, oy, "^", mfc="white", mec=c, ms=6,
                                                      ls="none")
                        allx.append(ox)
                        ally.append(oy)
                elif len(self._tno(dt)):
                    self.lower_artists += self.ax_lo.plot(
                        self._tno(dt), np.full(len(self._tno(dt)), X_ROW[s]), "x", color=c,
                        ms=6, transform=blend, scalex=False, scaley=False)
            self.cur[s] = (np.concatenate(allx), np.concatenate(ally))
        if getattr(self, "_xlim", None):          # plotting can autoscale the shared x axis
            self.ax_up.set_xlim(*self._xlim)
        self._rescale_y()
        self.fig.canvas.draw_idle()

    def _rescale_y(self):
        """Adaptive ON: fit y axes to the visible window. OFF: fixed WIDE limits = full range
        of all loaded labels over ALL times (so any start time is directly comparable)."""
        if self.adaptive:
            lo, hi = self.ax_up.get_xlim()
        else:
            lo, hi = -np.inf, np.inf
        # upper: depth (science + training if shown)
        parts = []
        for s in SENSORS:
            for dd in ([self.d[s]] + ([self.dt[s]] if self.show_training and self.dt else [])):
                t = self._t(dd)
                parts.append(dd["mld"][(t >= lo) & (t <= hi)])
        ys = np.concatenate(parts)
        if ys.size:
            top = max(0.0, ys.min() - 3) if self.adaptive else 0.0
            self.ax_up.set_ylim(ys.max() + 3, top)
        # lower: each sensor on its own axis
        for s in SENSORS:
            x, y = self.cur[s]
            m = (x >= lo) & (x <= hi) & np.isfinite(y)
            if m.any():
                ymin, ymax = y[m].min(), y[m].max()
                pad = 0.08 * (ymax - ymin) if ymax > ymin else 0.5
                # headroom at the top so X markers (rows 0.89-0.97) don't sit on the data
                self.ax_by[s].set_ylim(ymin - pad, ymax + pad + 0.25 * (ymax - ymin + 2 * pad))

    # ---- time controls ---------------------------------------------------
    def _on_time(self, _val):
        self._apply()

    def _apply(self):
        """Window start = coarse + fine offset; end = start + width."""
        self.start = self.sl_coarse.val + self.sl_fine.val
        width = self.sl_width.val
        self._xlim = (self.start, self.start + width)
        self.ax_up.set_xlim(*self._xlim)            # lower chart shares x
        fmt = "%Y-%m-%d %H:%M"
        tz = "Pacific local" if self.local else "UTC"
        self.sl_coarse.valtext.set_text(mdates.num2date(self.sl_coarse.val).strftime(fmt))
        self.sl_fine.valtext.set_text(f"+{self.sl_fine.val:.2f} d")
        self.sl_width.valtext.set_text(f"{width:.2f}")
        self.ax_up.set_title(f"MLD time series -- {self.site} (who={self.who}, {tz})")
        self.ax_lo.set_xlabel(f"window ({tz}): {mdates.num2date(self._xlim[0]).strftime(fmt)}"
                              f"  to  {mdates.num2date(self._xlim[1]).strftime(fmt)}",
                              fontsize=9)
        self._rescale_y()
        self.fig.canvas.draw_idle()

    def _convert_start(self, to_local):
        """Same instant, expressed in the other time zone (matplotlib date number)."""
        ts = pd.Timestamp(mdates.num2date(self.start).replace(tzinfo=None))
        if to_local:
            out = ts.tz_localize("UTC").tz_convert(LOCAL_TZ).tz_localize(None)
        else:
            out = (ts.tz_localize(LOCAL_TZ, ambiguous=True, nonexistent="shift_forward")
                   .tz_convert("UTC").tz_localize(None))
        return mdates.date2num(out)

    # ---- checkbox panel ----------------------------------------------------
    def _on_check(self, _label):
        st = dict(zip(CHECK_LABELS, self.chk.get_status()))
        self.adaptive = st["Adaptive y"]
        self.show_training = st["Training (^)"] and self.dt is not None
        new_mode = "O" if st["Faux No-MLD"] else "X"
        new_local = st["Local time"]
        if new_local != self.local:
            new_start = self._convert_start(new_local)
            self.local = new_local
            for sl, v in ((self.sl_coarse, float(np.clip(new_start, self.c0, self.c1))),
                          (self.sl_fine, 0.0)):
                sl.eventson = False           # set both without triggering redraws
                sl.set_val(v)
                sl.eventson = True
        self.mode = new_mode
        self._draw_upper()
        self._redraw_lower()
        self._apply()


def main():
    ap = argparse.ArgumentParser(description="MLD time-series viewer.")
    ap.add_argument("--site", choices=op.SITES, default="sb", help="Site (default sb).")
    ap.add_argument("--start", default="2024-01-01", help="Window start (default 2024-01-01).")
    ap.add_argument("--end", default="2024-01-31",
                    help="Window end, inclusive (default 2024-01-31).")
    ap.add_argument("--who", default="R", help="Labeler whose CSVs to read (default R).")
    ap.add_argument("--local", action="store_true",
                    help="Start in Pacific local time (default UTC); toggle in the window.")
    ap.add_argument("--size", default=None, metavar="WxH",
                    help="Initial window size in pixels, e.g. 1500x850 "
                         "(default: auto-fit to the screen).")
    args = ap.parse_args()
    size = tuple(int(v) for v in args.size.lower().split("x")) if args.size else None

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end) + pd.Timedelta(days=1)   # --end is inclusive of that day

    sci_path = MLD.science_labels_path(args.site, args.who)
    if not sci_path.exists():
        raise SystemExit(f"No science label file: {sci_path}")
    sci = load_labels(sci_path)

    tr = None
    tr_path = MLD.labels_path(args.site, 5, args.who)
    if tr_path.exists():
        tr = load_labels(tr_path)
        seen = set(zip(sci["gpi"], sci["sensor"]))       # science was seeded from training
        keep = [(g, s) not in seen for g, s in zip(tr["gpi"], tr["sensor"])]
        tr = tr[keep].reset_index(drop=True)
    else:
        print(f"(no training label file at {tr_path}; Training toggle disabled)")

    print(f"{args.site}/{args.who}: science {len(sci)} rows "
          f"({sci.groupby('sensor').size().to_dict()}; {int(sci['nomld'].sum())} No MLD)"
          + (f"; training (not in science) {len(tr)} rows "
             f"({int(tr['nomld'].sum())} No MLD)" if tr is not None else ""))
    Viewer(args.site, args.who, sci, tr, start, end, args.local, size)
    plt.show()


if __name__ == "__main__":
    main()
