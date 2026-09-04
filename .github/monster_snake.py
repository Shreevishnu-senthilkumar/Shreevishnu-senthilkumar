import os
import json
import urllib.request
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]

OUTPUT_DIR = Path("dist")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROWS = 7
COLUMNS = 53

CELL = 12
GAP = 3
STEP = CELL + GAP

WIDTH = COLUMNS * STEP
HEIGHT = ROWS * STEP + 30

# 🐍 SLOW SNAKE
# Increase this number = slower
SNAKE_DURATION = 35


# ============================================================
# COLORS
# ============================================================

BACKGROUND = "#070b14"
EMPTY = "#111827"

BLUE = "#3949ff"
PURPLE = "#7c3aed"
PINK = "#ec168c"
RED = "#ff1744"

WHITE = "#ffffff"
BLACK = "#050008"


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


with urllib.request.urlopen(request) as response:
    data = json.loads(response.read().decode("utf-8"))


if "errors" in data:
    raise RuntimeError(data["errors"])


calendar = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]

weeks = calendar["weeks"]

print("========================================")
print(" MONSTER CONTRIBUTION SNAKE")
print("========================================")
print("Username:", USERNAME)
print("Contributions:", calendar["totalContributions"])
print("Snake duration:", SNAKE_DURATION, "seconds")


# ============================================================
# BUILD GRID
# ============================================================

grid = []

for x in range(COLUMNS):

    if x < len(weeks):
        days = weeks[x]["contributionDays"]
    else:
        days = []

    column = []

    for y in range(ROWS):

        if y < len(days):

            column.append({
                "count": days[y]["contributionCount"],
                "date": days[y]["date"]
            })

        else:

            column.append({
                "count": 0,
                "date": ""
            })

    grid.append(column)


# ============================================================
# CONTRIBUTION COLOR
# ============================================================

def contribution_color(count):

    if count == 0:
        return EMPTY

    if count <= 2:
        return "#25206b"

    if count <= 5:
        return BLUE

    if count <= 9:
        return PURPLE

    return PINK


# ============================================================
# CONTRIBUTION GRID
# ============================================================

def create_grid():

    result = []

    for x in range(COLUMNS):

        for y in range(ROWS):

            item = grid[x][y]

            px = x * STEP
            py = y * STEP + 8

            color = contribution_color(
                item["count"]
            )

            title = ""

            if item["date"]:

                title = (
                    f"<title>"
                    f"{item['date']}: "
                    f"{item['count']} contributions"
                    f"</title>"
                )

            result.append(
                f'''
                <rect
                    x="{px}"
                    y="{py}"
                    width="{CELL}"
                    height="{CELL}"
                    rx="3"
                    fill="{color}">
                    {title}
                </rect>
                '''
            )

    return "\n".join(result)


# ============================================================
# SNAKE PATH
# ============================================================

def create_path():

    points = []

    for y in range(ROWS):

        py = y * STEP + CELL / 2 + 8

        if y % 2 == 0:

            xs = range(COLUMNS)

        else:

            xs = range(
                COLUMNS - 1,
                -1,
                -1
            )

        for x in xs:

            px = x * STEP + CELL / 2

            points.append(
                (px, py)
            )


    path = (
        f"M {points[0][0]} {points[0][1]}"
    )

    for px, py in points[1:]:

        path += (
            f" L {px} {py}"
        )

    return path, points


PATH, POINTS = create_path()


# ============================================================
# SNAKE BODY
#
# Body follows behind the head.
# ============================================================

def create_body():

    result = []

    segments = 18

    for i in range(segments):

        # Small delay = body follows head
        delay = i * 0.07

        radius = 7.2 - (
            i * 0.09
        )

        if radius < 5.5:
            radius = 5.5


        # Blue -> Purple -> Pink
        if i < 6:

            color = BLUE

        elif i < 12:

            color = PURPLE

        else:

            color = PINK


        result.append(
            f'''
            <circle
                cx="0"
                cy="0"
                r="{radius:.2f}"
                fill="{color}"
                opacity="0.95">

                <animateMotion
                    dur="{SNAKE_DURATION}s"
                    begin="{delay:.3f}s"
                    repeatCount="indefinite"
                    rotate="auto"
                    path="{PATH}"
                />

            </circle>
            '''
        )

    return "\n".join(result)


# ============================================================
# EATING EFFECT
#
# IMPORTANT:
# NO repeatCount here.
#
# Therefore:
# 💥 burst happens once
# 🟪 cell disappears once
# ❌ cell does NOT come back
# ============================================================

def create_eating_effect():

    result = []

    total_points = len(POINTS)

    time_per_cell = (
        SNAKE_DURATION / total_points
    )


    for index, (cx, cy) in enumerate(POINTS):

        x = int(
            (cx - CELL / 2) / STEP
        )

        y = int(
            (cy - 8 - CELL / 2) / STEP
        )


        if x < 0 or x >= COLUMNS:
            continue

        if y < 0 or y >= ROWS:
            continue


        item = grid[x][y]


        # No contribution = nothing to eat
        if item["count"] <= 0:
            continue


        # When snake reaches this cell
        start = (
            index * time_per_cell
        )


        # ====================================================
        # QUICK BURST
        # ====================================================

        result.append(
            f'''
            <g>

                <!-- WHITE FLASH -->

                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="1"
                    fill="{WHITE}"
                    opacity="0">

                    <animate
                        attributeName="r"
                        values="1;8;1"
                        dur="0.22s"
                        begin="{start:.3f}s"
                        fill="freeze"
                    />

                    <animate
                        attributeName="opacity"
                        values="0;1;0"
                        dur="0.22s"
                        begin="{start:.3f}s"
                        fill="freeze"
                    />

                </circle>


                <!-- RED BURST -->

                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="1"
                    fill="{RED}"
                    opacity="0">

                    <animate
                        attributeName="r"
                        values="1;7;1"
                        dur="0.30s"
                        begin="{start + 0.03:.3f}s"
                        fill="freeze"
                    />

                    <animate
                        attributeName="opacity"
                        values="0;1;0"
                        dur="0.30s"
                        begin="{start + 0.03:.3f}s"
                        fill="freeze"
                    />

                </circle>


                <!-- PARTICLE 1 -->

                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="1.5"
                    fill="{PINK}"
                    opacity="0">

                    <animate
                        attributeName="cx"
                        values="{cx};{cx + 7}"
                        dur="0.25s"
                        begin="{start:.3f}s"
                        fill="freeze"
                    />

                    <animate
                        attributeName="cy"
                        values="{cy};{cy - 6}"
                        dur="0.25s"
                        begin="{start:.3f}s"
                        fill="freeze"
                    />

                    <animate
                        attributeName="opacity"
                        values="1;0"
                        dur="0.25s"
                        begin="{start:.3f}s"
                        fill="freeze"
                    />

                </circle>


                <!-- PARTICLE 2 -->

                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="1.5"
                    fill="{PURPLE}"
                    opacity="0">

                    <animate
                        attributeName="cx"
                        values="{cx};{cx - 7}"
                        dur="0.28s"
                        begin="{start:.03f}s"
                        fill="freeze"
                    />

                    <animate
                        attributeName="cy"
                        values="{cy};{cy + 6}"
                        dur="0.28s"
                        begin="{start:.03f}s"
                        fill="freeze"
                    />

                    <animate
                        attributeName="opacity"
                        values="1;0"
                        dur="0.28s"
                        begin="{start:.03f}s"
                        fill="freeze"
                    />

                </circle>


                <!-- EATEN CELL -->

                <rect
                    x="{cx - CELL / 2 - 2}"
                    y="{cy - CELL / 2 - 2}"
                    width="{CELL + 4}"
                    height="{CELL + 4}"
                    rx="4"
                    fill="{BACKGROUND}"
                    opacity="0">

                    <animate
                        attributeName="opacity"
                        values="0;1"
                        dur="0.18s"
                        begin="{start + 0.20:.3f}s"
                        fill="freeze"
                    />

                </rect>

            </g>
            '''
        )


    return "\n".join(result)


# ============================================================
# MONSTER HEAD
# ============================================================

def create_head():

    return f'''
    <g>


        <!-- OUTER GLOW -->

        <circle
            cx="0"
            cy="0"
            r="20"
            fill="{RED}"
            opacity="0.12">

            <animateMotion
                dur="{SNAKE_DURATION}s"
                repeatCount="indefinite"
                rotate="auto"
                path="{PATH}"
            />

        </circle>


        <!-- INNER GLOW -->

        <circle
            cx="0"
            cy="0"
            r="15"
            fill="{PINK}"
            opacity="0.18">

            <animateMotion
                dur="{SNAKE_DURATION}s"
                repeatCount="indefinite"
                rotate="auto"
                path="{PATH}"
            />

        </circle>


        <!-- MONSTER HEAD -->

        <circle
            cx="0"
            cy="0"
            r="11"
            fill="{RED}"
            stroke="{BLACK}"
            stroke-width="2"
        />


        <!-- FACE -->

        <ellipse
            cx="0"
            cy="1"
            rx="8.5"
            ry="8"
            fill="{BLACK}"
        />


        <!-- LEFT EYE -->

        <ellipse
            cx="-3.7"
            cy="-3"
            rx="2.4"
            ry="2.8"
            fill="{WHITE}"
        />

        <circle
            cx="-3.7"
            cy="-2.7"
            r="1.3"
            fill="{RED}"
        />


        <!-- RIGHT EYE -->

        <ellipse
            cx="3.7"
            cy="-3"
            rx="2.4"
            ry="2.8"
            fill="{WHITE}"
        />

        <circle
            cx="3.7"
            cy="-2.7"
            r="1.3"
            fill="{RED}"
        />


        <!-- LEFT EYEBROW -->

        <path
            d="M -7 -6 L -2 -5"
            stroke="{BLACK}"
            stroke-width="2"
            stroke-linecap="round"
        />


        <!-- RIGHT EYEBROW -->

        <path
            d="M 7 -6 L 2 -5"
            stroke="{BLACK}"
            stroke-width="2"
            stroke-linecap="round"
        />


        <!-- MOUTH -->

        <path
            d="
                M -7 2
                Q 0 11 7 2
                Q 0 6 -7 2
            "
            fill="#150006"
            stroke="{BLACK}"
            stroke-width="1"
        />


        <!-- TEETH -->

        <path
            d="
                M -5 3
                L -3.3 7
                L -1.6 3

                M 1.6 3
                L 3.3 7
                L 5 3
            "
            fill="{WHITE}"
        />


        <!-- TONGUE -->

        <path
            d="
                M 0 6
                Q -1.5 10 -3 10

                M 0 6
                Q 1.5 10 3 10
            "
            fill="none"
            stroke="{RED}"
            stroke-width="1.5"
            stroke-linecap="round"
        />


        <!-- HORNS -->

        <path
            d="
                M -6 -8
                L -10 -15
                L -3 -10
            "
            fill="{PINK}"
            stroke="{BLACK}"
            stroke-width="1"
        />

        <path
            d="
                M 6 -8
                L 10 -15
                L 3 -10
            "
            fill="{PINK}"
            stroke="{BLACK}"
            stroke-width="1"
        />


        <!-- HEAD MOVEMENT -->

        <animateMotion
            dur="{SNAKE_DURATION}s"
            repeatCount="indefinite"
            rotate="auto"
            path="{PATH}"
        />

    </g>
    '''


# ============================================================
# SVG
# ============================================================

def create_svg():

    return f'''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="100%"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="Monster contribution snake"
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


    <!-- BACKGROUND -->

    <rect
        width="100%"
        height="100%"
        rx="12"
        fill="{BACKGROUND}"
    />


    <!-- CONTRIBUTION GRID -->

    <g>
        {create_grid()}
    </g>


    <!-- EATING EFFECT -->

    <g>
        {create_eating_effect()}
    </g>


    <!-- MONSTER -->

    <g filter="url(#glow)">

        {create_body()}

        {create_head()}

    </g>


    <!-- LABEL -->

    <text
        x="10"
        y="{HEIGHT - 8}"
        font-family="Arial, sans-serif"
        font-size="8"
        fill="#64748b"
    >
        MONSTER MODE • {USERNAME} • DEVOURING CONTRIBUTIONS
    </text>

</svg>
'''


# ============================================================
# WRITE OUTPUT
# ============================================================

svg = create_svg()


light_file = (
    OUTPUT_DIR /
    "github-contribution-monster.svg"
)

dark_file = (
    OUTPUT_DIR /
    "github-contribution-monster-dark.svg"
)


light_file.write_text(
    svg,
    encoding="utf-8"
)

dark_file.write_text(
    svg,
    encoding="utf-8"
)


print()
print("========================================")
print(" MONSTER SNAKE GENERATED SUCCESSFULLY")
print("========================================")
print("Snake speed:", SNAKE_DURATION, "seconds")
print("Burst: QUICK")
print("Eating: ONE TIME ONLY")
print("Eaten cells: STAY GONE")
print("========================================")
