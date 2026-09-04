import os
import json
import urllib.request
from pathlib import Path


# ============================================================
# CONFIGURATION
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
HEIGHT = ROWS * STEP + 25

BG = "#0b0f14"

GREEN = "#00ff66"
GREEN2 = "#00cc55"

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
        "User-Agent": "monster-snake"
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
print(" MONSTER SNAKE")
print("========================================")
print("User:", USERNAME)
print("Contributions:", calendar["totalContributions"])


# ============================================================
# GRID
# ============================================================

grid = []

for x in range(COLUMNS):

    days = []

    if x < len(weeks):
        days = weeks[x]["contributionDays"]

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
        return "#111820"

    if count <= 2:
        return "#064d2b"

    if count <= 5:
        return "#08783c"

    if count <= 9:
        return "#00b84a"

    return "#00ff66"


# ============================================================
# GRID
# ============================================================

def create_grid():

    svg = []

    for x in range(COLUMNS):

        for y in range(ROWS):

            item = grid[x][y]

            px = x * STEP
            py = y * STEP + 8

            color = contribution_color(item["count"])

            title = ""

            if item["date"]:

                title = (
                    f"<title>{item['date']}: "
                    f"{item['count']} contributions</title>"
                )

            svg.append(
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

    return "\n".join(svg)


# ============================================================
# SNAKE PATH
# ============================================================

def create_path():

    points = []

    for y in range(ROWS):

        py = y * STEP + STEP / 2 + 8

        if y % 2 == 0:

            xs = range(COLUMNS)

        else:

            xs = range(COLUMNS - 1, -1, -1)

        for x in xs:

            px = x * STEP + STEP / 2

            points.append((px, py))


    path = f"M {points[0][0]} {points[0][1]}"

    for px, py in points[1:]:

        path += f" L {px} {py}"

    return path


PATH = create_path()


# ============================================================
# MONSTER BODY
#
# IMPORTANT:
# The body segments use the SAME animation path.
# Each segment starts slightly later so it follows the head.
# ============================================================

def create_body():

    svg = []

    segments = 14

    for i in range(segments):

        delay = i * 0.07

        radius = 6.8 - (i * 0.12)

        if radius < 4.8:
            radius = 4.8

        opacity = 1.0 - (i * 0.035)

        svg.append(
            f'''
            <circle
                cx="0"
                cy="0"
                r="{radius:.2f}"
                fill="{GREEN}"
                opacity="{opacity:.2f}">

                <animateMotion
                    dur="30s"
                    begin="-{delay:.2f}s"
                    repeatCount="indefinite"
                    rotate="auto"
                    path="{PATH}"
                />

            </circle>
            '''
        )

    return "\n".join(svg)


# ============================================================
# EATING SYSTEM
#
# Every contribution cell is hidden at the EXACT time
# the monster reaches that cell.
# ============================================================

def create_eating():

    svg = []

    total_points = ROWS * COLUMNS

    duration = 30.0

    cell_time = duration / total_points

    index = 0

    for y in range(ROWS):

        if y % 2 == 0:
            xs = range(COLUMNS)
        else:
            xs = range(COLUMNS - 1, -1, -1)

        for x in xs:

            item = grid[x][y]

            if item["count"] > 0:

                px = x * STEP
                py = y * STEP + 8

                cx = px + CELL / 2
                cy = py + CELL / 2

                start = index * cell_time

                # Contribution disappears
                svg.append(
                    f'''
                    <rect
                        x="{px - 1}"
                        y="{py - 1}"
                        width="{CELL + 2}"
                        height="{CELL + 2}"
                        rx="3"
                        fill="{BG}"
                        opacity="0">

                        <animate
                            attributeName="opacity"
                            values="0;0;1;1;0"
                            keyTimes="0;0.42;0.50;0.88;1"
                            dur="{duration}s"
                            begin="{start:.3f}s"
                            repeatCount="indefinite"
                        />

                    </rect>
                    '''
                )

                # Bite explosion
                svg.append(
                    f'''
                    <circle
                        cx="{cx}"
                        cy="{cy}"
                        r="1"
                        fill="{GREEN}"
                        opacity="0">

                        <animate
                            attributeName="r"
                            values="1;9;1"
                            dur="0.4s"
                            begin="{start:.3f}s"
                            repeatCount="indefinite"
                        />

                        <animate
                            attributeName="opacity"
                            values="0;1;0"
                            dur="0.4s"
                            begin="{start:.3f}s"
                            repeatCount="indefinite"
                        />

                    </circle>
                    '''
                )

            index += 1

    return "\n".join(svg)


# ============================================================
# MONSTER HEAD
# ============================================================

def create_head():

    return f'''
    <g>

        <!-- HEAD GLOW -->

        <circle
            cx="0"
            cy="0"
            r="18"
            fill="{GREEN}"
            opacity="0.14">

            <animateMotion
                dur="30s"
                repeatCount="indefinite"
                rotate="auto"
                path="{PATH}"
            />

        </circle>


        <!-- OUTER HEAD -->

        <circle
            cx="0"
            cy="0"
            r="11"
            fill="{GREEN}"
            stroke="{BLACK}"
            stroke-width="2"
        />


        <!-- FACE -->

        <ellipse
            cx="0"
            cy="1"
            rx="8.5"
            ry="8"
            fill="#06140d"
        />


        <!-- LEFT EYE -->

        <ellipse
            cx="-3.6"
            cy="-3"
            rx="2.2"
            ry="2.7"
            fill="{WHITE}"
        />

        <circle
            cx="-3.6"
            cy="-2.8"
            r="1.1"
            fill="{RED}"
        />


        <!-- RIGHT EYE -->

        <ellipse
            cx="3.6"
            cy="-3"
            rx="2.2"
            ry="2.7"
            fill="{WHITE}"
        />

        <circle
            cx="3.6"
            cy="-2.8"
            r="1.1"
            fill="{RED}"
        />


        <!-- MOUTH -->

        <path
            d="
                M -7 2
                Q 0 10 7 2
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
                L -3.2 7
                L -1.5 3

                M 1.5 3
                L 3.2 7
                L 5 3
            "
            fill="{WHITE}"
            stroke="{WHITE}"
            stroke-width="1.5"
        />


        <!-- TONGUE -->

        <path
            d="
                M 0 6
                Q -1.5 10 -3.5 10

                M 0 6
                Q 1.5 10 3.5 10
            "
            fill="none"
            stroke="{RED}"
            stroke-width="1.4"
            stroke-linecap="round"
        />


        <!-- LEFT HORN -->

        <path
            d="
                M -6 -8
                L -10 -14
                L -3 -10
            "
            fill="{GREEN2}"
            stroke="{BLACK}"
            stroke-width="1"
        />


        <!-- RIGHT HORN -->

        <path
            d="
                M 6 -8
                L 10 -14
                L 3 -10
            "
            fill="{GREEN2}"
            stroke="{BLACK}"
            stroke-width="1"
        />


        <!-- HEAD MOVEMENT -->

        <animateMotion
            dur="30s"
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

    grid_svg = create_grid()

    eating_svg = create_eating()

    body_svg = create_body()

    head_svg = create_head()


    return f'''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="100%"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="Venom style monster GitHub contribution snake"
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
                stdDeviation="2.8"
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
        rx="10"
        fill="{BG}"
    />


    <!-- CONTRIBUTIONS -->

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

        {head_svg}

    </g>


    <!-- LABEL -->

    <text
        x="8"
        y="{HEIGHT - 6}"
        font-family="Arial, sans-serif"
        font-size="7"
        fill="#64748b"
    >
        MONSTER MODE • {USERNAME} • DEVOURING CONTRIBUTIONS
    </text>

</svg>
'''


# ============================================================
# OUTPUT
# ============================================================

svg = create_svg()


light = OUTPUT_DIR / "github-contribution-monster.svg"

dark = OUTPUT_DIR / "github-contribution-monster-dark.svg"


light.write_text(svg, encoding="utf-8")

dark.write_text(svg, encoding="utf-8")


print()
print("========================================")
print(" MONSTER SNAKE GENERATED SUCCESSFULLY")
print("========================================")
print("Files:")
print(light)
print(dark)
