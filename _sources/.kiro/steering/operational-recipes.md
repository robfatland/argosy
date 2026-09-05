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


## 4. Poster PDF export (AGU)

The AGU poster is HTML/CSS (`poster/AGUPoster.html`, KaTeX for math). Export to a
size-exact PDF via headless Chromium — see `poster/README.md` for the command and the
QR-code generation step.
