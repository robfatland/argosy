"""
load_era5.py -- read the ERA5 point-timeseries payloads downloaded by fetch_era5.py
and return a tidy hourly series (and a daily reduction) per site.

What the raw CDS payload looks like (reanalysis-era5-single-levels-timeseries):
each site-year is a ZIP of two NetCDFs sharing one `valid_time` coord --
  wave file (0.5 deg grid):  swh, mwp, mwd
  surface  (0.25 deg grid):  u10, v10, slhf, sshf
(The other variables we asked for are not served by this product; see fetch_era5.py.)

Derived fields added here:
  wspd    = sqrt(u10^2 + v10^2)                     [m s-1]   10 m wind speed
  wdir    = meteorological FROM-direction of wind   [deg]     (0=N, 90=E)
  tau     = rho_air * Cd * wspd^2                    [N m-2]   wind stress magnitude
  ustar   = sqrt(tau / rho_water)                    [m s-1]   water-side friction velocity
  qlat    = slhf / 3600                               [W m-2]   latent heat flux (+ down)
  qsens   = sshf / 3600                               [W m-2]   sensible heat flux (+ down)
  qturb   = qlat + qsens                              [W m-2]   turbulent heat flux (+ down)

Caveats baked in:
  - Cd is a constant bulk drag coefficient (CD_DEFAULT). Good to ~20-30%; fine for a
    seasonal MLD comparison, not for a flux-closure study. Swap in a wind-speed-dependent
    Cd later if needed.
  - slhf/sshf are ONLY the turbulent part of the surface heat budget (no radiation in this
    product). Convective MLD deepening is driven mainly by buoyancy loss, to which the
    turbulent terms + longwave contribute; treat qturb as a proxy, not a closed budget.
  - Accumulated fields are hourly accumulations in J m-2; /3600 -> W m-2. Positive = DOWNWARD
    (ocean gains heat). So qturb < 0 (ocean losing heat) is the convective-deepening regime.

Public API:
  load_site_year(site, year)        -> xr.Dataset (hourly, derived fields added)
  load_site(site, years=None)       -> xr.Dataset (all available years concatenated)
  daily(ds)                         -> xr.Dataset (daily means + a daily wind-work column)

CLI (quick look):
  python ~/argosy/era5/load_era5.py --site oo --year 2024
  python ~/argosy/era5/load_era5.py --site oo --year 2024 --plot   # saves a PNG
"""
import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op  # noqa: E402
from fetch_era5 import SITE_LATLON  # noqa: E402  (site coordinates; same folder)

RHO_AIR = 1.22       # kg m-3
RHO_WATER = 1025.0   # kg m-3
CD_DEFAULT = 1.3e-3  # bulk 10 m drag coefficient (neutral, mid-range)


def _era5_dir(site):
    return op.metadata_dir(site, "external") / "era5"


def _payload_path(site, year):
    """Return the raw payload path for a site-year, preferring .nc then .zip."""
    d = _era5_dir(site)
    nc = d / f"era5_{site}_{year}.nc"
    zp = d / f"era5_{site}_{year}.zip"
    if nc.exists():
        return nc
    if zp.exists():
        return zp
    raise FileNotFoundError(f"No ERA5 payload for {site} {year} in {d}")


def _open_payload(path):
    """Open a payload (plain .nc or a zip of several .nc) and merge on valid_time.
    Returns an x.Dataset with a 'time' dimension."""
    if path.suffix == ".nc":
        ds = xr.open_dataset(path)
        members = [ds]
    else:
        members = []
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(path) as z:
                z.extractall(td)
            for nc in sorted(Path(td).glob("*.nc")):
                # load() so data survives the TemporaryDirectory teardown
                members.append(xr.open_dataset(nc).load())
    # Drop the scalar lat/lon data_vars (they differ between the two grids and would
    # collide on merge); keep them as dataset attributes instead.
    cleaned = []
    latlon = {}
    for m in members:
        for c in ("latitude", "longitude"):
            if c in m.variables:
                try:
                    latlon.setdefault(c, float(np.asarray(m[c]).ravel()[0]))
                except Exception:
                    pass
                m = m.drop_vars(c)
        cleaned.append(m)
    ds = xr.merge(cleaned, compat="override", combine_attrs="drop_conflicts")
    if "valid_time" in ds.dims or "valid_time" in ds.coords:
        ds = ds.rename({"valid_time": "time"})
    for k, v in latlon.items():
        ds.attrs[k] = v
    return ds


def _add_derived(ds):
    """Add wspd, wdir, tau, ustar, qlat, qsens, qturb in place; return ds."""
    u, v = ds["u10"], ds["v10"]
    ds["wspd"] = np.sqrt(u**2 + v**2)
    ds["wspd"].attrs = {"units": "m s-1", "long_name": "10 m wind speed"}

    # meteorological FROM-direction: 0=N, 90=E
    wdir = (270.0 - np.degrees(np.arctan2(v, u))) % 360.0
    ds["wdir"] = wdir
    ds["wdir"].attrs = {"units": "degree", "long_name": "10 m wind FROM-direction (met)"}

    tau = RHO_AIR * CD_DEFAULT * ds["wspd"] ** 2
    ds["tau"] = tau
    ds["tau"].attrs = {"units": "N m-2", "long_name": "wind stress magnitude",
                       "note": f"rho_air={RHO_AIR}, Cd={CD_DEFAULT} (constant bulk)"}

    ds["ustar"] = np.sqrt(tau / RHO_WATER)
    ds["ustar"].attrs = {"units": "m s-1", "long_name": "water-side friction velocity",
                         "note": f"sqrt(tau/rho_water), rho_water={RHO_WATER}"}

    for src, dst, lname in (("slhf", "qlat", "latent heat flux"),
                            ("sshf", "qsens", "sensible heat flux")):
        if src in ds:
            ds[dst] = ds[src] / 3600.0
            ds[dst].attrs = {"units": "W m-2",
                             "long_name": f"surface {lname} (positive downward)"}
    if "qlat" in ds and "qsens" in ds:
        ds["qturb"] = ds["qlat"] + ds["qsens"]
        ds["qturb"].attrs = {"units": "W m-2",
                             "long_name": "turbulent heat flux, latent+sensible (+ down)",
                             "note": "radiation terms NOT in this product; partial budget"}
    return ds


def _open_radiation(path):
    """Open the shared gridded radiation payload (plain .nc, or a zip of .nc members)."""
    if path.suffix == ".nc":
        return xr.open_dataset(path).load()
    parts = []
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(path) as z:
            z.extractall(td)
        for nc in sorted(Path(td).glob("*.nc")):
            parts.append(xr.open_dataset(nc).load())
    return xr.merge(parts, compat="override")


def _add_radiation(ds, site, year):
    """If the shared radiation file for `year` exists (fetch_era5_radiation.py), crop the
    nearest grid cell to `site` and add qsw, qlw (W m-2, + down), qrad = qsw+qlw, and
    qnet = qrad + qturb (the full net surface heat flux). No-op if the file is absent."""
    d = op.OOI_ROOT / "era5_shared"
    path = next((p for p in (d / f"era5rad_shared_{year}.nc", d / f"era5rad_shared_{year}.zip")
                 if p.exists()), None)
    if path is None:
        return ds
    rad = _open_radiation(path)
    if "valid_time" in rad.dims or "valid_time" in rad.coords:
        rad = rad.rename({"valid_time": "time"})
    if "expver" in rad.dims:                      # ERA5T/ERA5 mix: NaN-skipping merge
        rad = rad.mean("expver")
    lat, lon = SITE_LATLON[site]
    if float(rad["longitude"].max()) > 180 and lon < 0:
        lon += 360.0
    cell = rad.sel(latitude=lat, longitude=lon, method="nearest")
    ds.attrs["rad_latitude"] = float(cell["latitude"])
    ds.attrs["rad_longitude"] = float(cell["longitude"])
    cell = cell.drop_vars(["latitude", "longitude"], errors="ignore")
    for src, dst, name in (("ssr", "qsw", "net shortwave (solar)"),
                           ("str", "qlw", "net longwave (thermal)")):
        if src in cell:
            ds[dst] = (cell[src] / 3600.0).reindex(time=ds["time"])
            ds[dst].attrs = {"units": "W m-2",
                             "long_name": f"surface {name} radiation (positive downward)"}
    if "qsw" in ds and "qlw" in ds:
        ds["qrad"] = ds["qsw"] + ds["qlw"]
        ds["qrad"].attrs = {"units": "W m-2", "long_name": "net radiation (+ down)"}
        if "qturb" in ds:
            ds["qnet"] = ds["qrad"] + ds["qturb"]
            ds["qnet"].attrs = {"units": "W m-2",
                                "long_name": "net surface heat flux, qsw+qlw+qlat+qsens (+ down)"}
    return ds


def load_site_year(site, year):
    """Hourly ERA5 dataset for one site-year, with derived fields (and radiation / net heat
    flux when the shared radiation file for that year has been downloaded)."""
    ds = _open_payload(_payload_path(site, year))
    ds = _add_derived(ds)
    ds = _add_radiation(ds, site, year)
    ds.attrs["site"] = site
    return ds


def load_site(site, years=None):
    """Concatenate all available (or the given) site-years along time."""
    d = _era5_dir(site)
    if years is None:
        found = set()
        for p in d.glob(f"era5_{site}_*.nc"):
            found.add(int(p.stem.rsplit("_", 1)[1]))
        for p in d.glob(f"era5_{site}_*.zip"):
            found.add(int(p.stem.rsplit("_", 1)[1]))
        years = sorted(found)
    parts = [load_site_year(site, y) for y in years]
    if not parts:
        raise FileNotFoundError(f"No ERA5 payloads for {site} in {d}")
    return xr.concat(parts, dim="time")


def daily(ds):
    """Daily means, plus a daily cumulative wind-work proxy (integral of ustar^3).
    ustar^3 ~ turbulent kinetic energy input rate; its daily sum is a mixing-energy
    index well suited to lagged MLD regressions."""
    dd = ds.resample(time="1D").mean()
    # ustar^3 summed over the day's hourly samples (times 3600 s = per-day energy ~ m3 s-2)
    work = (ds["ustar"] ** 3).resample(time="1D").sum() * 3600.0
    dd["wind_work"] = work
    dd["wind_work"].attrs = {"units": "m3 s-2",
                             "long_name": "daily integral of ustar^3 (mixing-energy proxy)"}
    return dd


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--plot", action="store_true", help="save a quick PNG to visualizations/")
    args = ap.parse_args()

    ds = load_site_year(args.site, args.year)
    print(ds)
    print("\nlat/lon:", ds.attrs.get("latitude"), ds.attrs.get("longitude"))
    print("time:", str(ds["time"].values[0]), "->", str(ds["time"].values[-1]),
          f"({ds.sizes['time']} hourly steps)")
    print("radiation cell:", ds.attrs.get("rad_latitude"), ds.attrs.get("rad_longitude"))
    for v in ("swh", "wspd", "tau", "ustar", "qturb", "qsw", "qlw", "qnet"):
        if v in ds:
            arr = ds[v].values
            print(f"  {v:6s} min={np.nanmin(arr):10.4g}  "
                  f"mean={np.nanmean(arr):10.4g}  max={np.nanmax(arr):10.4g}")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        dd = daily(ds)
        fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
        ax[0].plot(dd["time"], dd["swh"], lw=0.8)
        ax[0].set_ylabel("Hs (m)")
        ax[1].plot(dd["time"], dd["wind_work"], lw=0.8, color="tab:orange")
        ax[1].set_ylabel("wind work\n(ustar^3, m3 s-2/day)")
        ax[2].plot(dd["time"], dd["qturb"], lw=0.8, color="tab:red")
        ax[2].axhline(0, color="k", lw=0.5)
        ax[2].set_ylabel("q_turb (W m-2)\n(+ down)")
        ax[0].set_title(f"ERA5 daily -- {args.site} {args.year}")
        fig.tight_layout()
        out = op.visualizations_dir(args.site) / f"era5_daily_{args.site}_{args.year}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
