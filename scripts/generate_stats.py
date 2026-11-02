#!/usr/bin/env python3
"""Generate GitHub profile statistics SVGs using Chamathka's pink mix color theme."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = os.environ.get("GITHUB_USERNAME", "Chama2811")
TOKEN = os.environ.get("GITHUB_TOKEN")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Chamathka's Pink Mix Palette
BG_DARK = "#0d1117"
PANEL_DARK = "#161b22"
BORDER_DARK = "#30363d"
PINK = "#e879a9"
PINK_GLOW = "#f9a8d4"
PURPLE = "#a78bfa"
ICE_BLUE = "#79a8ff"
TEAL = "#43d9bd"
TEXT_PRIMARY = "#f0f6fc"
TEXT_SECONDARY = "#c9d1d9"
TEXT_MUTED = "#8b949e"


def request_json(url, method="GET", payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"{USERNAME}-profile-analytics",
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


def get_user_data():
    return request_json(f"https://api.github.com/users/{urllib.parse.quote(USERNAME)}")


def get_contribution_calendar():
    if not TOKEN:
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
        print(f"GraphQL calendar error: {exc}")
        return None, []


def make_github_stats(total_stars, total_commits=29):
    w, h = 467, 195
    svg = f"""<svg
  width="{w}"
  height="{h}"
  viewBox="0 0 {w} {h}"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  role="img"
  aria-label="Chamathka Shehani's GitHub Stats"
>
  <style>
    .header {{
      font: 700 17px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: {PINK};
    }}
    .stat-label {{
      font: 600 13px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: {TEXT_SECONDARY};
    }}
    .stat-value {{
      font: 700 13px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: {TEXT_PRIMARY};
    }}
    .icon {{
      fill: {PINK};
    }}
    .rank-circle-rim {{
      stroke: {BORDER_DARK};
      fill: none;
      stroke-width: 6;
      opacity: 0.6;
    }}
    .rank-circle {{
      stroke: {PINK};
      stroke-dasharray: 250;
      stroke-dashoffset: 80;
      fill: none;
      stroke-width: 6;
      stroke-linecap: round;
      transform-origin: 0px 0px;
      transform: rotate(-90deg);
    }}
  </style>

  <rect width="100%" height="100%" rx="12" fill="{BG_DARK}" stroke="{BORDER_DARK}" stroke-width="1"/>

  <text x="25" y="35" class="header">Chamathka Shehani's GitHub Stats</text>

  <g transform="translate(25, 48)">
    <g transform="translate(0, 16)">
      <path class="icon" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z" transform="scale(0.85)"/>
      <text x="22" y="11" class="stat-label">Total Stars Earned:</text>
      <text x="175" y="11" class="stat-value">{total_stars}</text>
    </g>

    <g transform="translate(0, 40)">
      <path class="icon" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z" transform="scale(0.85)"/>
      <text x="22" y="11" class="stat-label">Total Commits:</text>
      <text x="175" y="11" class="stat-value">{total_commits}</text>
    </g>

    <g transform="translate(0, 64)">
      <path class="icon" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.128a2.251 2.251 0 11-1.5 0V6a2.5 2.5 0 00-2.5-2.5h-1V2h1a2.5 2.5 0 012.5 2.5v.128a2.251 2.251 0 011.5 0V5a2.5 2.5 0 00-2.5-2.5z" transform="scale(0.85)"/>
      <text x="22" y="11" class="stat-label">Total PRs:</text>
      <text x="175" y="11" class="stat-value">0</text>
    </g>

    <g transform="translate(0, 88)">
      <path class="icon" d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z" transform="scale(0.85)"/>
      <text x="22" y="11" class="stat-label">Total Issues:</text>
      <text x="175" y="11" class="stat-value">0</text>
    </g>

    <g transform="translate(0, 112)">
      <path class="icon" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8V1.5z" transform="scale(0.85)"/>
      <text x="22" y="11" class="stat-label">Contributed to (last year):</text>
      <text x="175" y="11" class="stat-value">0</text>
    </g>
  </g>

  <g transform="translate(385, 110)">
    <circle class="rank-circle-rim" cx="0" cy="0" r="38" />
    <circle class="rank-circle" cx="0" cy="0" r="38" />
    <path fill="{PINK}" transform="translate(-16, -17) scale(1.1)" d="M12 1.25C6.07 1.25 1.25 6.07 1.25 12c0 4.75 3.08 8.77 7.36 10.2.54.1.73-.23.73-.51v-1.81c-2.99.65-3.62-1.44-3.62-1.44-.49-1.24-1.2-1.57-1.2-1.57-.98-.67.07-.65.07-.65 1.08.08 1.65 1.11 1.65 1.11.96 1.65 2.52 1.17 3.13.9.1-.7.38-1.17.69-1.44-2.39-.27-4.9-1.2-4.9-5.32 0-1.18.42-2.14 1.11-2.9-.11-.27-.48-1.37.11-2.86 0 0 .9-.29 2.96 1.1a10.3 10.3 0 015.38 0c2.05-1.39 2.95-1.1 2.95-1.1.59 1.49.22 2.59.11 2.86.69.76 1.11 1.72 1.11 2.9 0 4.13-2.52 5.04-4.92 5.31.39.33.74.99.74 2v2.97c0 .29.19.62.74.51 4.27-1.44 7.34-5.46 7.34-10.2 0-5.93-4.82-10.75-10.75-10.75z"/>
  </g>
</svg>"""
    (ASSETS / "github-stats.svg").write_text(svg + "\n", encoding="utf-8")


def make_top_langs():
    w, h = 467, 195
    svg = f"""<svg
  width="{w}"
  height="{h}"
  viewBox="0 0 {w} {h}"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  role="img"
  aria-label="Most Used Languages"
>
  <style>
    .header {{
      font: 700 17px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: {PINK};
    }}
    .lang-name {{
      font: 600 13px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: {TEXT_SECONDARY};
    }}
    .lang-pct {{
      font: 600 13px 'Segoe UI', Ubuntu, -apple-system, sans-serif;
      fill: {TEXT_MUTED};
    }}
  </style>

  <rect width="100%" height="100%" rx="12" fill="{BG_DARK}" stroke="{BORDER_DARK}" stroke-width="1"/>

  <text x="25" y="35" class="header">Most Used Languages</text>

  <g transform="translate(25, 55)">
    <rect width="417" height="10" rx="5" fill="{PANEL_DARK}" stroke="{BORDER_DARK}" stroke-width="1"/>
    <rect width="417" height="10" rx="5" fill="{PINK}"/>
  </g>

  <g transform="translate(25, 90)">
    <g transform="translate(0, 0)">
      <circle cx="6" cy="6" r="5" fill="{PINK}"/>
      <text x="20" y="10" class="lang-name">Python</text>
      <text x="80" y="10" class="lang-pct">100.0%</text>
    </g>

    <g transform="translate(220, 0)">
      <circle cx="6" cy="6" r="5" fill="{PURPLE}"/>
      <text x="20" y="10" class="lang-name">C# / .NET</text>
      <text x="100" y="10" class="lang-pct">Learning</text>
    </g>

    <g transform="translate(0, 32)">
      <circle cx="6" cy="6" r="5" fill="{ICE_BLUE}"/>
      <text x="20" y="10" class="lang-name">SQL / DB</text>
      <text x="80" y="10" class="lang-pct">Exploring</text>
    </g>

    <g transform="translate(220, 32)">
      <circle cx="6" cy="6" r="5" fill="{TEAL}"/>
      <text x="20" y="10" class="lang-name">JavaScript</text>
      <text x="100" y="10" class="lang-pct">Practicing</text>
    </g>
  </g>
</svg>"""
    (ASSETS / "top-langs.svg").write_text(svg + "\n", encoding="utf-8")
    (ASSETS / "top-languages.svg").write_text(svg + "\n", encoding="utf-8")


def make_profile_metrics(public_repos, stars, followers, forks):
    values = [
        ("PUBLIC REPOS", str(public_repos)),
        ("STARS EARNED", str(stars)),
        ("FOLLOWERS", str(followers)),
        ("PUBLIC FORKS", str(forks))
    ]
    card_width = 210
    gap = 12
    padding = 16
    height = 112
    width = padding * 2 + card_width * 4 + gap * 3

    cards = []
    for i, (label, val) in enumerate(values):
        x = padding + i * (card_width + gap)
        cards.append(f"""
          <g transform="translate({x},16)">
            <rect
              width="{card_width}"
              height="80"
              rx="12"
              fill="{PANEL_DARK}"
              stroke="{BORDER_DARK}"
            />
            <text
              x="16"
              y="31"
              fill="{TEXT_MUTED}"
              font-size="12"
              font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"
              font-weight="700"
            >
              {escape(label)}
            </text>
            <text
              x="16"
              y="61"
              fill="{PINK}"
              font-size="25"
              font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"
              font-weight="700"
            >
              {escape(val)}
            </text>
          </g>
        """)

    svg = f"""<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{width}"
  height="{height}"
  viewBox="0 0 {width} {height}"
  role="img"
  aria-label="GitHub profile metrics"
>
  <rect
    width="100%"
    height="100%"
    rx="14"
    fill="#010409"
    stroke="{BORDER_DARK}"
    stroke-width="1"
  />
  {''.join(cards)}
</svg>"""
    (ASSETS / "profile-metrics.svg").write_text(svg + "\n", encoding="utf-8")


def make_streak_card():
    w, h = 495, 195
    svg = f"""<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{w}"
  height="{h}"
  viewBox="0 0 {w} {h}"
  role="img"
  aria-label="Contribution Streak"
>
  <style>
    .num {{
      font: 800 28px 'Segoe UI', Ubuntu, sans-serif;
      fill: {PINK};
      text-anchor: middle;
    }}
    .sub {{
      font: 600 12px 'Segoe UI', Ubuntu, sans-serif;
      fill: {TEXT_MUTED};
      text-anchor: middle;
    }}
    .date {{
      font: 500 10.5px 'Segoe UI', Ubuntu, sans-serif;
      fill: #6e7681;
      text-anchor: middle;
    }}
    .ring-bg {{
      fill: none;
      stroke: {BORDER_DARK};
      stroke-width: 5;
    }}
    .ring-prog {{
      fill: none;
      stroke: {PINK};
      stroke-width: 5;
      stroke-linecap: round;
      stroke-dasharray: 220;
      stroke-dashoffset: 45;
      transform: rotate(-90deg);
      transform-origin: 0px 0px;
    }}
  </style>

  <rect width="100%" height="100%" rx="12" fill="{BG_DARK}" stroke="{BORDER_DARK}" stroke-width="1"/>

  <g transform="translate(85, 80)">
    <text x="0" y="0" class="num">6</text>
    <text x="0" y="24" class="sub">Total Contributions</text>
    <text x="0" y="44" class="date">Nov 2025 - Present</text>
  </g>

  <line x1="168" y1="45" x2="168" y2="150" stroke="{BORDER_DARK}" stroke-width="1"/>

  <g transform="translate(247, 98)">
    <circle class="ring-bg" cx="0" cy="0" r="35"/>
    <circle class="ring-prog" cx="0" cy="0" r="35"/>
    <path fill="{PINK}" transform="translate(-7, -26) scale(0.9)" d="M8 0c-.076 0-.15.005-.224.014a4.436 4.436 0 00-3.14 1.34A5.27 5.27 0 003.3 4.298c-.14.288-.24.59-.3.902-.128.66-.075 1.344.154 1.97.23.626.64 1.173 1.18 1.57.19-.38.45-.72.77-.99.32-.27.7-.46 1.11-.56.41-.1.84-.1 1.25 0 .41.1.79.29 1.11.56.32.27.58.61.77.99.54-.397.95-.944 1.18-1.57.23-.626.28-1.31.15-1.97a4.93 4.93 0 00-.3-.902 5.27 5.27 0 00-1.336-2.944 4.436 4.436 0 00-3.14-1.34A4.8 4.8 0 008 0z"/>
    <text x="0" y="6" class="num" font-size="24">1</text>
    <text x="0" y="52" class="sub" font-weight="700">Current Streak</text>
    <text x="0" y="69" class="date">2 Nov</text>
  </g>

  <line x1="326" y1="45" x2="326" y2="150" stroke="{BORDER_DARK}" stroke-width="1"/>

  <g transform="translate(410, 80)">
    <text x="0" y="0" class="num">2</text>
    <text x="0" y="24" class="sub">Longest Streak</text>
    <text x="0" y="44" class="date">1 Nov - 2 Nov</text>
  </g>
</svg>"""
    (ASSETS / "streak.svg").write_text(svg + "\n", encoding="utf-8")


def make_activity_graph():
    w, h = 900, 300
    left, right, top, bottom = 55, 25, 55, 45
    gw = w - left - right
    gh = h - top - bottom

    today = date.today()
    days = [today - timedelta(days=i) for i in range(30, -1, -1)]
    values = [0] * 29 + [2, 4]
    max_val = max(values) if max(values) > 0 else 1

    points = []
    for i, val in enumerate(values):
        x = left + (i / (len(values) - 1)) * gw
        y = top + gh - (val / max_val) * gh
        points.append((x, y))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    circles = ""
    for (x, y), val in zip(points, values):
        if val > 0:
            circles += f"""
            <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{PINK}" stroke="{TEXT_PRIMARY}" stroke-width="1.5">
              <title>{val} contributions</title>
            </circle>
            """
        else:
            circles += f"""
            <circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{BORDER_DARK}">
              <title>0 contributions</title>
            </circle>
            """

    grid = ""
    for i in range(5):
        y = top + (gh / 4) * i
        grid += f'<line x1="{left}" y1="{y:.1f}" x2="{w-right}" y2="{y:.1f}" stroke="#21262d" stroke-width="1"/>'

    start_lbl = days[0].strftime("%d %b")
    end_lbl = days[-1].strftime("%d %b")
    total_act = sum(values)

    svg = f"""<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{w}"
  height="{h}"
  viewBox="0 0 {w} {h}"
  role="img"
  aria-label="GitHub contribution activity graph"
>
  <rect width="100%" height="100%" rx="14" fill="{BG_DARK}" stroke="{BORDER_DARK}" stroke-width="1"/>

  <text x="{left}" y="32" fill="{TEXT_PRIMARY}" font-size="16" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif" font-weight="700">
    Contribution Activity — Last 31 Days
  </text>
  <text x="{w-right}" y="32" text-anchor="end" fill="{PINK}" font-size="13" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif" font-weight="700">
    {total_act} contributions
  </text>

  {grid}

  <polyline
    points="{polyline}"
    fill="none"
    stroke="{PINK}"
    stroke-width="3"
    stroke-linejoin="round"
    stroke-linecap="round"
  />

  {circles}

  <text x="{left}" y="{h-15}" fill="{TEXT_MUTED}" font-size="11" font-family="Arial, sans-serif">{start_lbl}</text>
  <text x="{w-right}" y="{h-15}" text-anchor="end" fill="{TEXT_MUTED}" font-size="11" font-family="Arial, sans-serif">{end_lbl}</text>
</svg>"""
    (ASSETS / "activity-graph.svg").write_text(svg + "\n", encoding="utf-8")


def main():
    print(f"Updating GitHub Analytics for {USERNAME} with Pink Mix Theme...")
    user = get_user_data()
    repos = get_repositories()
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos if not repo.get("fork"))
    forks = sum(int(repo.get("forks_count", 0)) for repo in repos if not repo.get("fork"))
    followers = int(user.get("followers", 0))
    public_repos = int(user.get("public_repos", len(repos)))

    make_github_stats(stars)
    make_top_langs()
    make_profile_metrics(public_repos, stars, followers, forks)
    make_streak_card()
    make_activity_graph()
    print("All analytics SVGs updated successfully in pink mix theme!")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Stats updater failed: {exc}", file=sys.stderr)
        sys.exit(1)
