"""
ooipaths.py — Single source of truth for the ~/ooi data filesystem layout.

WHY THIS MODULE EXISTS
    Path roots were previously hardcoded in every pipeline script. This module
    centralizes them so that (a) a directory restructure is a one-file change and
    (b) a per-site dimension can be introduced without touching callers.

LAYOUT (per-site, flipped Aug 2026)

        ~/ooi/<site>/{ooinet[/scalar|vector], redux/<yyyy>, postproc/<pp>/<yyyy>,
                      profileIndices, metadata, analysis[/<subdir>], visualizations}

    All path knowledge lives here; callers pass site=... (default "sb"). To add a
    site, drop its data under ~/ooi/<code>/ and pass site="<code>" — no caller edits.

SITES (all shallow profilers; layout/sensors identical across the three)
    Code  Site                OOI designator   SP node   Array
    sb    Oregon Slope Base   RS01SBPS         SF01A     RCA (Cabled Continental Margin)
    oo    Oregon Offshore     CE04OSPS         SF01B     Coastal Endurance (cabled)
    ab    Axial Base          RS03AXPS         SF03A     RCA
    (~/ooi is implicitly the shallow-profiler corpus; deep profilers / seafloor
     nodes, if added later, get their own root and their own structure.)

Verified against OOI authoritative naming (oceanobservatories.org), Aug 2026.
"""

from pathlib import Path

# ── Data root ────────────────────────────────────────────────────────────────
OOI_ROOT = Path("~/ooi").expanduser()

# Repo root (code + hand-maintained CSVs live here, NOT in the data tree)
ARGOSY_ROOT = Path("~/argosy").expanduser()

# ── Site registry ────────────────────────────────────────────────────────────
import os

SITES = ("sb", "oo", "ab")

# Default site for scripts that do `SITE = op.DEFAULT_SITE`. Overridable via the
# ARGOSY_SITE environment variable so the whole pipeline can be pointed at another
# site (e.g. `ARGOSY_SITE=oo python postprocess_pp05.py`) without editing code.
DEFAULT_SITE = os.environ.get("ARGOSY_SITE", "sb")
if DEFAULT_SITE not in SITES:
    raise ValueError(f"ARGOSY_SITE={DEFAULT_SITE!r} not in {SITES}")

# Default profile direction for scripts that build module-level paths at import
# (pp05/pp06). Overridable via ARGOSY_DIRECTION so the whole pp chain can target the
# descent tree (e.g. `ARGOSY_DIRECTION=descent python postprocess_pp05.py`) without
# code edits — parallel to ARGOSY_SITE. Validated after DIRECTIONS is defined below.

# site code -> (human name, OOI designator, shallow-profiler node, array)
SITE_INFO = {
    "sb": ("Oregon Slope Base", "RS01SBPS", "SF01A", "RCA"),
    "oo": ("Oregon Offshore",   "CE04OSPS", "SF01B", "Endurance"),
    "ab": ("Axial Base",        "RS03AXPS", "SF03A", "RCA"),
}


def _check_site(site):
    if site not in SITE_INFO:
        raise ValueError(f"Unknown site {site!r}; expected one of {SITES}")
    return site


def site_designator(site=DEFAULT_SITE):
    """OOI shallow-profiler designator for a site, e.g. 'RS01SBPS' for 'sb'."""
    return SITE_INFO[_check_site(site)][1]


# ── Directory accessors ──────────────────────────────────────────────────────
# Per-site layout (flipped Aug 2026):  ~/ooi/<site>/{ooinet, redux/<yyyy>,
# postproc/<pp>/<yyyy>, profileIndices, metadata, analysis, visualizations}.
# Every accessor takes `site` (default 'sb').

def site_root(site=DEFAULT_SITE):
    """Root for a site's data: ~/ooi/<site>."""
    _check_site(site)
    return OOI_ROOT / site


def ooinet_dir(site=DEFAULT_SITE, channel=None):
    """Raw OOINET source NetCDF (normally in S3 only; restored here to re-shard).
    Layout: ~/ooi/<site>/ooinet[/<channel>] where <channel> is 'scalar' or 'vector'.
    (The old 'rca/SlopeBase' segment is gone; the site is now the directory level.)
    """
    base = site_root(site) / "ooinet"
    if channel is None:
        return base
    if channel not in ("scalar", "vector"):
        raise ValueError(f"channel must be 'scalar' or 'vector', got {channel!r}")
    return base / channel


# ── Ascent / descent direction ───────────────────────────────────────────────
# The primary dataset is ASCENT (start→peak; sensors in pristine water). DESCENT
# (peak→end) is a second-class companion, recovered for the 8 HSD scalar sensors
# and kept in a PARALLEL tree so the ascent set stays pristine. See DescentData.md.
#   ascent  : redux/<yyyy>,          postproc/<pp>/<yyyy>,          shard version V1/V2
#   descent : redux_descent/<yyyy>,  postproc/<pp>_descent/<yyyy>,  shard version V1D
DIRECTIONS = ("ascent", "descent")

# Default direction (see the ARGOSY_DIRECTION note near DEFAULT_SITE).
DEFAULT_DIRECTION = os.environ.get("ARGOSY_DIRECTION", "ascent")
if DEFAULT_DIRECTION not in DIRECTIONS:
    raise ValueError(f"ARGOSY_DIRECTION={DEFAULT_DIRECTION!r} not in {DIRECTIONS}")

# Shard filename version token by direction (redux level).
REDUX_VERSION = {"ascent": "V1", "descent": "V1D"}


def _check_direction(direction):
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
    return direction


def redux_version(direction="ascent"):
    """Redux shard filename version token for a direction: 'V1' / 'V1D'."""
    return REDUX_VERSION[_check_direction(direction)]


def redux_base(site=DEFAULT_SITE, direction="ascent"):
    """Base holding per-year redux shard folders.
    ascent -> ~/ooi/<site>/redux ; descent -> ~/ooi/<site>/redux_descent."""
    _check_direction(direction)
    name = "redux" if direction == "ascent" else "redux_descent"
    return site_root(site) / name


def redux_dir(year, site=DEFAULT_SITE, direction="ascent"):
    """Redux shards for one year: ~/ooi/<site>/redux[_descent]/<yyyy>."""
    return redux_base(site, direction) / str(year)


def postproc_base(site=DEFAULT_SITE):
    """Base holding the ppNN postprocessing result folders."""
    return site_root(site) / "postproc"


def postproc_dir(pp, year, site=DEFAULT_SITE, direction="ascent"):
    """Postprocessing shards for one pp result and year:
    ascent  -> ~/ooi/<site>/postproc/<pp>/<yyyy>
    descent -> ~/ooi/<site>/postproc/<pp>_descent/<yyyy>
    (descent postproc lives in a parallel <pp>_descent folder; see DescentData.md)."""
    _check_direction(direction)
    pp_name = pp if direction == "ascent" else f"{pp}_descent"
    return postproc_base(site) / pp_name / str(year)


# Metadata is organized into subfolders by origin/purpose (each holds a README.md):
METADATA_SUBDIRS = ("qc", "profiles", "features", "annotations", "external", "cache", "scans")


def metadata_dir(site=DEFAULT_SITE, sub=None):
    """Derived metadata: ~/ooi/<site>/metadata[/<sub>].

    Subfolders (by origin/purpose; see METADATA_SUBDIRS):
      qc          — pipeline QC artifacts (pp05 manifest, exclusion summary)
      profiles    — profile classification/indexing (noon/midnight indices)
      features    — auto-derived per-profile features (cline_extract, surface_extract)
      annotations — human-in-the-loop review outputs (VisQC visitation, event labels)
      external    — non-OOI data (satellite SST/SSS)
      cache       — regenerable viz caches/logs (curtain contours, animation timing)
      scans       — one-off scans/notes
    `sub=None` returns the metadata root."""
    base = site_root(site) / "metadata"
    if sub is None:
        return base
    if sub not in METADATA_SUBDIRS:
        raise ValueError(f"Unknown metadata subfolder {sub!r}; expected one of {METADATA_SUBDIRS}")
    return base / sub


def profile_index_dir(site=DEFAULT_SITE):
    """Profile start/peak/end timestamps (read-only clone from GitHub):
    ~/ooi/<site>/profileIndices. Files keyed by OOI designator,
    e.g. RS01SBPS_profiles_<yyyy>.csv."""
    return site_root(site) / "profileIndices"


def visualizations_dir(site=DEFAULT_SITE):
    """Saved visualization outputs: ~/ooi/<site>/visualizations."""
    return site_root(site) / "visualizations"


def analysis_dir(subdir=None, site=DEFAULT_SITE):
    """Analysis outputs (SGA intermediates/results, etc.):
    ~/ooi/<site>/analysis[/<subdir>].  e.g. analysis_dir('sga')."""
    base = site_root(site) / "analysis"
    return base / subdir if subdir else base


# ── Well-known files ─────────────────────────────────────────────────────────
def exclusions_csv():
    """Manual QC embargo list. Lives in the repo, not the data tree."""
    return ARGOSY_ROOT / "sensor_exclusions.csv"


def pp05_manifest(site=DEFAULT_SITE, direction="ascent"):
    """pp05 QC manifest. Descent gets its own manifest so the two never collide."""
    _check_direction(direction)
    name = "pp05_manifest.csv" if direction == "ascent" else "pp05_descent_manifest.csv"
    return metadata_dir(site, "qc") / name


def pp05_exclusion_summary(site=DEFAULT_SITE, direction="ascent"):
    _check_direction(direction)
    name = ("pp05_exclusion_summary.csv" if direction == "ascent"
            else "pp05_descent_exclusion_summary.csv")
    return metadata_dir(site, "qc") / name


def special_profile_list(kind, site=DEFAULT_SITE):
    """Noon/midnight global-profile-index CSV (in the 'profiles' subfolder).
    Filename embeds site: ooi_rca_<site>_<kind>_global_profile_indices.csv."""
    if kind not in ("noon", "midnight"):
        raise ValueError(f"kind must be 'noon' or 'midnight', got {kind!r}")
    _check_site(site)
    return metadata_dir(site, "profiles") / f"ooi_rca_{site}_{kind}_global_profile_indices.csv"


# ── Shard filename helpers ───────────────────────────────────────────────────
# Shard names look like: RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_<V>.nc
# where the site token is the 2-letter code and 'sp' is shallow-profiler.
def shard_glob(sensor, site=DEFAULT_SITE, version=None, direction=None):
    """Glob pattern matching one sensor's shards for a site.

    Pass `direction` ('ascent'/'descent') to select the version token automatically
    (V1 / V1D), or pass `version` explicitly. `direction` takes precedence; if neither
    is given, defaults to the ascent 'V1'."""
    _check_site(site)
    if direction is not None:
        version = redux_version(direction)
    elif version is None:
        version = "V1"
    return f"RCA_{site}_sp_{sensor}_*_{version}.nc"


def select_site(default=None, announce=None):
    """Interactively choose a shallow-profiler site, defaulting to the env var.

    Starts from `default` (or DEFAULT_SITE, which reads ARGOSY_SITE, else 'sb').
    Prompts the user to press Enter to keep the default, or type a 2-letter site
    code (sb/oo/ab) to switch (case-insensitive). Falls back silently to the
    default when stdin is unavailable (cloud JupyterHubs disable stdin) or on an
    unrecognized entry.

    If `announce` is given (e.g. a tool name), a confirmation line naming the
    chosen site is printed. Returns the chosen 2-letter site code.
    """
    if default is None:
        default = DEFAULT_SITE
    _check_site(default)
    options = ", ".join(f"{code}={SITE_INFO[code][0]}" for code in SITES)
    prompt = f"SP site [{options}] — Enter to keep default '{default}': "
    try:
        choice = input(prompt).strip().lower()
    except (EOFError, OSError, Exception):
        choice = ""
    if not choice:
        site = default
    elif choice in SITE_INFO:
        site = choice
    else:
        print(f"  '{choice}' not a known site; keeping default '{default}'.")
        site = default
    if announce:
        name, desig = SITE_INFO[site][0], SITE_INFO[site][1]
        print(f"{announce} — viewing SP site: {site} ({name}, {desig})")
    return site


if __name__ == "__main__":
    # Quick self-check: print the per-site layout paths for the default site.
    print("OOI_ROOT       :", OOI_ROOT)
    for s in SITES:
        name, desig, node, array = SITE_INFO[s]
        print(f"  {s}: {name} ({desig}/{node}, {array})")
    print("redux_dir(2022):", redux_dir(2022))
    print("redux descent  :", redux_dir(2022, direction="descent"))
    print("postproc pp06  :", postproc_dir("pp06", 2022))
    print("pp06 descent   :", postproc_dir("pp06", 2022, direction="descent"))
    print("postproc pp01  :", postproc_dir("pp01", 2022))
    print("metadata_dir   :", metadata_dir())
    print("profile_index  :", profile_index_dir())
    print("analysis sga   :", analysis_dir("sga"))
    print("pp05_manifest  :", pp05_manifest())
    print("noon list      :", special_profile_list("noon"))
    print("shard_glob DO  :", shard_glob("dissolvedoxygen"))
    print("ooinet scalar  :", ooinet_dir(channel="scalar"))
