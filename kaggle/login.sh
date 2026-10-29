#!/usr/bin/env bash
# Kaggle CLI login for GitHub Actions steps (sourced logic moved here from kaggle-test.yml so every
# workflow logs in the same way). Needs KAGGLE_USERNAME and KAGGLE_API_TOKEN; writes to $GITHUB_ENV.
# Two kinds of Kaggle keys (run 40854367716 was refused): the new API token, or the legacy key from
# kaggle.json (32 hex characters, used together with the username). Only the kind and length are printed.
set -e
[ -n "$KAGGLE_USERNAME" ] && [ -n "$KAGGLE_API_TOKEN" ] || { echo "Add repo secrets KAGGLE_USERNAME and KAGGLE_API_TOKEN first"; exit 1; }
pip install -q kaggle && kaggle --version
tok=$(printf '%s' "$KAGGLE_API_TOKEN" | tr -d '[:space:]"')
if [[ "$tok" =~ ^[0-9a-f]{32}$ ]]; then
  echo "key kind: legacy kaggle.json key (length ${#tok})"
  echo "KAGGLE_KEY=$tok" >> "$GITHUB_ENV"; echo "KAGGLE_API_TOKEN=" >> "$GITHUB_ENV"
  export KAGGLE_KEY="$tok" KAGGLE_API_TOKEN=
else
  echo "key kind: new API token (length ${#tok})"
  mkdir -p ~/.kaggle && printf '%s' "$tok" > ~/.kaggle/access_token && chmod 600 ~/.kaggle/access_token
  echo "KAGGLE_API_TOKEN=$tok" >> "$GITHUB_ENV"
fi
kaggle kernels list --mine --page-size 1 > /dev/null && echo "login ok"
