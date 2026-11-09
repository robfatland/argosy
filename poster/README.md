This folder `~/argosy/poster/` contains files for the AGU poster (standalone artifact,
intentionally NOT part of the Jupyter Book TOC).

- **Status:** active (reviewed Nov 2026)
- **Purpose:** AGU26 poster (HTML), its project handout and technical guide (agumemo.md), and logistics
- **Next:** re-lay out to 42 x 42 in; build the four panel figures; Zenodo DOI and QR code

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

Chrome/Chromium headless preserves the exact page size. Set the poster to 42×42 in (below):

```bash
google-chrome --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=AGUPoster.pdf --no-margins \
  file://$HOME/argosy/poster/AGUPoster.html
```
If the page size isn't honored, add an `@page` rule in the HTML `<style>`:
`@page { size: 42in 42in; margin: 0 }`. (On WSL the binary may be `google-chrome`,
`google-chrome-stable`, or `chromium`.)

## Host online + QR (Zenodo)

- Host the poster at a **Zenodo DOI** (citable; see `Publishing.md`). Publish the poster
  (PDF and/or the HTML) to Zenodo, then encode that DOI URL in the QR.
- Generate the QR, then replace the `.qr` placeholder div in `AGUPoster.html` with
  `<img src="figs/qr.png">`:
  ```bash
  pip install "qrcode[pil]"
  python -c "import qrcode; qrcode.make('<ZENODO_DOI_URL>').save('figs/qr.png')"   # run from poster/
  ```
- Test: scan the printed/exported PDF from ~2 m before finalizing.

## AGU26 acceptance details (authoritative)

*Source: AGU acceptance email (pasted by Rob). Links are from that email — follow them in a
browser; they are not verified here.*

- Meeting: **AGU26** — https://www.agu.org/annual-meeting
- Abstract submission ID: **2097211**
- Format: **Poster** (shared board, side-by-side)
- Session: **OS31D — Long-Term Ocean Observatories as Drivers of Sensor and Data Science
  Innovation I Poster**
- When: **Wednesday 9 December 2026, 08:30–12:00 PST**
- Where: **Moscone, Halls ABC (poster hall)**
- Title: *Coincident Anomalies in Ten Years of Photic Zone Profiles: An Interpretive
  Framework for OOI Shallow Profiler Data*
- Title/session/abstract are embedded in `AGUPoster.html` (submitted abstract condensed to fit
  the poster; full text is in the AGU submission).

### Poster size (hard constraint)

- **Max 44 in × 44 in** on a shared board. **Design target: 42 in × 42 in (square).**
  Update `AGUPoster.html` from the old 48×36 landscape to **42×42 square** — this changes the
  CSS page size AND the 2×2 panel layout (was landscape).

### Printing

- **CCI on-site poster printing service** (AGU presenter resources):
  https://www.agu.org/annual-meeting/present?tab=presenter-resources  (poster-requirements tab)

### Deadlines & presenter links (from the email)

- [ ] **Confirm participation by 5 November** in the Speaker Center:
  https://studio.m-anage.com/agu/agu26/speakercenter.cgi
  (the email included a pre-filled username/password query string — use the email's link directly)
- Poster presenter resources: https://www.agu.org/annual-meeting/present?tab=posters
- Scientific Program / schedule app: https://studio.m-anage.com/agu/agu26/meetingapp.cgi

## Panel mapping (poster vs. abstract)

The abstract frames **three** coincidence types (self / inter-sensor / corroborated) plus a
baseline-envelope method and a pycnocline finding. The 4-panel grid maps these as:
1. Baseline envelopes & anomaly definition (the method)
2. Self & inter-sensor coincidence
3. Pycnocline signals (internal waves / water-mass emplacement) — the headline result
4. Corroborated coincidence + open/reproducible science (external sources + cloud)
(Earlier scaffold themes "residual climatology" and "cross-comparison/umbrella" are folded
into panels 1 and 4 respectively. Revisit if you'd rather split differently.)

## Status / TODO

- [x] Title, session, abstract embedded (AGU26 / OS31D / 2097211)
- [x] Size/orientation confirmed: max 44×44 shared board → design for **42×42 square**
- [x] Co-authors: **R. Fatland**; **Isabella Fatland (Cornell University)**
- [ ] Re-lay out `AGUPoster.html` from 48×36 landscape to **42×42 square** (page size + panel grid)
- [ ] Four panel figures (currently placeholders)
- [ ] Publish poster to **Zenodo** → mint DOI → generate QR to it
- [ ] Confirm AGU26 participation by **5 Nov** in the Speaker Center
