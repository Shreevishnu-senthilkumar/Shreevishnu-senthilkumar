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

# Animation speed
DURATION = 12


# ============================================================
# COLORS
# ============================================================

BACKGROUND = "#070b14"

EMPTY = "#111827"

BLUE = "#3949ff"
PURPLE = "#7c3aed"
PINK = "#ec168c"
MAGENTA = "#ff1493"
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
    print(data["errors"])
    raise RuntimeError("GitHub API request failed")


calendar = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]

weeks = calendar["weeks"]

print("==========================================")
print("       MONSTER CONTRIBUTION SNAKE")
print("==========================================")
print("Username:", USERNAME)
print("Contributions:", calendar["totalContributions"])


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
# CONTRIBUTION COLORS
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
# CREATE FORWARD SNAKE PATH
#
# Row 1: LEFT  -> RIGHT
# Row 2: RIGHT -> LEFT
# Row 3: LEFT  -> RIGHT
# ...
#
# This is important:
# The head and body use this SAME path.
# ============================================================

def create_path():

    points = []

    for y in range(ROWS):

        py = y * STEP + CELL / 2 + 8

        if y % 2 == 0:

            x_values = range(COLUMNS)

        else:

            x_values = range(
                COLUMNS - 1,
                -1,
                -1
            )

        for x in x_values:

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
# BODY
#
# Positive begin values make the body FOLLOW the head.
# ============================================================

def create_body():

    result = []

    segments = 16

    for i in range(segments):

        delay = i * 0.055

        radius = 7.5 - (
            i * 0.12
        )

        if radius < 5.5:
            radius = 5.5

        # Purple -> pink -> red
        if i < 6:
            color = BLUE
        elif i < 11:
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
                    dur="{DURATION}s"
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
# Contribution cells disappear shortly AFTER the monster
# reaches them.
# ============================================================

def create_eating_effect():

    result = []

    total_points = len(POINTS)

    cell_duration = (
        DURATION / total_points
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

        if item["count"] <= 0:
            continue

        start = (
            index * cell_duration
        )

        # ----------------------------------------------------
        # EXPLOSION PARTICLES
        # ----------------------------------------------------

        result.append(
            f'''
            <g>

                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="2"
                    fill="{WHITE}"
                    opacity="0">

                    <animate
                        attributeName="r"
                        values="1;9;1"
                        dur="0.28s"
                        begin="{start:.3f}s"
                        repeatCount="indefinite"
                    />

                    <animate
                        attributeName="opacity"
                        values="0;1;0"
                        dur="0.28s"
                        begin="{start:.3f}s"
                        repeatCount="indefinite"
                    />

                </circle>


                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="1"
                    fill="{RED}"
                    opacity="0">

                    <animate
                        attributeName="r"
                        values="1;7;1"
                        dur="0.35s"
                        begin="{start + 0.03:.3f}s"
                        repeatCount="indefinite"
                    />

                    <animate
                        attributeName="opacity"
                        values="0;0.9;0"
                        dur="0.35s"
                        begin="{start + 0.03:.3f}s"
                        repeatCount="indefinite"
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
                        values="0;0;1;1;0"
                        keyTimes="0;0.45;0.55;0.85;1"
                        dur="{DURATION}s"
                        begin="{start:.3f}s"
                        repeatCount="indefinite"
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

        <!-- BIG RED GLOW -->

        <circle
            cx="0"
            cy="0"
            r="20"
            fill="{RED}"
            opacity="0.10">

            <animateMotion
                dur="{DURATION}s"
                repeatCount="indefinite"
                rotate="auto"
                path="{PATH}"
            />

        </circle>


        <circle
            cx="0"
            cy="0"
            r="15"
            fill="{PINK}"
            opacity="0.16">

            <animateMotion
                dur="{DURATION}s"
                repeatCount="indefinite"
                rotate="auto"
                path="{PATH}"
            />

        </circle>


        <!-- HEAD -->

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


        <!-- EYEBROWS -->

        <path
            d="M -7 -6 L -2 -5"
            stroke="{BLACK}"
            stroke-width="2"
            stroke-linecap="round"
        />

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
            fill="#130006"
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


        <!-- HEAD MOVES FORWARD -->

        <animateMotion
            dur="{DURATION}s"
            repeatCount="indefinite"
            rotate="auto"
            path="{PATH}"
        />

    </g>
    '''


# ============================================================
# SPEED LINES
# ============================================================

def create_speed_lines():

    return f'''
    <g
        opacity="0.55"
        stroke="{PINK}"
        stroke-linecap="round"
    >

        <line
            x1="0"
            y1="-4"
            x2="-15"
            y2="-4"
            stroke-width="2"
        >

            <animateMotion
                dur="{DURATION}s"
                repeatCount="indefinite"
                path="{PATH}"
            />

        </line>


        <line
            x1="0"
            y1="5"
            x2="-11"
            y2="5"
            stroke-width="1.5"
        >

            <animateMotion
                dur="{DURATION}s"
                repeatCount="indefinite"
                path="{PATH}"
            />

        </line>

    </g>
    '''


# ============================================================
# COMPLETE SVG
# ============================================================

def create_svg():

    grid_svg = create_grid()

    eating_svg = create_eating_effect()

    body_svg = create_body()

    head_svg = create_head()

    speed_svg = create_speed_lines()


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
        x="0"
        y="0"
        width="100%"
        height="100%"
        rx="12"
        fill="{BACKGROUND}"
    />


    <!-- CONTRIBUTION GRID -->

    <g>
        {grid_svg}
    </g>


    <!-- EATING EFFECT -->

    <g>
        {eating_svg}
    </g>


    <!-- MONSTER -->

    <g filter="url(#glow)">

        {body_svg}

        {speed_svg}

        {head_svg}

    </g>


    <!-- LABEL -->

    <text
        x="10"
        y="{HEIGHT - 8}"
        font-family="Arial, sans-serif"
        font-size="8"
        fill="#64748b"
    >
        🐍 MONSTER MODE • {USERNAME} • DEVOURING CONTRIBUTIONS
    </text>

</svg>
'''


# ============================================================
# WRITE FILES
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
print("==========================================")
print(" MONSTER SNAKE GENERATED")
print("==========================================")
print("Animation:", DURATION, "seconds")
print("Output:", light_file)
print("Output:", dark_file)
print("==========================================")
