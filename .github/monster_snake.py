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

# ============================================================
# SNAKE SPEED
# ============================================================

# Bigger = slower
SNAKE_DURATION = 40


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
# GITHUB API
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
    data = json.loads(
        response.read().decode("utf-8")
    )


if "errors" in data:
    raise RuntimeError(data["errors"])


calendar = (
    data["data"]
    ["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
)

weeks = calendar["weeks"]


print("========================================")
print("       MONSTER CONTRIBUTION SNAKE")
print("========================================")
print("Username:", USERNAME)
print(
    "Total Contributions:",
    calendar["totalContributions"]
)
print("Snake Duration:", SNAKE_DURATION)
print("========================================")


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
        return BLUE

    if count <= 5:
        return PURPLE

    if count <= 9:
        return PINK

    return RED


# ============================================================
# SNAKE PATH
# ============================================================

def create_path():

    points = []


    for y in range(ROWS):

        py = (
            y * STEP
            + CELL / 2
            + 8
        )


        # Zig-zag path
        if y % 2 == 0:

            xs = range(COLUMNS)

        else:

            xs = range(
                COLUMNS - 1,
                -1,
                -1
            )


        for x in xs:

            px = (
                x * STEP
                + CELL / 2
            )

            points.append(
                (px, py)
            )


    path = (
        f"M {points[0][0]} "
        f"{points[0][1]}"
    )


    for px, py in points[1:]:

        path += (
            f" L {px} {py}"
        )


    return path, points


PATH, POINTS = create_path()


# ============================================================
# CONTRIBUTION GRID
#
# IMPORTANT:
# The actual contribution rectangle is animated.
# We do NOT place another rectangle over it.
# ============================================================

def create_grid():

    output = []


    total_points = len(POINTS)

    time_per_point = (
        SNAKE_DURATION /
        total_points
    )


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


            # ------------------------------------------------
            # EMPTY CELL
            # ------------------------------------------------

            if item["count"] == 0:

                output.append(
                    f'''
                    <rect
                        x="{px}"
                        y="{py}"
                        width="{CELL}"
                        height="{CELL}"
                        rx="3"
                        fill="{EMPTY}"
                    />
                    '''
                )

                continue


            # ------------------------------------------------
            # FIND WHERE SNAKE REACHES THIS CELL
            # ------------------------------------------------

            point_index = (
                y * COLUMNS + x
            )


            if y % 2 == 1:

                point_index = (
                    y * COLUMNS
                    + (COLUMNS - 1 - x)
                )


            eat_time = (
                point_index *
                time_per_point
            )


            # ------------------------------------------------
            # CONTRIBUTION CELL
            #
            # Visible at beginning.
            #
            # Disappears when snake reaches it.
            #
            # Then comes back at next cycle.
            # ------------------------------------------------

            output.append(
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

                    <animate
                        attributeName="opacity"
                        values="1;1;0;0;1"
                        keyTimes="
                            0;
                            {eat_time / SNAKE_DURATION:.5f};
                            {(eat_time + 0.25) / SNAKE_DURATION:.5f};
                            0.9999;
                            1
                        "
                        dur="{SNAKE_DURATION}s"
                        repeatCount="indefinite"
                    />

                </rect>
                '''
            )


    return "\n".join(output)


# ============================================================
# BODY
# ============================================================

def create_body():

    output = []

    segments = 18


    for i in range(segments):

        # Body follows behind head
        delay = i * 0.35


        radius = 7.2 - (
            i * 0.09
        )


        if radius < 5.5:
            radius = 5.5


        if i < 6:

            color = BLUE

        elif i < 12:

            color = PURPLE

        else:

            color = PINK


        output.append(
            f'''
            <circle
                cx="0"
                cy="0"
                r="{radius:.2f}"
                fill="{color}"
                opacity="0.95">

                <animateMotion
                    dur="{SNAKE_DURATION}s"
                    begin="{delay:.2f}s"
                    repeatCount="indefinite"
                    calcMode="linear"
                    rotate="auto"
                    path="{PATH}"
                />

            </circle>
            '''
        )


    return "\n".join(output)


# ============================================================
# EATING BURSTS
#
# QUICK ONLY
#
# These are independent visual effects.
# They repeat with the snake cycle.
# ============================================================

def create_bursts():

    output = []


    total_points = len(POINTS)

    time_per_point = (
        SNAKE_DURATION /
        total_points
    )


    for index, (cx, cy) in enumerate(POINTS):

        x = int(
            (cx - CELL / 2) /
            STEP
        )

        y = int(
            (cy - 8 - CELL / 2) /
            STEP
        )


        if x < 0 or x >= COLUMNS:
            continue

        if y < 0 or y >= ROWS:
            continue


        if grid[x][y]["count"] <= 0:
            continue


        eat_time = (
            index *
            time_per_point
        )


        # ====================================================
        # QUICK FLASH
        # ====================================================

        output.append(
            f'''
            <circle
                cx="{cx}"
                cy="{cy}"
                r="1"
                fill="{WHITE}"
                opacity="0">

                <animate
                    attributeName="r"
                    values="1;9;1"
                    dur="0.22s"
                    begin="{eat_time:.3f}s"
                    repeatCount="indefinite"
                />

                <animate
                    attributeName="opacity"
                    values="0;1;0"
                    dur="0.22s"
                    begin="{eat_time:.3f}s"
                    repeatCount="indefinite"
                />

            </circle>
            '''


        )


        # ====================================================
        # PINK BURST
        # ====================================================

        output.append(
            f'''
            <circle
                cx="{cx}"
                cy="{cy}"
                r="1"
                fill="{PINK}"
                opacity="0">

                <animate
                    attributeName="r"
                    values="1;7;1"
                    dur="0.30s"
                    begin="{eat_time + 0.03:.3f}s"
                    repeatCount="indefinite"
                />

                <animate
                    attributeName="opacity"
                    values="0;0.9;0"
                    dur="0.30s"
                    begin="{eat_time + 0.03:.3f}s"
                    repeatCount="indefinite"
                />

            </circle>
            '''
        )


    return "\n".join(output)


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
                calcMode="linear"
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
            fill="#150006"
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
            calcMode="linear"
            rotate="auto"
            path="{PATH}"
        />

    </g>
    '''


# ============================================================
# COMPLETE SVG
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
        x="0"
        y="0"
        width="100%"
        height="100%"
        rx="12"
        fill="{BACKGROUND}"
    />


    <!-- CONTRIBUTION GRID -->

    <g id="contributions">

        {create_grid()}

    </g>


    <!-- BURST EFFECT -->

    <g
        id="eating-bursts"
        filter="url(#glow)"
    >

        {create_bursts()}

    </g>


    <!-- MONSTER -->

    <g
        id="monster"
        filter="url(#glow)"
    >

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
print("========================================")
print(" MONSTER SNAKE GENERATED")
print("========================================")
print("Speed       :", SNAKE_DURATION, "seconds")
print("Loop        : YES")
print("Contribute  : VISIBLE BEFORE EATING")
print("Burst       : 0.22 - 0.30 sec")
print("Reset       : EVERY NEW CYCLE")
print("========================================")
