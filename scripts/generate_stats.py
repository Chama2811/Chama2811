#!/usr/bin/env python3
"""Generate GitHub profile statistics SVGs using GitHub's APIs."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "Chama2811")
TOKEN = os.environ.get("GITHUB_TOKEN")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

BG, PANEL = "#1b1b2f", "#20243a"
TEXT, MUTED = "#e6edf3", "#9da7b3"
PINK, PURPLE, BLUE, GREEN = "#e879a9", "#a78bfa", "#79a8ff", "#43d9bd"
GRID = "#30364d"


def request_json(url, method="GET", payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Chama2811-GitHub-Profile-Updater",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_repositories():
    repos, page = [], 1
    while True:
        url = (
            f"https://api.github.com/users/{urllib.parse.quote(USERNAME)}"
            f"/repos?type=owner&per_page=100&page={page}&sort=updated"
        )
        batch = request_json(url)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def get_contribution_calendar():
    if not TOKEN:
        print("GITHUB_TOKEN unavailable; skipping contribution calendar.")
        return None, []
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    try:
        result = request_json(
            "https://api.github.com/graphql",
            method="POST",
            payload={"query": query, "variables": {"login": USERNAME}},
        )
        if result.get("errors"):
            raise RuntimeError(json.dumps(result["errors"]))
        calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
        return int(calendar["totalContributions"]), days
    except Exception as exc:
        print(f"Contribution calendar unavailable: {exc}")
        return None, []


def svg_start(width, height, title):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<rect width="100%" height="100%" rx="16" fill="{BG}"/>
<style>
  text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  .title {{ fill: {TEXT}; font-size: 21px; font-weight: 700; }}
  .muted {{ fill: {MUTED}; font-size: 12px; }}
  .value {{ font-size: 31px; font-weight: 700; }}
  .label {{ fill: {TEXT}; font-size: 13px; }}
</style>
"""


def write_svg(name, content):
    path = ASSETS / name
    path.write_text(content + "\n", encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}")


def make_stats_card(repo_count, stars, forks, contributions):
    items = [
        ("Public repositories", repo_count, PINK),
        ("Total stars", stars, BLUE),
        ("Total forks", forks, GREEN),
        ("Contributions this year", contributions if contributions is not None else "—", PURPLE),
    ]
    svg = [svg_start(760, 250, "GitHub statistics")]
    svg.append('<text x="30" y="42" class="title">GitHub Statistics</text>')
    updated = datetime.now(timezone.utc).strftime("%d %b %Y")
    svg.append(f'<text x="30" y="66" class="muted">@{escape(USERNAME)} · Updated {updated} UTC</text>')
    for i, (label, value, color) in enumerate(items):
        x = 30 + i * 185
        svg.append(f'<rect x="{x}" y="88" width="165" height="125" rx="12" fill="{PANEL}" stroke="{GRID}"/>')
        svg.append(f'<text x="{x+16}" y="143" class="value" fill="{color}">{escape(str(value))}</text>')
        svg.append(f'<text x="{x+16}" y="174" class="label">{escape(label)}</text>')
    svg.append('<text x="30" y="235" class="muted">Generated automatically with GitHub Actions</text>')
    svg.append("</svg>")
    write_svg("github-stats.svg", "\n".join(svg))


def make_languages_card(language_bytes):
    total = sum(language_bytes.values())
    sorted_langs = sorted(language_bytes.items(), key=lambda item: item[1], reverse=True)[:8]
    svg = [svg_start(760, 300, "Most used languages")]
    svg.append('<text x="30" y="42" class="title">Most Used Languages</text>')
    if not sorted_langs or total == 0:
        svg.append('<text x="30" y="100" class="label">No language data is available yet.</text>')
    else:
        palette = [PINK, BLUE, GREEN, PURPLE, "#f0c674", "#e06c75", "#56b6c2", "#c678dd"]
        bar_x, bar_y, bar_w = 30, 70, 700
        current_x = bar_x
        for i, (_, amount) in enumerate(sorted_langs):
            segment = bar_w * amount / total
            svg.append(f'<rect x="{current_x:.2f}" y="{bar_y}" width="{segment:.2f}" height="15" fill="{palette[i % len(palette)]}"/>')
            current_x += segment
        for i, (language, amount) in enumerate(sorted_langs):
            col, row = i % 2, i // 2
            x, y = 35 + col * 360, 125 + row * 39
            pct, color = amount / total * 100, palette[i % len(palette)]
            svg.append(f'<circle cx="{x}" cy="{y-4}" r="5" fill="{color}"/>')
            svg.append(f'<text x="{x+14}" y="{y}" class="label">{escape(language)}</text>')
            svg.append(f'<text x="{x+320}" y="{y}" text-anchor="end" class="muted">{pct:.1f}%</text>')
    svg.append('<text x="30" y="282" class="muted">Based on language bytes across public repositories; not a measure of skill.</text>')
    svg.append("</svg>")
    write_svg("top-languages.svg", "\n".join(svg))


def make_contributions_card(total, days):
    svg = [svg_start(760, 190, "GitHub contribution activity")]
    svg.append('<text x="30" y="38" class="title">Contribution Activity</text>')
    if not days:
        svg.append('<text x="30" y="90" class="label">Contribution calendar could not be loaded.</text>')
        svg.append('<text x="30" y="118" class="muted">Repository and language cards can still update normally.</text>')
    else:
        days = days[-364:]
        max_count = max((int(day["contributionCount"]) for day in days), default=0)
        palette = ["#252b3b", "#173b35", "#176b50", "#1e9b68", "#43d9bd"]
        start_x, start_y, cell, gap = 30, 65, 9, 3
        for idx, day in enumerate(days):
            col, row = divmod(idx, 7)
            count = int(day["contributionCount"])
            ratio = count / max_count if max_count else 0
            level = 0 if count == 0 else 1 if ratio <= .25 else 2 if ratio <= .5 else 3 if ratio <= .75 else 4
            x, y = start_x + col * (cell + gap), start_y + row * (cell + gap)
            svg.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{palette[level]}">'
                f'<title>{escape(day["date"])}: {count} contributions</title></rect>'
            )
        svg.append(f'<text x="30" y="174" class="muted">Total contributions in GitHub calendar: {total}</text>')
        svg.append('<text x="730" y="174" text-anchor="end" class="muted">Last 52 weeks</text>')
    svg.append("</svg>")
    write_svg("contributions.svg", "\n".join(svg))


def main():
    print(f"Collecting public GitHub data for {USERNAME}...")
    repos = get_repositories()
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    forks = sum(int(repo.get("forks_count", 0)) for repo in repos)
    language_bytes = Counter()

    for repo in repos:
        if repo.get("languages_url"):
            try:
                language_bytes.update(request_json(repo["languages_url"]))
            except Exception as exc:
                print(f"Skipping language data for {repo.get('full_name')}: {exc}")

    contributions, days = get_contribution_calendar()
    make_stats_card(len(repos), stars, forks, contributions)
    make_languages_card(language_bytes)
    make_contributions_card(contributions, days)
    print(f"Done: {len(repos)} public repositories, {stars} stars, {forks} forks.")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {exc.code}: {detail}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Updater failed: {exc}", file=sys.stderr)
        sys.exit(1)
