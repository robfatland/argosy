"""
shard_source.py — Local/S3 abstraction for reading shard files (Phase-1 / notebook use).

Lets a viewer (e.g. the bundle explorer in Visualizations.ipynb) read per-profile shards
either from the LOCAL data tree or DIRECTLY from S3, without the reader downloading the whole
~15 GB shard set. Fits the "compute-to-data / don't pull to the laptop" tenet (see BR.md).

Two operations are abstracted:
  - DISCOVERY  : which (gpi, sensor) shards exist for a year — glob local FS vs list S3.
  - OPEN       : return an xarray Dataset for a shard — local path vs s3fs/fsspec.

Public-access constraint: only pp06 is public on S3 ({sb,oo,ab}/postproc/pp06/*).
redux/pp01/pp02/pp05 are PRIVATE — so over S3 with no credentials, source MUST be 'pp06'.
(With credentials, other sources work too; open_dataset just needs read access.)

Usage:
    from shard_source import ShardSource
    src = ShardSource(site="sb", source="pp06", location="s3")   # or location="local"
    index = src.build_index(2022)          # {sensor: {gpi: key_or_path}}
    ds = src.open(index["temperature"][12345])

S3 reads require `s3fs` (pip install s3fs). The index listing is cached per (year) to
avoid repeated slow S3 list calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

try:
    import xarray as xr
except Exception:  # pragma: no cover
    xr = None

S3_BUCKET = "s3ooi"
PUBLIC_SOURCE = "pp06"   # the only source public over S3


class ShardSource:
    def __init__(self, site=op.DEFAULT_SITE, source="pp06", location="local"):
        if site not in op.SITES:
            raise ValueError(f"Unknown site {site!r}; expected {op.SITES}")
        if location not in ("local", "s3"):
            raise ValueError("location must be 'local' or 's3'")
        self.site = site
        self.source = source
        self.location = location
        self._index_cache = {}   # year -> {sensor: {gpi: ref}}
        self._fs = None          # lazy s3fs handle

        if location == "s3" and source != PUBLIC_SOURCE:
            # Not fatal (credentialed users can read private prefixes), but warn: an
            # unauthenticated Book reader can only get pp06 from S3.
            print(f"[shard_source] NOTE: only '{PUBLIC_SOURCE}' is public on S3; "
                  f"source={source!r} over S3 needs AWS credentials.")

    # -- path/key helpers ------------------------------------------------------
    def _local_year_dir(self, year):
        if self.source in ("redux", "pp05"):
            return op.redux_dir(year, self.site)
        return op.postproc_dir(self.source, year, self.site)

    def _s3_year_prefix(self, year):
        # Mirrors the local layout under the bucket.
        if self.source in ("redux", "pp05"):
            return f"{self.site}/redux/{year}/"
        return f"{self.site}/postproc/{self.source}/{year}/"

    def _s3(self):
        if self._fs is None:
            import s3fs
            # anon=True works for the public pp06 prefixes with no credentials.
            self._fs = s3fs.S3FileSystem(anon=(self.source == PUBLIC_SOURCE))
        return self._fs

    # -- discovery -------------------------------------------------------------
    def build_index(self, year, sensors=None):
        """Return {sensor: {gpi: ref}} for a year. `ref` is a local Path (location=local)
        or an 's3://...' string (location=s3). Cached per year."""
        if year in self._index_cache:
            return self._index_cache[year]
        sensors = sensors or _ALL_SENSORS
        index = {s: {} for s in sensors}

        if self.location == "local":
            year_dir = self._local_year_dir(year)
            if year_dir.exists():
                for s in sensors:
                    for f in year_dir.glob(f"*_{s}_*.nc"):
                        gpi = _gpi_from_name(f.name)
                        if gpi is not None:
                            index[s][gpi] = f
        else:
            fs = self._s3()
            prefix = f"{S3_BUCKET}/{self._s3_year_prefix(year)}"
            try:
                keys = fs.find(prefix)   # recursive listing
            except Exception as e:
                print(f"[shard_source] S3 list failed for {prefix}: {e}")
                keys = []
            for key in keys:
                name = key.rsplit("/", 1)[-1]
                if not name.endswith(".nc"):
                    continue
                s = _sensor_from_name(name, sensors)
                if s is None:
                    continue
                gpi = _gpi_from_name(name)
                if gpi is not None:
                    index[s][gpi] = "s3://" + key

        self._index_cache[year] = index
        return index

    # -- open ------------------------------------------------------------------
    def open(self, ref):
        """Open a shard reference (local Path or s3://... string) as an xarray Dataset."""
        if xr is None:
            raise RuntimeError("xarray not available")
        if isinstance(ref, Path) or (isinstance(ref, str) and not ref.startswith("s3://")):
            return xr.open_dataset(ref)
        # S3: hand xarray an open file object via s3fs.
        fs = self._s3()
        return xr.open_dataset(fs.open(ref[len("s3://"):]))


# == filename helpers ==========================================================
# RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc

_ALL_SENSORS = [
    "temperature", "salinity", "density", "dissolvedoxygen",
    "cdom", "chlora", "backscatter", "ph", "pco2", "nitrate", "par",
]


def _gpi_from_name(name):
    parts = name.replace(".nc", "").split("_")
    try:
        return int(parts[6])
    except (IndexError, ValueError):
        return None


def _sensor_from_name(name, sensors):
    for s in sensors:
        if f"_{s}_" in name:
            return s
    return None
