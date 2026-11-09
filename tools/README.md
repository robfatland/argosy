This folder `~/argosy/tools` contains files for **keeping the project navigable**: a checker for
broken cross-references and a generator for the project manifest.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** project hygiene tools: a cross-reference checker and a manifest generator
- **Next:** run `check_refs.py --baseline` once, then after every file move

## Files

- `check_refs.py` -- finds references (file names, paths, links, `%run`, `_toc.yml` entries, backticked
  folders, repo-local imports) that no longer resolve. `--baseline` records today's state; a plain run
  reports only NEW breakage; `--all` lists everything; `--impact NAME` shows everything that mentions
  NAME before you move it, plus the Python path hazards. Read-only.
- `refs_ignore.txt` -- regular expressions for names to skip (examples, files in other repos).
- `refs_baseline.json` -- written by `--baseline`: the known, accepted dangling references.
- `gen_manifest.py` -- builds the table of sub-project folders (status, purpose) from the folder
  READMEs, in a logical order, and can rewrite the marked block in `../poster/agumemo.md`.

## Routine around a move

1. `python tools/check_refs.py --impact NAME` -- see the blast radius and the hazards. Run it with
   the file name (`postprocess_pp05.py`) and again with the bare stem (`postprocess_pp05`) to catch
   prose mentions that omit the extension.
2. Move the file; update the LIVE references it lists (leave historical ones alone).
3. `python tools/check_refs.py` -- must print no NEW dangling references.
4. `python tools/gen_manifest.py --write poster/agumemo.md` -- refresh the manifest if folders changed.
