import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]

OUTPUT_DIR = Path("dist")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CELL = 12
GAP = 3
STEP = CELL + GAP

COLUMNS = 53
ROWS = 7

WIDTH = COLUMNS * STEP
HEIGHT = ROWS * STEP + 25

GREEN = "#00ff66"
DARK_GREEN = "#00b84a"
VERY_DARK = "#07140d"
RED = "#ff1744"
WHITE = "#ffffff"
BLACK = "#020604"


# ============================================================
# GET GITHUB CONTRIBUTIONS
# ============================================================

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {
        "login": USERNAME
    }
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "monster-contribution-snake"
    }
)

try:
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))
except Exception as e:
    print("Could not retrieve GitHub contributions:")
    print(e)
    raise


if "errors" in data:
    print(data["errors"])
    raise RuntimeError("GitHub GraphQL request failed")


calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

weeks = calendar["weeks"]

print(f"User: {USERNAME}")
print(f"Total contributions: {calendar['totalContributions']}")


# ============================================================
# CONTRIBUTION LEVEL
# ============================================================

def contribution_level(count):
    if count == 0:
        return 0

    if count <= 2:
        return 1

    if count <= 5:
        return 2

    if count <= 9:
        return 3

    return 4


# ============================================================
# BUILD CONTRIBUTION GRID
# ============================================================

grid = []

for x, week in enumerate(weeks):

    days = week["contributionDays"]

    column = []

    for y in range(ROWS):

        if y < len(days):
            day = days[y]

            column.append({
                "count": day["contributionCount"],
                "date": day["date"],
                "level": contribution_level(
                    day["contributionCount"]
                )
            })
        else:
            column.append({
                "count": 0,
                "date": "",
                "level": 0
            })

    grid.append(column)


# ============================================================
# SVG HELPERS
# ============================================================

def rect_color(level, dark=False):

    if level == 0:
        return "#111820"

    if level == 1:
        return "#064d2b"

    if level == 2:
        return "#08783c"

    if level == 3:
        return "#00b84a"

    return "#00ff66"


def escape(text):
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# ============================================================
# CREATE CONTRIBUTION GRID
# ============================================================

def create_grid():

    result = []

    for x, column in enumerate(grid):

        for y, day in enumerate(column):

            px = x * STEP
            py = y * STEP + 10

            color = rect_color(day["level"])

            title = ""

            if day["date"]:
                title = (
                    f'<title>{escape(day["date"])}: '
                    f'{day["count"]} contributions</title>'
                )

            result.append(
                f'''
                <rect
                    x="{px}"
                    y="{py}"
                    width="{CELL}"
                    height="{CELL}"
                    rx="3"
                    fill="{color}"
                >
                    {title}
                </rect>
                '''
            )

    return "\n".join(result)


# ============================================================
# CREATE SERPENT PATH
# ============================================================

def create_path():

    points = []

    # Make a serpentine path through the grid.
    #
    # The snake moves:
    #
    # → → → →
    # ← ← ← ←
    # → → → →
    # ← ← ← ←
    #
    # This creates a continuous monster path.

    for y in range(ROWS):

        py = y * STEP + STEP / 2 + 10

        if y % 2 == 0:

            for x in range(COLUMNS):
                px = x * STEP + STEP / 2
                points.append((px, py))

        else:

            for x in range(COLUMNS - 1, -1, -1):
                px = x * STEP + STEP / 2
                points.append((px, py))

    path = f"M {points[0][0]} {points[0][1]} "

    for px, py in points[1:]:
        path += f"L {px} {py} "

    return path


PATH = create_path()


# ============================================================
# MONSTER BODY
# ============================================================

def create_body_segments():

    result = []

    segments = 11

    for i in range(segments):

        radius = 6.5 - (i * 0.25)

        opacity = 1.0 - (i * 0.045)

        delay = -(i * 0.11)

        result.append(
            f'''
            <circle
                cx="0"
                cy="0"
                r="{radius}"
                fill="{GREEN}"
                opacity="{opacity}"
            >
                <animateMotion
                    dur="22s"
                    repeatCount="indefinite"
                    begin="{delay}s"
                    path="{PATH}"
                />
            </circle>
            '''
        )

    return "\n".join(result)


# ============================================================
# MONSTER HEAD
# ============================================================

def create_monster_head():

    return f'''
    <g>

        <!-- Glow -->
        <circle
            cx="0"
            cy="0"
            r="16"
            fill="{GREEN}"
            opacity="0.12"
        >
            <animateMotion
                dur="22s"
                repeatCount="indefinite"
                path="{PATH}"
            />
        </circle>


        <!-- Monster Head -->
        <g>

            <circle
                cx="0"
                cy="0"
                r="10"
                fill="{GREEN}"
                stroke="{BLACK}"
                stroke-width="2"
            />

            <!-- Face -->
            <ellipse
                cx="0"
                cy="1"
                rx="8"
                ry="7"
                fill="{VERY_DARK}"
            />


            <!-- Left Eye -->

            <ellipse
                cx="-3.5"
                cy="-2.5"
                rx="2"
                ry="2.5"
                fill="{WHITE}"
            />

            <circle
                cx="-3.5"
                cy="-2.2"
                r="1"
                fill="{RED}"
            />


            <!-- Right Eye -->

            <ellipse
                cx="3.5"
                cy="-2.5"
                rx="2"
                ry="2.5"
                fill="{WHITE}"
            />

            <circle
                cx="3.5"
                cy="-2.2"
                r="1"
                fill="{RED}"
            />


            <!-- Mouth -->

            <path
                d="M -6 2 Q 0 9 6 2 Q 0 5 -6 2"
                fill="#170008"
                stroke="{BLACK}"
                stroke-width="1"
            />


            <!-- Teeth -->

            <path
                d="
                    M -4 3
                    L -2.5 6
                    L -1 3

                    M 1 3
                    L 2.5 6
                    L 4 3
                "
                fill="{WHITE}"
                stroke="{WHITE}"
                stroke-width="1.4"
                stroke-linejoin="round"
            />


            <!-- Tongue -->

            <path
                d="
                    M 0 5
                    Q -1 9 -3 9

                    M 0 5
                    Q 1 9 3 9
                "
                fill="none"
                stroke="{RED}"
                stroke-width="1.3"
                stroke-linecap="round"
            />


            <!-- Horns -->

            <path
                d="
                    M -6 -7 L -9 -12 L -3 -9
                    M 6 -7 L 9 -12 L 3 -9
                "
                fill="{GREEN}"
                stroke="{BLACK}"
                stroke-width="1"
            />

            <animateMotion
                dur="22s"
                repeatCount="indefinite"
                path="{PATH}"
            />

        </g>

    </g>
    '''


# ============================================================
# CREATE SVG
# ============================================================

def create_svg(dark=True):

    background = "#0b0f14"

    grid_svg = create_grid()

    body_svg = create_body_segments()

    head_svg = create_monster_head()

    return f'''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="100%"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="Monster GitHub contribution snake"
>

    <defs>

        <filter
            id="glow"
            x="-100%"
            y="-100%"
            width="300%"
            height="300%"
        >

            <feGaussianBlur
                stdDeviation="3"
                result="blur"
            />

            <feMerge>

                <feMergeNode in="blur"/>

                <feMergeNode in="SourceGraphic"/>

            </feMerge>

        </filter>

    </defs>


    <!-- Background -->

    <rect
        width="100%"
        height="100%"
        rx="12"
        fill="{background}"
    />


    <!-- Contribution Grid -->

    <g>
        {grid_svg}
    </g>


    <!-- Animated Monster -->

    <g filter="url(#glow)">

        {body_svg}

        {head_svg}

    </g>


    <!-- Title -->

    <text
        x="10"
        y="{HEIGHT - 5}"
        font-family="Arial, sans-serif"
        font-size="8"
        fill="#6b7280"
    >
        MONSTER CONTRIBUTION SNAKE • {escape(USERNAME)}
    </text>

</svg>
'''


# ============================================================
# WRITE FILES
# ============================================================

light_file = OUTPUT_DIR / "github-contribution-monster.svg"
dark_file = OUTPUT_DIR / "github-contribution-monster-dark.svg"

light_file.write_text(
    create_svg(False),
    encoding="utf-8"
)

dark_file.write_text(
    create_svg(True),
    encoding="utf-8"
)

print("Monster snake generated successfully.")

print(light_file)
print(dark_file)
