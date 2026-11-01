#!/usr/bin/env bash
# Prints one block per finding type from an audit's JSONL rows.
set -euo pipefail

dir="${1:-}"
if [[ -z ${dir} ]]; then
    echo "usage: summary.sh <AUDIT_DIR>" >&2
    exit 2
fi
rows="${dir}/audit.jsonl"
if [[ ! -s ${rows} ]]; then
    echo "no rows in ${rows}" >&2
    exit 2
fi

echo '## Games'
jq -r 'select(.kind=="turns") | "\(.project): \(.moves) moves, action on one screen \(.together)/\(.turns), median spread \(.medianSpread)px for vh \(.vh), unseen \(.unseen)"' "${rows}"

echo '## Covered controls'
jq -r 'select(.kind=="covered") | "\(.project): \(.control) covered by \(.by)"' "${rows}" | sort | uniq -c

echo '## Dialogs that do not fit'
jq -r 'select(.kind=="dialog" and .fits==false) | "\(.project) \(.name): buttons on screen \([.buttons[] | .onScreen])"' "${rows}"

echo '## Per screen'
jq -r 'select(.screen) | "\(.project) \(.screen): overflow \(.overflowX | length), small targets \(.smallTargets | length), tiny text \(.tinyText | length)"' "${rows}"

echo '## Text inputs under 16px (iOS zooms on focus)'
jq -r 'select(.screen) | .project as $p | .textInputs[] | select((capture("(?<px>[0-9.]+)px$").px | tonumber) < 16) | "\($p): \(.)"' "${rows}" | sort -u
