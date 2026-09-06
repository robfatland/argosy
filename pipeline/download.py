"""
pipeline/download.py — OOINET data acquisition for the Phase 1 pipeline.

Single source of truth for the download logic (extracted from DataDownload.ipynb so the
notebook and the cloud/EC2 job call the SAME code, not duplicates). Pure functions +
`ooipaths` for destinations, so it runs identically:
  - locally from the notebook (`%run` / `from pipeline.download import ...`)
  - headless on an EC2 instance (see pipeline/run_pipeline.sh)

Inputs: a URL list file (default `~/argosy/download_link_list.txt`), one OOINET async
staging URL per line (`#` lines ignored). Destinations come from
`ooipaths.ooinet_dir(site, channel="scalar")` → `<year>_<instrument>/` folders.
Restart-tolerant: existing non-empty files are skipped.
"""

import sys
import re
from pathlib import Path

# Repo root importable so `import ooipaths` works under %run or headless.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# Optional deps (only needed for actual downloads, not for imports/tests).
try:
    import requests
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    requests = None
    BeautifulSoup = None

# Repo-level bookkeeping files (NOT in the data tree).
URL_LIST_FILE = op.ARGOSY_ROOT / "download_link_list.txt"
COMPLETED_FILE = op.ARGOSY_ROOT / "downlinklist_completed.txt"

# Instrument key -> OOI instrument code (from the sensor table).
SCALAR_INSTRUMENTS = {
    "ctd":  "CTDPF",
    "flor": "FLORT",
    "ph":   "PHSEN",
    "pco2": "PCO2W",
    "nitr": "NUTNR",
    "par":  "PARAD",
}
# Vector instruments (not yet active): 'vel':'VELPT', 'irr':'SPKIR', 'oa':'OPTAA'

INSTRUMENT_CODES = [
    "CTDPF", "FLORT", "PHSEN", "PCO2W", "NUTNR", "PARAD",
    "VELPT", "SPKIR", "OPTAA", "DOFST",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def _read_urls(url_list_file=URL_LIST_FILE):
    p = Path(url_list_file)
    if not p.exists():
        return None
    with open(p) as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


def parse_year_from_filename(filename):
    """Year from an OOINET NetCDF filename (first timestamp), or None."""
    m = re.search(r"_(\d{4})\d{2}\d{2}T\d{6}\.\d+-\d{8}T\d{6}\.\d+\.nc$", filename)
    return int(m.group(1)) if m else None


def is_file_complete(filepath):
    return filepath.exists() and filepath.stat().st_size > 0


def download_file(url, destination):
    """Stream one file to destination via a .tmp then atomic rename."""
    tmp = destination.with_suffix(".tmp")
    try:
        r = requests.get(url, stream=True, timeout=300)
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        tmp.rename(destination)
        return True
    except Exception as e:
        print(f"    Error: {e}")
        if tmp.exists():
            tmp.unlink()
        return False


def _move_url_to_completed(url_list_file, url):
    """Move a finished URL from the pending list to the completed log."""
    with open(COMPLETED_FILE, "a") as f:
        f.write(url + "\n")
    p = Path(url_list_file)
    lines = p.read_text().splitlines(keepends=True)
    with open(p, "w") as f:
        for ln in lines:
            if ln.strip() != url:
                f.write(ln)


# ── volume estimate (pre-download) ───────────────────────────────────────────

def estimate_download_volume(url_list_file=URL_LIST_FILE):
    """Report approximate pending download size per URL (samples file sizes via HEAD)."""
    if requests is None:
        print("requests/bs4 not available; cannot estimate.")
        return
    urls = _read_urls(url_list_file)
    if not urls:
        print("No active URLs.")
        return
    print(f"Active URLs: {len(urls)}\n{'='*80}\n")
    grand_bytes = grand_files = 0
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        try:
            resp = requests.get(url, timeout=30); resp.raise_for_status()
            links = BeautifulSoup(resp.text, "html.parser").find_all("a")
            nc = [l for l in links if l.get("href", "").endswith(".nc")
                  and not l.get("href", "").endswith(".ncml")]
            by_inst = {}
            for l in nc:
                href = l.get("href", "")
                code = next((c for c in INSTRUMENT_CODES if c in href), "OTHER")
                by_inst.setdefault(code, []).append(l)
            url_inst = next((c for c in INSTRUMENT_CODES if c in url), None)
            print(f"  Total .nc files: {len(nc)}" + (f" | URL instrument: {url_inst}" if url_inst else ""))
            for code, ls in sorted(by_inst.items()):
                sampled = sampled_bytes = 0
                for l in ls[:min(2, len(ls))]:
                    try:
                        h = requests.head(url.rstrip("/") + "/" + l.get("href", ""),
                                          timeout=15, allow_redirects=True)
                        cl = h.headers.get("Content-Length")
                        if cl:
                            sampled_bytes += int(cl); sampled += 1
                    except Exception:
                        pass
                if sampled:
                    avg = sampled_bytes / sampled
                    est = avg * len(ls)
                    will = (code == url_inst)
                    tag = " <-- WILL DOWNLOAD" if will else "     (skipped)"
                    print(f"    {code:6s}: {len(ls):3d} files, ~{avg/1e6:.0f} MB each, est {est/1e9:.2f} GB{tag}")
                    if will:
                        grand_bytes += est
                else:
                    print(f"    {code:6s}: {len(ls):3d} files, size unknown")
            grand_files += len(by_inst.get(url_inst, []))
        except Exception as e:
            print(f"  Error: {e}")
        print()
    print(f"{'='*80}\nWILL DOWNLOAD: ~{grand_files} files, ~{grand_bytes/1e9:.2f} GB")


# ── bulk download ────────────────────────────────────────────────────────────

def bulk_download(instrument, ooi_instrument, site=op.DEFAULT_SITE,
                  url_list_file=URL_LIST_FILE, years=None):
    """Download one instrument's files from every matching URL, restart-tolerant.
    Destination: ooipaths.ooinet_dir(site,'scalar')/<year>_<instrument>/.
    `years`: optional iterable of ints; if given, only files whose (first-timestamp)
    year is in the set are fetched — useful for slice-testing and incremental top-ups."""
    if requests is None:
        print("requests/bs4 not available; cannot download.")
        return
    years = set(years) if years else None
    print(f"bulk_download: instrument={instrument} (OOI {ooi_instrument}) site={site}"
          + (f" years={sorted(years)}" if years else ""))
    urls = _read_urls(url_list_file)
    if urls is None:
        print(f"File not found: {url_list_file}")
        return

    base = op.ooinet_dir(site, channel="scalar")
    base.mkdir(parents=True, exist_ok=True)
    for year in range(2014, 2027):
        (base / f"{year}_{instrument}").mkdir(exist_ok=True)

    dl = skip = complete = 0
    for i, url in enumerate(urls, 1):
        print(f"=== URL {i}/{len(urls)} ===\n{url}")
        try:
            resp = requests.get(url, timeout=30); resp.raise_for_status()
            links = BeautifulSoup(resp.text, "html.parser").find_all("a")
            names = [l.get("href", "") for l in links
                     if l.get("href", "").endswith(".nc")
                     and not l.get("href", "").endswith(".ncml")
                     and ooi_instrument in l.get("href", "")]
            todo = []
            for nm in names:
                yr = parse_year_from_filename(nm)
                if yr is None:
                    continue
                if years is not None and yr not in years:
                    continue
                dest = base / f"{yr}_{instrument}" / nm
                if is_file_complete(dest):
                    complete += 1
                else:
                    todo.append((nm, yr))
            print(f"  .nc: {len(names)} | done: {len(names)-len(todo)} | to fetch: {len(todo)}")
            for j, (nm, yr) in enumerate(todo, 1):
                dest = base / f"{yr}_{instrument}" / nm
                print(f"  [{j}/{len(todo)}] {nm} -> {yr}_{instrument}/")
                if download_file(url.rstrip("/") + "/" + nm, dest):
                    dl += 1
                else:
                    skip += 1
        except Exception as e:
            print(f"  Error processing URL: {e}")
    print(f"=== done: complete={complete} downloaded={dl} failed={skip} ===")


def download_all(site=op.DEFAULT_SITE, url_list_file=URL_LIST_FILE, years=None):
    """Process every URL in the list: infer its instrument from the URL and fetch it.
    `years`: optional iterable of ints to restrict which years are downloaded."""
    urls = _read_urls(url_list_file)
    if urls is None:
        print("No download_link_list.txt found.")
        return
    code_to_key = {v: k for k, v in SCALAR_INSTRUMENTS.items()}
    for url in urls:
        key = next((code_to_key[c] for c in code_to_key if c in url), None)
        if key:
            bulk_download(key, SCALAR_INSTRUMENTS[key], site=site,
                          url_list_file=url_list_file, years=years)
        else:
            print(f"WARNING: could not determine instrument for URL: {url}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="OOINET download for the Phase 1 pipeline.")
    ap.add_argument("--site", default=op.DEFAULT_SITE, help="site code (sb/oo/ab)")
    ap.add_argument("--url-list", default=str(URL_LIST_FILE),
                    help="path to the URL list file (default download_link_list.txt); "
                         "use a per-site list, e.g. pipeline/oo_url_list.txt")
    ap.add_argument("--years", nargs="*", type=int, default=None,
                    help="restrict to these years, e.g. --years 2016 (default: all)")
    ap.add_argument("--estimate", action="store_true", help="estimate volume only, no download")
    args = ap.parse_args()
    if args.estimate:
        estimate_download_volume(url_list_file=args.url_list)
    else:
        download_all(site=args.site, url_list_file=args.url_list, years=args.years)
