import os
import json
import urllib.request
from pathlib import Path


# ============================================================
# MONSTER CONTRIBUTION SNAKE
# ============================================================

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]

OUTPUT_DIR = Path("dist")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# GRID
# ============================================================

ROWS = 7
COLUMNS = 53

CELL = 12
GAP = 3
STEP = CELL + GAP

WIDTH = COLUMNS * STEP
HEIGHT = ROWS * STEP + 32


# ============================================================
# ANIMATION SETTINGS
# ============================================================

# Full snake journey across the contribution grid
# 32 seconds = smooth / normal speed
SNAKE_DURATION = 32

# Very quick eating burst
BURST_DURATION = 0.18

# Number of monster body segments
BODY_SEGMENTS = 22

# Time gap between body segments
# Positive value makes every segment FOLLOW the head.
#
# 0.06 seconds = tight body
# 0.08 seconds = normal body
#
# We use 0.06 for a compact snake.
BODY_SEGMENT_DELAY = 0.06


# ============================================================
# COLORS
# ============================================================

BACKGROUND = "#070b14"
EMPTY = "#111827"

BLUE = "#3155ff"
PURPLE = "#743cff"
PINK = "#ff168c"
RED = "#ff1744"

WHITE = "#ffffff"
BLACK = "#030006"


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


print("==========================================")
print("       MONSTER CONTRIBUTION SNAKE")
print("==========================================")
print("Username       :", USERNAME)
print("Contributions  :", calendar["totalContributions"])
print("Snake duration :", SNAKE_DURATION, "seconds")
print("Body segments  :", BODY_SEGMENTS)
print("Segment delay  :", BODY_SEGMENT_DELAY)
print("Burst duration :", BURST_DURATION)
print("==========================================")


# ============================================================
# BUILD CONTRIBUTION GRID
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
# CREATE SNAKE PATH
# ============================================================

def create_path():

    points = []

    for y in range(ROWS):

        py = (
            y * STEP
            + CELL / 2
            + 8
        )

        # Even rows:
        # LEFT → RIGHT
        #
        # Odd rows:
        # RIGHT → LEFT
        #
        # This creates the serpentine path.

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
# ============================================================

def create_grid():

    output = []

    total_cells = len(POINTS)

    time_per_cell = (
        SNAKE_DURATION /
        total_cells
    )

    for x in range(COLUMNS):

        for y in range(ROWS):

            item = grid[x][y]

            px = x * STEP
            py = y * STEP + 8


            # =================================================
            # EMPTY CELL
            # =================================================

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


            # =================================================
            # FIND POSITION ON SNAKE PATH
            # =================================================

            if y % 2 == 0:

                path_index = (
                    y * COLUMNS
                    + x
                )

            else:

                path_index = (
                    y * COLUMNS
                    + (
                        COLUMNS
                        - 1
                        - x
                    )
                )


            # Time when snake reaches cell
            eat_time = (
                path_index *
                time_per_cell
            )


            # End of quick burst
            burst_end = (
                eat_time
                + BURST_DURATION
            )


            # =================================================
            # SAFE SVG TIMELINE VALUES
            # =================================================

            eat_key = min(
                eat_time /
                SNAKE_DURATION,
                0.998
            )

            burst_key = min(
                burst_end /
                SNAKE_DURATION,
                0.999
            )


            color = contribution_color(
                item["count"]
            )


            # =================================================
            # TOOLTIP
            # =================================================

            title = ""

            if item["date"]:

                title = (
                    f'''
                    <title>
                        {item["date"]}:
                        {item["count"]}
                        contributions
                    </title>
                    '''
                )


            # =================================================
            # CONTRIBUTION CELL
            #
            # START:
            #   visible
            #
            # SNAKE ARRIVES:
            #   flash
            #
            # AFTER EATING:
            #   disappear
            #
            # NEXT CYCLE:
            #   appear again
            # =================================================

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

                        values="
                            1;
                            1;
                            0.35;
                            0;
                            0;
                            1
                        "

                        keyTimes="
                            0;
                            {eat_key:.6f};
                            {eat_key + 0.002:.6f};
                            {burst_key:.6f};
                            0.999;
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
# QUICK EATING BURSTS
# ============================================================

def create_bursts():

    output = []

    total_cells = len(POINTS)

    time_per_cell = (
        SNAKE_DURATION /
        total_cells
    )


    for index, (cx, cy) in enumerate(POINTS):

        # Convert path index back to grid coordinates

        x = index % COLUMNS
        y = index // COLUMNS


        if y % 2 == 1:

            x = (
                COLUMNS
                - 1
                - x
            )


        if x < 0 or x >= COLUMNS:
            continue

        if y < 0 or y >= ROWS:
            continue


        # Only contribution cells burst

        if grid[x][y]["count"] <= 0:
            continue


        eat_time = (
            index *
            time_per_cell
        )


        # ====================================================
        # WHITE FLASH
        # ====================================================

        output.append(
            f'''
            <circle
                cx="{cx}"
                cy="{cy}"
                r="1"
                fill="{WHITE}"
                opacity="0"
            >

                <animate
                    attributeName="r"
                    values="1;5;1"
                    dur="{BURST_DURATION}s"
                    begin="{eat_time:.5f}s"
                    repeatCount="indefinite"
                />

                <animate
                    attributeName="opacity"
                    values="0;1;0"
                    dur="{BURST_DURATION}s"
                    begin="{eat_time:.5f}s"
                    repeatCount="indefinite"
                />

            </circle>
            '''
        )


        # ====================================================
        # PINK EXPLOSION RING
        # ====================================================

        output.append(
            f'''
            <circle
                cx="{cx}"
                cy="{cy}"
                r="1"
                fill="none"
                stroke="{PINK}"
                stroke-width="1.5"
                opacity="0"
            >

                <animate
                    attributeName="r"
                    values="1;8"
                    dur="{BURST_DURATION}s"
                    begin="{eat_time:.5f}s"
                    repeatCount="indefinite"
                />

                <animate
                    attributeName="opacity"
                    values="0;0.9;0"
                    dur="{BURST_DURATION}s"
                    begin="{eat_time:.5f}s"
                    repeatCount="indefinite"
                />

            </circle>
            '''
        )


    return "\n".join(output)


# ============================================================
# MONSTER BODY
# ============================================================

def create_body():

    output = []


    for i in range(BODY_SEGMENTS):

        # ====================================================
        # IMPORTANT:
        #
        # POSITIVE BEGIN
        #
        # Each segment starts AFTER the previous segment.
        #
        # This makes the body follow the head instead of
        # appearing to move backward.
        # ====================================================

        delay = (
            i *
            BODY_SEGMENT_DELAY
        )


        # ====================================================
        # BODY SIZE
        # ====================================================

        radius = (
            7.4 -
            i * 0.08
        )


        if radius < 5.7:
            radius = 5.7


        # ====================================================
        # BODY COLOR
        # ====================================================

        if i < 7:

            color = BLUE

        elif i < 14:

            color = PURPLE

        else:

            color = PINK


        # ====================================================
        # BODY SEGMENT
        # ====================================================

        output.append(
            f'''
            <circle
                cx="0"
                cy="0"
                r="{radius:.2f}"
                fill="{color}"
                opacity="0.97"
            >

                <animateMotion
                    dur="{SNAKE_DURATION}s"
                    begin="{delay:.4f}s"
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
# MONSTER HEAD
# ============================================================

def create_head():

    return f'''
    <g>


        <!-- ================================================
             HEAD GLOW
             ================================================ -->

        <circle
            cx="0"
            cy="0"
            r="16"
            fill="{RED}"
            opacity="0.12"
        >

            <animateMotion
                dur="{SNAKE_DURATION}s"
                repeatCount="indefinite"
                calcMode="linear"
                rotate="auto"
                path="{PATH}"
            />

        </circle>


        <!-- ================================================
             HEAD
             ================================================ -->

        <circle
            cx="0"
            cy="0"
            r="10.5"
            fill="{RED}"
            stroke="{BLACK}"
            stroke-width="2"
        />


        <!-- ================================================
             FACE
             ================================================ -->

        <ellipse
            cx="0"
            cy="1"
            rx="8"
            ry="7.5"
            fill="{BLACK}"
        />


        <!-- ================================================
             LEFT EYE
             ================================================ -->

        <ellipse
            cx="-3.5"
            cy="-3"
            rx="2.3"
            ry="2.7"
            fill="{WHITE}"
        />

        <circle
            cx="-3.5"
            cy="-2.7"
            r="1.2"
            fill="{RED}"
        />


        <!-- ================================================
             RIGHT EYE
             ================================================ -->

        <ellipse
            cx="3.5"
            cy="-3"
            rx="2.3"
            ry="2.7"
            fill="{WHITE}"
        />

        <circle
            cx="3.5"
            cy="-2.7"
            r="1.2"
            fill="{RED}"
        />


        <!-- ================================================
             EYEBROWS
             ================================================ -->

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


        <!-- ================================================
             MOUTH
             ================================================ -->

        <path
            d="
                M -7 2
                Q 0 10 7 2
                Q 0 6 -7 2
            "
            fill="#120005"
        />


        <!-- ================================================
             TEETH
             ================================================ -->

        <path
            d="
                M -5 3
                L -3.2 7
                L -1.5 3

                M 1.5 3
                L 3.2 7
                L 5 3
            "
            fill="{WHITE}"
        />


        <!-- ================================================
             LEFT HORN
             ================================================ -->

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


        <!-- ================================================
             RIGHT HORN
             ================================================ -->

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


        <!-- ================================================
             HEAD MOVEMENT
             ================================================ -->

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

    aria-label="Monster GitHub contribution snake"
>


    <!-- ====================================================
         DEFINITIONS
         ==================================================== -->

    <defs>

        <filter
            id="glow"
            x="-100%"
            y="-100%"
            width="300%"
            height="300%"
        >

            <feGaussianBlur
                stdDeviation="2"
                result="blur"
            />

            <feMerge>

                <feMergeNode in="blur"/>

                <feMergeNode in="SourceGraphic"/>

            </feMerge>

        </filter>

    </defs>


    <!-- ====================================================
         BACKGROUND
         ==================================================== -->

    <rect
        x="0"
        y="0"
        width="100%"
        height="100%"
        rx="12"
        fill="{BACKGROUND}"
    />


    <!-- ====================================================
         CONTRIBUTION CELLS
         ==================================================== -->

    <g id="contributions">

        {create_grid()}

    </g>


    <!-- ====================================================
         EATING BURSTS
         ==================================================== -->

    <g
        id="bursts"
        filter="url(#glow)"
    >

        {create_bursts()}

    </g>


    <!-- ====================================================
         MONSTER
         ==================================================== -->

    <g
        id="monster"
        filter="url(#glow)"
    >

        {create_body()}

        {create_head()}

    </g>


    <!-- ====================================================
         LABEL
         ==================================================== -->

    <text
        x="10"
        y="{HEIGHT - 9}"
        font-family="Arial, sans-serif"
        font-size="8"
        fill="#64748b"
    >
        MONSTER MODE • {USERNAME} • DEVOURING CONTRIBUTIONS
    </text>


</svg>
'''


# ============================================================
# WRITE SVG FILES
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


# ============================================================
# FINAL LOG
# ============================================================

print()

print("==========================================")
print("       MONSTER SNAKE GENERATED")
print("==========================================")

print(
    "Cycle        :",
    SNAKE_DURATION,
    "seconds"
)

print(
    "Body         :",
    BODY_SEGMENTS,
    "segments"
)

print(
    "Segment gap  :",
    BODY_SEGMENT_DELAY,
    "seconds"
)

print(
    "Burst        :",
    BURST_DURATION,
    "seconds"
)

print(
    "Eating       : ENABLED"
)

print(
    "Reset        : ENABLED"
)

print(
    "Direction    : HEAD → TAIL"
)

print("==========================================")
