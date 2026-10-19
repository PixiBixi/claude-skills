#!/usr/bin/env bash
# Capture a page at 375, 768, 1440 and 2560px, in light and dark, with the Playwright CLI on the installed Chrome.
# Usage: screenshot.sh <url> <out-dir> [height]
# Output: <out-dir>/<width>-<light|dark>.png
set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "usage: $0 <url> <out-dir> [height]" >&2
    exit 2
fi

url=$1
out_dir=$2
height=${3:-900}
chrome=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
playwright=playwright@1.56.1

if [[ ! -x $chrome ]]; then
    echo "Chrome not found at $chrome (set CHROME=...)" >&2
    exit 1
fi

# CDNs and WAFs answer a "HeadlessChrome" user agent with a 403/404 page or no CSS: send the desktop one.
version=$("$chrome" --version | grep -Eo '[0-9]+(\.[0-9]+)+' | head -1)
ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${version} Safari/537.36"

# A blocked or missing page still renders: refuse to capture it.
if [[ $url == http* ]]; then
    status=$(curl -sS -o /dev/null -w '%{http_code}' -A "$ua" -L "$url" || echo 000)
    if [[ $status != 2* ]]; then
        echo "HTTP $status for $url (bot protection or wrong URL): nothing captured" >&2
        exit 1
    fi
fi

mkdir -p "$out_dir"

for theme in light dark; do
    for width in 375 768 1440 2560; do
        shot="$out_dir/$width-$theme.png"
        rm -f "$shot"
        # Playwright sets a real viewport: headless Chrome's own --window-size lays out at 500px minimum and crops.
        timeout 90 npx -y "$playwright" screenshot --channel=chrome \
            --viewport-size="$width,$height" \
            --color-scheme="$theme" \
            --user-agent="$ua" \
            --wait-for-timeout=3000 \
            "$url" "$shot" > /dev/null 2>&1 || true
        if [[ ! -s $shot ]]; then
            echo "FAILED $shot" >&2
            continue
        fi
        echo "$shot"
    done
done
