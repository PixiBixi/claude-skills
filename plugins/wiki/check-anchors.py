#!/usr/bin/env python3
"""Check that every wiki.jdelgado.fr URL and anchor cited by the wiki skills exists on the published site.

A renamed heading changes its anchor and the skill keeps citing a dead link: nothing else catches it.
Reads plugins/wiki/skills/**/*.md and understands three citation forms:
  - full URLs: https://wiki.jdelgado.fr/<path>/#<anchor>
  - an article letter declared as "- T = <url>" or "- T: <url>", then "T #<anchor>" anywhere
  - bare "- #<anchor>" list items under an "Anchors for T" line
Exit 1 when a page or an anchor is missing, 2 when the site cannot be fetched.

With --site DIR, reads a local MkDocs build instead of the published site: the wiki CI runs it
before deploying, so a heading rename fails there instead of breaking the citation silently.
"""

import argparse
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"
BASE = "https://wiki.jdelgado.fr/"

URL_RE = re.compile(r"https://wiki\.jdelgado\.fr/[^\s<>)|`\"']*")
LEGEND_RE = re.compile(r"^- ([A-Z]) *[=:] *<(https://wiki\.jdelgado\.fr/[^>]+)>")
LETTER_REF_RE = re.compile(r"(?<![\w#])([A-Z]) +#([a-z0-9][a-z0-9-]*)")
ANCHORS_FOR_RE = re.compile(r"^Anchors for ([A-Z])\b")
BARE_ANCHOR_RE = re.compile(r"^- #([a-z0-9][a-z0-9-]*)")


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, _tag, attrs):
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)


def collect(path):
    """Return {(page_url, anchor or None): [locations]} cited by one file."""
    letters, refs, current = {}, {}, None
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        m = LEGEND_RE.match(line)
        if m:
            letters[m.group(1)] = m.group(2)
    for n, line in enumerate(lines, 1):
        where = f"{path.relative_to(SKILLS_DIR)}:{n}"
        for url in URL_RE.findall(line):
            page, _, anchor = url.partition("#")
            refs.setdefault((page, anchor or None), []).append(where)
        m = ANCHORS_FOR_RE.match(line)
        if m:
            current = m.group(1)
        elif line.startswith("#"):
            current = None
        m = BARE_ANCHOR_RE.match(line)
        if m and current in letters:
            refs.setdefault((letters[current], m.group(1)), []).append(where)
        for letter, anchor in LETTER_REF_RE.findall(line):
            if letter in letters:
                refs.setdefault((letters[letter], anchor), []).append(where)
    return refs


def parse_ids(html):
    parser = IdCollector()
    parser.feed(html)
    return parser.ids


def fetch_ids(url):
    req = urllib.request.Request(url, headers={"User-Agent": "claude-skills-anchor-check"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return parse_ids(resp.read().decode("utf-8", "replace"))


def local_page(site, url):
    """Map a published URL to its file in a MkDocs build (use_directory_urls)."""
    rel = url[len(BASE):].split("?", 1)[0]
    return site / rel / "index.html" if not rel or rel.endswith("/") else site / rel


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", type=Path, help="local MkDocs build to check instead of the published site")
    args = ap.parse_args()

    refs = {}
    for path in sorted(SKILLS_DIR.rglob("*.md")):
        for key, where in collect(path).items():
            refs.setdefault(key, []).extend(where)
    if not refs:
        print(f"No wiki citation found under {SKILLS_DIR}", file=sys.stderr)
        return 2

    pages, errors = {}, []
    for page in sorted({p for p, _ in refs}):
        if args.site:
            path = local_page(args.site, page)
            if path.is_file():
                pages[page] = parse_ids(path.read_text(encoding="utf-8", errors="replace"))
            else:
                pages[page] = None
                errors.append(f"{page}: page missing in {args.site}")
            continue
        try:
            pages[page] = fetch_ids(page)
        except urllib.error.HTTPError as e:
            pages[page] = None
            errors.append(f"{page}: HTTP {e.code}")
        except urllib.error.URLError as e:
            print(f"Cannot reach {page}: {e.reason}", file=sys.stderr)
            return 2

    for (page, anchor), where in sorted(refs.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        if anchor and pages.get(page) is not None and anchor not in pages[page]:
            errors.append(f"{page}#{anchor}: anchor missing (cited at {', '.join(sorted(set(where)))})")

    anchors = sum(1 for _, a in refs if a)
    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} broken of {anchors} anchors on {len(pages)} pages")
        return 1
    print(f"OK: {anchors} anchors on {len(pages)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
