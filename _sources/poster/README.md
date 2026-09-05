This folder `~/argosy/poster/` contains files for the AGU poster (standalone artifact,
intentionally NOT part of the Jupyter Book TOC).

- `AGUPoster.html` — the poster, authored in HTML/CSS with KaTeX for LaTeX math.
  48×36 in landscape; font sizes set for legibility at ~2 m. Currently a scaffold:
  stubbed title/authors/abstract and four figure placeholders (2×2 theme grid:
  Coincidence, Residual climatology, Cross-comparison/umbrella, Cloud & open science).

## Editing

- Math: write LaTeX as `$...$` (inline) or `$$...$$` (display) — KaTeX renders it. No new syntax.
- Swap a figure: replace a `<div class="figph">...</div>` with
  `<figure><img src="figs/yourfigure.png"></figure>`. Put figures in `poster/figs/`.
- Sizes are in inches so the physical poster is exact; keep body text ≥ ~0.3in for the 2 m rule.

## Export to PDF (vector, print-ready)

Chrome/Chromium headless preserves the exact page size:

```bash
google-chrome --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=AGUPoster.pdf --no-margins \
  file://$HOME/argosy/poster/AGUPoster.html
```
(If the page size isn't honored, set an @page rule `@page { size: 48in 36in; margin:0 }`
in the HTML, or use a headless-print tool that reads it.)

## Host online + QR

- The poster can be hosted at the GitHub Pages site (e.g. `robfatland.github.io/argosy/poster/AGUPoster.html`)
  or given a Zenodo DOI (preferred for citability — see `Publishing.md`).
- Generate the QR encoding that URL, then replace the `.qr` placeholder div with an `<img>`:
  ```bash
  # one option (Python): pip install qrcode[pil]
  python -c "import qrcode; qrcode.make('<POSTER_URL>').save('poster/figs/qr.png')"
  ```

## Status / TODO

- [ ] Final title, authors, affiliations, abstract
- [ ] Four theme figures (currently placeholders)
- [ ] Decide poster online home (Pages vs Zenodo DOI) → generate QR to it
- [ ] Confirm AGU session size/orientation requirement (assumed 48×36 landscape)
