#!/usr/bin/env bash
# s3_public_on.sh — (RE)OPEN public read on pp06 for all 3 sites.
# Applies ~/argosy/s3_public_read_policy.json to the s3ooi bucket.
# This is the normal/intended state; use s3_public_off.sh as the kill switch.
set -euo pipefail
POLICY="$HOME/argosy/s3_public_read_policy.json"
[ -f "$POLICY" ] || { echo "missing $POLICY"; exit 1; }
echo "Applying PUBLIC pp06 policy to s3ooi ..."
aws s3api put-bucket-policy --bucket s3ooi --policy "file://$POLICY"
echo "Done. Live policy now:"
aws s3api get-bucket-policy --bucket s3ooi --query Policy --output text
