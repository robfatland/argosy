#!/usr/bin/env bash
# ==============================================================================
# pipeline/run_pipeline.sh — Phase 1 pipeline entrypoint for a disposable EC2 box.
#
# Flow (local-then-sync): download OOINET -> shard to redux -> pp05/pp06,
# writing to the instance's local ~/ooi tree, then `aws s3 sync` the results
# up to s3://s3ooi/<site>/. Designed to be invoked by the CDK stack's user-data,
# or run by hand after SSHing in. Idempotent / restart-tolerant where the
# underlying steps are (download skips existing; pp06 skips existing outputs).
#
# Usage:  bash run_pipeline.sh <site> [stage] [url_list]
#   <site>    : sb | oo | ab
#   [stage]   : all (default) | download | shard | pp | sync
#   [url_list]: optional path to the OOINET URL list; defaults to
#               pipeline/<site>_url_list.txt if present, else download_link_list.txt
#
# Prereqs on the box (the CDK user-data installs these):
#   - miniconda with the `argosy` env (or requirements installed)
#   - the argosy repo cloned at ~/argosy
#   - AWS credentials via the instance IAM role (no keys on disk)
#   - ~/argosy/download_link_list.txt populated with the OOINET staging URLs
# ==============================================================================
set -uo pipefail

SITE="${1:?usage: run_pipeline.sh <site> [stage]}"
STAGE="${2:-all}"
ARGOSY="${ARGOSY:-$HOME/argosy}"
LOG="$HOME/pipeline_${SITE}_$(date +%Y%m%dT%H%M%S).log"

echo "=== Phase 1 pipeline | site=$SITE stage=$STAGE | log=$LOG ===" | tee "$LOG"

# Activate the conda env if present (harmless if already active).
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1091
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate argosy 2>/dev/null || true
fi

cd "$ARGOSY" || { echo "no $ARGOSY"; exit 1; }

# Ensure the data root exists. On a fresh box ~/ooi may not exist yet; the stages below
# write under it, and callers often redirect their own log to ~/ooi/. Create it early so
# a bare fresh box doesn't fail before any stage runs. (Real data still lands here; on the
# EBS-as-root layout ~/ooi is a normal dir on the big root volume.)
mkdir -p "$HOME/ooi" "$HOME/ooi/$SITE"

# Optional per-site URL list (3rd arg); defaults to pipeline/<site>_url_list.txt if present,
# else download.py's built-in ~/argosy/download_link_list.txt.
URL_LIST="${3:-}"
if [ -z "$URL_LIST" ] && [ -f "$ARGOSY/pipeline/${SITE}_url_list.txt" ]; then
    URL_LIST="$ARGOSY/pipeline/${SITE}_url_list.txt"
fi

run_download() {
    echo "--- [1/3] download (site=$SITE) ---" | tee -a "$LOG"
    # Profile indices (start/peak/end per profile) are a REQUIRED input for sharding
    # but are hand-maintained CSVs kept OUTSIDE the download (and outside git's data
    # tree). A fresh box (EC2/CI) has none, which makes sharding silently produce
    # attempted=0 (load_profile_indices() returns None -> every shard is skipped).
    # Pull them from S3 here so every provisioned box has them before shard runs.
    # One-time per site: push them up with
    #   aws s3 sync ~/ooi/<site>/profileIndices/ s3://s3ooi/<site>/profileIndices/
    echo "--- pulling profileIndices from S3 (site=$SITE) ---" | tee -a "$LOG"
    mkdir -p "$HOME/ooi/$SITE/profileIndices"
    aws s3 sync "s3://s3ooi/$SITE/profileIndices/" "$HOME/ooi/$SITE/profileIndices/" 2>&1 | tee -a "$LOG"
    idx_count=$(find "$HOME/ooi/$SITE/profileIndices" -name '*_profiles_*.csv' 2>/dev/null | wc -l)
    if [ "$idx_count" -eq 0 ]; then
        echo "WARNING: no profile-index CSVs under ~/ooi/$SITE/profileIndices/ after S3 sync." | tee -a "$LOG"
        echo "         Sharding will produce attempted=0. Push them first:" | tee -a "$LOG"
        echo "         aws s3 sync ~/ooi/$SITE/profileIndices/ s3://s3ooi/$SITE/profileIndices/" | tee -a "$LOG"
    else
        echo "  profileIndices present: $idx_count file(s)" | tee -a "$LOG"
    fi

    if [ -n "$URL_LIST" ]; then
        python pipeline/download.py --site "$SITE" --url-list "$URL_LIST" 2>&1 | tee -a "$LOG"
    else
        python pipeline/download.py --site "$SITE" 2>&1 | tee -a "$LOG"
    fi
}

run_shard() {
    echo "--- [2/3] shard (site=$SITE) ---" | tee -a "$LOG"
    # Sharding needs profile indices; without them it silently produces attempted=0.
    # Guard here too, since `shard` may be run as a standalone stage (download skipped).
    idx_count=$(find "$HOME/ooi/$SITE/profileIndices" -name '*_profiles_*.csv' 2>/dev/null | wc -l)
    if [ "$idx_count" -eq 0 ]; then
        echo "WARNING: no profile-index CSVs under ~/ooi/$SITE/profileIndices/ — sharding will" | tee -a "$LOG"
        echo "         produce attempted=0. Pull them first:" | tee -a "$LOG"
        echo "         aws s3 sync s3://s3ooi/$SITE/profileIndices/ ~/ooi/$SITE/profileIndices/" | tee -a "$LOG"
    fi
    python pipeline/shard.py --site "$SITE" 2>&1 | tee -a "$LOG"
}

run_pp() {
    echo "--- [3/3] post-process pp05 -> pp06 (site=$SITE) ---" | tee -a "$LOG"
    # These scripts default SITE via ooipaths.DEFAULT_SITE. To target another site,
    # set it explicitly. Simplest robust approach: run in a subshell exporting the site
    # the scripts honor. (postprocess_*.py currently read SITE = op.DEFAULT_SITE at import;
    # for multi-site they should accept --site or read $ARGOSY_SITE — a small TODO.)
    ARGOSY_SITE="$SITE" python postprocess_pp05.py 2>&1 | tee -a "$LOG"
    ARGOSY_SITE="$SITE" python postprocess_pp06.py 2>&1 | tee -a "$LOG"
    ARGOSY_SITE="$SITE" python postprocess_pp06_filter2.py 2>&1 | tee -a "$LOG"
    ARGOSY_SITE="$SITE" python postprocess_pp06_filter3.py 2>&1 | tee -a "$LOG"
}

run_sync() {
    echo "--- sync results to S3 (site=$SITE) ---" | tee -a "$LOG"
    aws s3 sync "$HOME/ooi/$SITE/redux/"    "s3://s3ooi/$SITE/redux/"    2>&1 | tee -a "$LOG"
    aws s3 sync "$HOME/ooi/$SITE/postproc/" "s3://s3ooi/$SITE/postproc/" 2>&1 | tee -a "$LOG"
    aws s3 sync "$HOME/ooi/$SITE/metadata/" "s3://s3ooi/$SITE/metadata/" 2>&1 | tee -a "$LOG"
    # Note: raw ooinet/ is large; back it up separately/deliberately (see DataOps.md), not here.
}

case "$STAGE" in
    download) run_download ;;
    shard)    run_shard ;;
    pp)       run_pp ;;
    sync)     run_sync ;;
    all)      run_download && run_shard && run_pp && run_sync ;;
    *) echo "unknown stage: $STAGE"; exit 1 ;;
esac

echo "=== pipeline done (site=$SITE stage=$STAGE) === log: $LOG" | tee -a "$LOG"
