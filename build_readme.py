#!/usr/bin/env python3
"""Rebuild the dynamic sections of the profile README.

Fills everything between the marker comments:
    <!-- ships:start --> ... <!-- ships:end -->
    <!-- oss:start -->   ... <!-- oss:end -->
    <!-- stats:start --> ... <!-- stats:end -->

Everything else in README.md is left untouched. Run weekly via
.github/workflows/build-readme.yml, or locally: python build_readme.py
"""
import json
import os
import re
import urllib.request

OWNER = "sharatchandrasai999-sketch"
REPOS = ["tokenlens", "extracteval"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-builder"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

ROOT = os.path.dirname(os.path.abspath(__file__))


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def ships_section():
    """Latest commits across the showcase repos, newest first."""
    entries = []
    for repo in REPOS:
        try:
            commits = api(f"/repos/{OWNER}/{repo}/commits?per_page=3")
        except Exception:
            continue
        for c in commits:
            msg = c["commit"]["message"].split("\n")[0].strip()
            if len(msg) > 58:
                msg = msg[:57] + "…"
            date = c["commit"]["author"]["date"][:10]
            short = c["sha"][:7]
            entries.append((date, repo, short, msg, c["html_url"]))
    entries.sort(reverse=True)
    lines = [
        f"[{repo}@{short} — {msg}]({url}) · {date}"
        for date, repo, short, msg, url in entries[:6]
    ]
    return "\n\n".join(lines) if lines else "_No recent commits found._"


def oss_section():
    """Live status of the simonw/llm contribution."""
    try:
        pr = api("/repos/simonw/llm/pulls/1726")
        state = pr["state"]
        merged = pr.get("merged_at")
        status = "merged 🎉" if merged else ("open" if state == "open" else state)
        title = pr["title"].strip()
        if len(title) > 70:
            title = title[:69] + "…"
        line1 = f"[simonw/llm#1726]({pr['html_url']}) — **{status}**"
        line2 = f"_{title}_"
    except Exception:
        line1 = "[simonw/llm#1726](https://github.com/simonw/llm/pull/1726)"
        line2 = "_Could not fetch live status._"
    line3 = (
        "Validates embedding counts per batch (a model returning the wrong "
        "count used to silently drop entries) plus three regression tests."
    )
    return "\n\n".join([line1, line2, line3])


def stats_section():
    """Verified numbers from data.json (kept in sync by hand on each release)."""
    try:
        with open(os.path.join(ROOT, "data.json")) as f:
            data = json.load(f)
    except Exception:
        return "_Stats unavailable._"
    bits = []
    tests = int(data.get("tokenlens_tests", 0)) + int(data.get("extracteval_tests", 0))
    if tests:
        bits.append(f"**{tests}** tests passing across both repos")
    if data.get("tokenlens_models"):
        bits.append(f"**{data['tokenlens_models']}** models priced in tokenlens")
    if data.get("tokenlens_version"):
        bits.append(f"tokenlens **v{data['tokenlens_version']}**")
    bits.append("**1** upstream PR to simonw/llm")
    return " · ".join(bits)


def fill(readme, name, content):
    pattern = re.compile(
        rf"<!-- {name}:start -->.*?<!-- {name}:end -->", re.DOTALL
    )
    replacement = f"<!-- {name}:start -->\n{content}\n<!-- {name}:end -->"
    return pattern.sub(replacement, readme)


def main():
    path = os.path.join(ROOT, "README.md")
    with open(path) as f:
        readme = f.read()
    readme = fill(readme, "ships", ships_section())
    readme = fill(readme, "oss", oss_section())
    readme = fill(readme, "stats", stats_section())
    with open(path, "w") as f:
        f.write(readme)
    print("README rebuilt.")


if __name__ == "__main__":
    main()
