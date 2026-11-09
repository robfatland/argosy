This folder `~/argosy/shared_labels` contains files for sharing the small human-labeled MLD
CSVs (science and training) between collaborators through git, since `~/ooi` is not in the repo.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** git-shared copies of the human MLD label CSVs (science and training)
- **Next:** push after each labeling session: python ~/argosy/sync_labels.py push

Files here are copies of `~/ooi/<site>/metadata/annotations/mld_labels_<site>_{science,block05}_<who>.csv`.
Do not edit them by hand; move them with the sync script (rows are merged by (gpi, sensor, who),
later `reviewed_at` wins).

- `../sync_labels.py` -- `push` copies/merges labels from `~/ooi` into this folder (then commit and
  push the repo); `pull` merges this folder into the collaborator's `~/ooi` (after `git pull`).
  `--site`, `--who`, `--dry-run` supported.
- `../MLDTimeSeries.py` -- consumer: plots the science and training labels it finds in `~/ooi`.
- `../MLD.py` -- producer: the annotator that writes the label CSVs.

Naming: `mld_labels_<site>_science_<who>.csv` (dense month blocks) and
`mld_labels_<site>_block05_<who>.csv` (1 profile in ~45). `<who>` is the labeler (R = Rob, C = Chuck).
