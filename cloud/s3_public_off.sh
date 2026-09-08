#!/usr/bin/env bash
# s3_public_off.sh — KILL SWITCH. Removes ALL public access to the s3ooi bucket.
# Run this the moment the budget alarm fires (or any suspected egress abuse).
# Deletes the bucket policy entirely -> no unauthenticated GetObject/ListBucket.
# Your own IAM/root access is unaffected (that comes from IAM, not the bucket policy).
# To reopen the intended public pp06 access afterward: run s3_public_on.sh.
set -euo pipefail
echo "KILL SWITCH: removing the s3ooi bucket policy (cuts ALL public access) ..."
aws s3api delete-bucket-policy --bucket s3ooi
echo "Done. Verifying no public policy remains:"
if aws s3api get-bucket-policy --bucket s3ooi >/dev/null 2>&1; then
    echo "WARNING: a bucket policy still exists — inspect manually:"
    aws s3api get-bucket-policy --bucket s3ooi --query Policy --output text
else
    echo "OK: no bucket policy present. Public access is OFF."
fi
