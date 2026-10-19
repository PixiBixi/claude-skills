#!/usr/bin/env python3
"""Group a live site's URLs into page templates, with a count and a sample URL each.

Reads /robots.txt for Sitemap: lines, falls back to /sitemap.xml, follows nested
sitemap indexes. Without any sitemap, crawls the home page links (nav and footer).

Usage: sitemap-inventory.py https://example.org
"""
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (sitemap-inventory)"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
MAX_SITEMAPS = 50
MAX_BYTES = 10 * 1024 * 1024


def same_site(url, base):
    """Sitemap URLs come from the remote site: only follow http(s) on the base host."""
    u, b = urlparse(url), urlparse(base)
    return u.scheme in ("http", "https") and u.netloc == b.netloc


BLOCKED = []  # (url, status) answered 401/403/429: bot protection, not a missing sitemap


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(MAX_BYTES)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 429):
            BLOCKED.append((url, exc.code))
        print(f"# skip {url}: {exc}", file=sys.stderr)
        return None
    except Exception as exc:  # network errors only change the fallback path
        print(f"# skip {url}: {exc}", file=sys.stderr)
        return None
    if body[:2] == b"\x1f\x8b":
        # sitemap.xml.gz: bounded inflate, the remote file could be a gzip bomb.
        body = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(body, MAX_BYTES)
    return body.decode("utf-8", errors="replace")


def sitemap_urls(base):
    robots = fetch(urljoin(base, "/robots.txt")) or ""
    found = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
    return found or [urljoin(base, "/sitemap.xml")]


def read_sitemaps(roots, base):
    pages, queue, seen = [], list(roots), set()
    while queue and len(seen) < MAX_SITEMAPS:
        url = queue.pop(0)
        if url in seen or not same_site(url, base):
            continue
        seen.add(url)
        body = fetch(url)
        if not body:
            continue
        try:
            tree = ET.fromstring(body)
        except ET.ParseError:
            print(f"# skip {url}: not XML", file=sys.stderr)
            continue
        locs = [e.text.strip() for e in tree.iter(f"{NS}loc") if e.text]
        if tree.tag == f"{NS}sitemapindex":
            queue.extend(locs)
        else:
            pages.extend(locs)
    return pages


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def crawl_home(base):
    body = fetch(base) or ""
    parser = Links()
    parser.feed(body)
    host = urlparse(base).netloc
    urls = {urljoin(base, h).split("#")[0] for h in parser.hrefs}
    return sorted(u for u in urls if urlparse(u).netloc == host)


def template_of(url):
    """First path segment, plus a marker when the URL goes deeper (detail pages)."""
    parts = [p for p in urlparse(url).path.split("/") if p]
    if not parts:
        return "/ (home)"
    if len(parts) == 1:
        return f"/{parts[0]}"
    return f"/{parts[0]}/* (depth {len(parts)})"


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith(("http://", "https://")):
        sys.exit("usage: sitemap-inventory.py https://example.org")
    base = sys.argv[1].rstrip("/") + "/"

    pages = read_sitemaps(sitemap_urls(base), base)
    source = "sitemap"
    if not pages:
        pages, source = crawl_home(base), "home page links (no sitemap)"

    groups = defaultdict(list)
    for url in dict.fromkeys(pages):
        groups[template_of(url)].append(url)

    if BLOCKED:
        codes = ", ".join(f"{code} {url}" for url, code in BLOCKED)
        print(f"# BLOCKED (bot protection, inventory incomplete): {codes}")
    print(f"# {len(pages)} URLs from {source}")
    print("template\tcount\tsamples")
    for tpl, urls in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        # First, middle and last: a URL group often mixes hub and detail templates.
        samples = list(dict.fromkeys([urls[0], urls[len(urls) // 2], urls[-1]]))
        print(f"{tpl}\t{len(urls)}\t{' '.join(samples)}")
    if BLOCKED and not pages:
        sys.exit(1)


if __name__ == "__main__":
    main()
