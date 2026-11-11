#!/usr/bin/env python3
"""Check SKILL.md frontmatter against the claude.ai (Cowork) sync rules.

claude.ai reads frontmatter more strictly than Claude Code and silently drops
a skill it cannot read. Rejected here:
  - a description holding anything shaped like an XML tag (<env>): write {env}
  - a description longer than 1024 characters, as YAML reads it
  - a block scalar (key: | or key: >) on any key but description

Usage: check-frontmatter.py [SKILL.md ...]   (default: every SKILL.md in the repo)
"""

import re
import sys
from pathlib import Path

MAX_DESCRIPTION = 1024
TAG = re.compile(r"<[A-Za-z/!?][^<>]*>")
KEY = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
BLOCK = re.compile(r"^[|>][+-]?\d*$")


def frontmatter(text):
    """Return the lines of the first frontmatter block, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:end]
    return None


def top_level(lines):
    """Yield (key, inline value, continuation lines) for each top-level key."""
    key, value, rest = None, "", []
    for line in lines:
        match = KEY.match(line)
        if match:
            if key:
                yield key, value, rest
            key, value, rest = match.group(1), match.group(2).strip(), []
        elif key:
            rest.append(line)
    if key:
        yield key, value, rest


def description_text(value, rest):
    """Approximate the description string YAML would produce."""
    body = [line.strip() for line in rest if line.strip()]
    if BLOCK.match(value):
        sep = "\n" if value.startswith("|") else " "
        return sep.join(body)
    text = " ".join([value, *body]).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        text = text[1:-1]
    return text


def check(path):
    errors = []
    lines = frontmatter(path.read_text(encoding="utf-8"))
    if lines is None:
        return [f"{path}: no frontmatter block"]
    for key, value, rest in top_level(lines):
        if key == "description":
            text = description_text(value, rest)
            tag = TAG.search(text)
            if tag:
                placeholder = "{" + tag.group(0).strip("<>/!?") + "}"
                errors.append(f"{path}: description holds the XML-like tag {tag.group(0)}, write it as {placeholder}")
            if len(text) > MAX_DESCRIPTION:
                errors.append(f"{path}: description is {len(text)} characters, max {MAX_DESCRIPTION}")
        elif BLOCK.match(value):
            errors.append(f"{path}: '{key}' is a block scalar, only description may be one")
    return errors


def main(argv):
    root = Path(__file__).resolve().parent.parent
    paths = [Path(arg) for arg in argv] or sorted([*root.glob("skills/*/SKILL.md"), *root.glob("plugins/*/skills/*/SKILL.md")])
    errors = [error for path in paths for error in check(path)]
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
