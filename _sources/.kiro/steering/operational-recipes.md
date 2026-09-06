---
inclusion: always
---

# Operational Recipes (argosy)

Battle-tested, copy-paste commands for recurring operational tasks that are easy to
forget after a layoff. NOT part of the Jupyter Book. When a recipe is re-verified or a
new fix is discovered, update it here (this is the single source of truth for "how did
we do X?"). All commands assume the `argosy` conda env unless noted:

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate argosy
```

Toolchain locations (verified Sep 2026): `pandoc`, `jupyter-book`/`jb` (v1.0.0), and
`xelatex` are available inside the `argosy` env; `ghp-import` is system-level.


## 1. Build & publish the Jupyter Book

Source of truth for ordering is `_toc.yml`; appearance is `_config.yml`.

```bash
cd ~/argosy
jupyter-book build .            # renders HTML into ./_build/html
# preview locally: open _build/html/index.html
ghp-import -n -p -f _build/html # push to the gh-pages branch -> GitHub Pages
```

- `-n` no-jekyll, `-p` push, `-f` force. Published site: https://robfatland.github.io/argosy/
- After edits to `_toc.yml` or any chapter, re-run both commands.
- `_config.yml` sets `execute_notebooks: force`, so a build re-runs notebooks — can be slow;
  set to `off` in `_config.yml` if you only changed prose and want a fast build.


## 2. Markdown → PDF (per file, and the whole-book synthesis)

The naive `pandoc a.md -o a.pdf` fails on bullet/unicode glyphs. The working fix uses
**xelatex + unicode-math + DejaVu fonts**, all encapsulated in `~/argosy/_header.tex`.
Always pass `-H _header.tex` and `--pdf-engine=xelatex`.

Single file (`X.md`):

```bash
cd ~/argosy
pandoc X.md -o X.pdf --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=11pt -H _header.tex
```

Whole-doc-set synthesis PDF (the ordered `pandoc <list...> -o argosy.pdf` command with the
full file list) is documented in `ArgosyOverview.md` → "Building the PDF". Keep that list in
sync with `_toc.yml`'s Documentation part.

Requirements behind the fix (already installed; listed so they can be reinstalled):
- a TeX distribution providing `xelatex` (system `/usr/bin/xelatex`)
- LaTeX packages: `unicode-math`, `enumitem` (deep nested bullet support)
- fonts: DejaVu Serif / DejaVu Sans Mono / DejaVu Math TeX Gyre (`_header.tex` `\setmainfont` etc.)
If a new unknown-glyph error appears: identify the glyph, confirm the DejaVu fonts cover it,
or add a font fallback in `_header.tex` — then record the fix here.


## 3. Standalone Python programs with working matplotlib widgets

Scripts run OUTSIDE Jupyter (plain `python foo.py`) need an interactive GUI backend;
the notebook `%matplotlib inline` path does not apply. Use the **TkAgg** backend, set
BEFORE importing pyplot:

```python
import matplotlib
matplotlib.use('TkAgg')          # must precede pyplot import
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons
```

Requires the Tk bindings: `sudo apt install python3-tk`.
Working example in the repo: `iw/VisQCInspector.py` (interactive profile QC GUI).

Contrast with HEADLESS standalone scripts that only *save* figures/animations (no live
window): use `matplotlib.use('Agg')` instead (also before pyplot). Example: `vis/bundle_animate.py`.
(In WSL2, interactive TkAgg needs a working X/display; Agg does not — prefer Agg for
batch/animation output, TkAgg only for genuinely interactive tools.)


## 3b. OOINET download URL list — where it lives

The download step reads OOINET async-staging URLs (one per line, `#` lines ignored) from a
single fixed file: **`~/argosy/download_link_list.txt`**. This is the default for
`pipeline/download.py` and the notebook. Workflow: place a data order in the OOINET web
interface → the "order ready" email gives a staging URL → paste it (one per line) into
`~/argosy/download_link_list.txt` → run the download. `download.py` infers each URL's
instrument from the URL text (CTDPF/FLORT/PHSEN/PCO2W/NUTNR/PARAD) and routes files to
`~/ooi/<site>/ooinet/scalar/<year>_<instrument>/`. On success a URL is moved to
`~/argosy/downlinklist_completed.txt`. (`download.py --url-list <path>` can override, but the
default single file is the norm.)


## 4. Cloud pipeline: create / run / destroy a disposable EC2 runner

Phase 1 pipeline on a throwaway EC2 box (download → shard → pp06 → sync to S3), via AWS
CDK. Full detail + prerequisites in `cloud/README.md`. Quick form:

```bash
# one-time: npm install -g aws-cdk ; conda create -n argosy-cdk python=3.11 -y ;
#           conda activate argosy-cdk ; pip install aws-cdk-lib constructs ; cdk bootstrap
# CDK lives in the SEPARATE env `argosy-cdk` (keeps it out of the argosy analysis env).
conda activate argosy-cdk
cd ~/argosy/cloud
cdk deploy                                    # CREATE (prints the instance id + connect cmd)
# connect KEYLESS via SSM (no SSH key, no open port):
aws ssm start-session --target <instance-id>
sudo su - ec2-user
# populate ~/argosy/download_link_list.txt, then:
bash ~/argosy/pipeline/run_pipeline.sh <site>               # e.g. oo
cd ~/argosy/cloud && cdk destroy                            # DELETE (stops billing)
```

- The whole pipeline honors `ARGOSY_SITE` (set by run_pipeline.sh) — `ooipaths.DEFAULT_SITE`
  reads it, so every script targets the chosen site with no code edits.
- `cdk destroy` removes the instance AND its 500 GB volume (part of the stack). Always confirm
  no orphaned EBS volume remains in the console — that's the usual accidental-cost trap.
- Instance type default `c6i.xlarge` (~<$0.40/hr, us-west-2). Local-then-sync: results land on
  the box's local `~/ooi/<site>/` then `aws s3 sync` up to `s3://s3ooi/<site>/`.


## 4b. Reconnect to & monitor a running pipeline (after SSM timeout)

SSM sessions time out; the `nohup`'d pipeline keeps running. To pick monitoring back up:

```bash
aws ssm start-session --target <instance-id>   # you land as ssm-user
sudo su - ec2-user                             # ALWAYS do this — repo, logs, ~/ooi are ec2-user's
```

**Gotcha (why you land in the wrong place):** `ssm-user`'s home is empty; everything lives under
`/home/ec2-user`. Globs like `~/ooi/*.log` return "No such file" until you switch users.

**Is it still running / where is it?** (non-invasive; the log itself is block-buffered when piped
through `tee`, so it looks frozen — trust the filesystem, not the log):

```bash
ps aux | grep -E "run_pipeline|shard.py|download.py|postprocess" | grep -v grep
# process STATE 'D' = busy on disk I/O (normal for big CTD files), 'R'/'S' = running/sleeping.
```

**Best progress check = the redux tree, not the log** (year with growing count = current position):

```bash
echo "=== $(date '+%H:%M:%S') shard status ==="
echo "proc : $(ps -o %cpu=,stat=,etime= -p $(pgrep -f shard.py) 2>/dev/null || echo 'NOT RUNNING')"
echo "shards total : $(find ~/ooi/<site>/redux -name '*.nc' | wc -l)"
for d in ~/ooi/<site>/redux/*/; do printf '  %s  %6d\n' "$(basename "$d")" "$(find "$d" -name '*.nc' | wc -l)"; done
find ~/ooi/<site>/redux -name '*.nc' -printf '%T+ %p\n' | sort | tail -3 | sed 's|.*/||'
```

**Rate / ETA** (run twice ~60s apart; the delta is shards/min):

```bash
find ~/ooi/<site>/redux -name '*.nc' | wc -l; sleep 60; find ~/ooi/<site>/redux -name '*.nc' | wc -l
```

**Make the log itself live** (fixes the "tail shows nothing" problem) — set `PYTHONUNBUFFERED=1`
so stdout is line-buffered, before launching any stage:

```bash
export PYTHONUNBUFFERED=1 ARGOSY_SITE=<site>
cd ~/argosy
nohup bash pipeline/run_pipeline.sh <site> <stage> > ~/ooi/<site>_<stage>_$(date +%Y%m%dT%H%M%S).log 2>&1 &
tail -f "$(ls -t ~/ooi/<site>_<stage>_*.log | head -1)"
```

**Stages** (run separately after a partial/recovered run; `all` does the whole chain):
`download` → `shard` → `pp` (pp05, pp06, pp06_filter2, pp06_filter3) → `sync` (to `s3://s3ooi/<site>/`).
Success check for shard = the final `attempted= written= skipped=` block has **nonzero `written`**;
`attempted=0` means profile indices are missing (see note below).

**profileIndices are a required shard input** and are NOT in the download or git data tree. A fresh
box has none → sharding silently yields `attempted=0`. `run_pipeline.sh`'s download stage now pulls
them from `s3://s3ooi/<site>/profileIndices/`; one-time per site, push them up first from WSL:
`aws s3 sync ~/ooi/<site>/profileIndices/ s3://s3ooi/<site>/profileIndices/`
(filenames are `<designator>_profiles_<yyyy>.csv`, e.g. `CE04OSPS_profiles_2022.csv` for `oo`).

**When the run is fully done:** verify `aws s3 ls s3://s3ooi/<site>/redux/ --recursive --summarize | tail`,
then `cd ~/argosy/cloud && cdk destroy` (billing meter!) and confirm no orphaned EBS in the console.


## 5. Poster PDF export (AGU)

The AGU poster is HTML/CSS (`poster/AGUPoster.html`, KaTeX for math). Export to a
size-exact PDF via headless Chromium — see `poster/README.md` for the command and the
QR-code generation step.
