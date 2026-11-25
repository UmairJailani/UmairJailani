"""Refresh the "Recently" section of the profile README.

Reads only public data: latest notes published by the Second Brain showcase,
and my most recently updated public repositories. Run daily by
.github/workflows/update-readme.yml.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

USER = "UmairJailani"
SKIP = {USER, "Anthropic-s-courses"}
README = Path(__file__).resolve().parents[1] / "README.md"


def get(url: str, raw: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-updater"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    return body if raw else json.loads(body)


def latest_notes(limit: int = 3) -> list[str]:
    try:
        index = get(f"https://raw.githubusercontent.com/{USER}/second-brain-showcase/main/notes/README.md", raw=True)
    except Exception:
        return []
    rows = re.findall(r"^\| \[([^\]]+)\]\(([^)]+)\) \| [^|]* \| ([^|]*) \|$", index, re.M)
    return [
        f"- 🧠 [{title}](https://github.com/{USER}/second-brain-showcase/blob/main/notes/{link}) · {date.strip()}"
        for title, link, date in rows[:limit]
    ]


def recent_repos(limit: int = 4) -> list[str]:
    repos = get(f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30")
    out = []
    for r in repos:
        if r["name"] in SKIP or r["fork"] or r["archived"] or r["private"]:
            continue
        desc = (r.get("description") or "").split(". ")[0]
        out.append(f"- 🔧 [{r['name']}]({r['html_url']}): {desc} · updated {r['pushed_at'][:10]}")
        if len(out) == limit:
            break
    return out


def main() -> None:
    lines = latest_notes() + recent_repos()
    block = "\n".join(lines) if lines else "- (nothing new)"
    text = README.read_text(encoding="utf-8")
    new = re.sub(r"(<!-- recent starts -->\n).*?(<!-- recent ends -->)", lambda m: m.group(1) + block + "\n" + m.group(2), text, flags=re.S)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README updated")
    else:
        print("No change")


if __name__ == "__main__":
    main()
