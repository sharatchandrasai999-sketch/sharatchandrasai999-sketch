#!/usr/bin/env python3
"""Rebuild the dynamic sections of the profile README.

Fills everything between the marker comments:
    <!-- oss:start -->   ... <!-- oss:end -->
    <!-- stats:start --> ... <!-- stats:end -->

Everything else in README.md is left untouched. Run weekly via
.github/workflows/build-readme.yml, or locally: python build_readme.py
"""
import json
import os
import re
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-builder"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

ROOT = os.path.dirname(os.path.abspath(__file__))


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def oss_section():
    """Live status of the simonw/llm contribution."""
    try:
        pr = api("/repos/simonw/llm/pulls/1726")
        state = pr["state"]
        merged = pr.get("merged_at")
        status = "merged" if merged else ("open" if state == "open" else state)
        line1 = f"[**simonw/llm#1726**]({pr['html_url']}) — {status}"
    except Exception:
        line1 = "[**simonw/llm#1726**](https://github.com/simonw/llm/pull/1726)"
    line2 = (
        "Per-batch embedding-count validation: a model returning the wrong number "
        "of embeddings used to have entries silently dropped — now it fails loudly, "
        "with three regression tests."
    )
    return "\n\n".join([line1, line2])


def stats_section():
    """Verified numbers from data.json (kept in sync by hand on each release)."""
    try:
        with open(os.path.join(ROOT, "data.json")) as f:
            data = json.load(f)
    except Exception:
        return ""
    bits = []
    tests = int(data.get("tokenlens_tests", 0)) + int(data.get("extracteval_tests", 0))
    if tests:
        bits.append(f"**{tests}** tests passing")
    if data.get("tokenlens_models"):
        bits.append(f"**{data['tokenlens_models']}** models priced")
    if data.get("tokenlens_version"):
        bits.append(f"tokenlens **v{data['tokenlens_version']}**")
    bits.append("**1** upstream OSS contribution")
    return " · ".join(bits)


def fill(readme, name, content):
    pattern = re.compile(rf"<!-- {name}:start -->.*?<!-- {name}:end -->", re.DOTALL)
    replacement = f"<!-- {name}:start -->\n{content}\n<!-- {name}:end -->"
    return pattern.sub(replacement, readme)


def main():
    path = os.path.join(ROOT, "README.md")
    with open(path) as f:
        readme = f.read()
    readme = fill(readme, "oss", oss_section())
    readme = fill(readme, "stats", stats_section())
    with open(path, "w") as f:
        f.write(readme)
    print("README rebuilt.")


if __name__ == "__main__":
    main()
