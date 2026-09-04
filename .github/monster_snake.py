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

COLUMNS = 53
ROWS = 7

CELL = 12
GAP = 3
STEP = CELL + GAP

WIDTH = COLUMNS * STEP
HEIGHT = ROWS * STEP + 30

BACKGROUND = "#0b0f14"

GREEN = "#00ff66"
GREEN_DARK = "#08783c"

RED = "#ff1744"
WHITE = "#ffffff"
BLACK = "#020604"


# ============================================================
# GITHUB GRAPHQL
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


with urllib.request.urlopen(request) as response:
    data = json.loads(response.read().decode("utf-8"))


if "errors" in data:
    print(data["errors"])
    raise RuntimeError("GitHub API request failed")


calendar = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]

weeks = calendar["weeks"]

print("Username:", USERNAME)
print("Total contributions:", calendar["totalContributions"])


# ============================================================
# CONTRIBUTION COLOR
# ============================================================

def get_color(count):

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
# GRID DATA
# ============================================================

grid = []

for x in range(COLUMNS):

    column = []

    if x < len(weeks):

        days = weeks[x]["contributionDays"]

    else:

        days = []

    for y in range(ROWS):

        if y < len(days):

            day = days[y]

            column.append({
                "count": day["contributionCount"],
                "date": day["date"]
            })

        else:

            column.append({
                "count": 0,
                "date": ""
            })

    grid.append(column)


# ============================================================
# GRID SVG
# ============================================================

def create_grid():

    output = []

    for x in range(COLUMNS):

        for y in range(ROWS):

            item = grid[x][y]

            px = x * STEP
            py = y * STEP + 10

            color = get_color(item["count"])

            title = ""

            if item["date"]:

                title = (
                    f"<title>"
                    f"{item['date']}: "
                    f"{item['count']} contributions"
                    f"</title>"
                )

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
                </rect>
                '''
            )

    return "\n".join(output)


# ============================================================
# SNAKE PATH
# ============================================================

def create_snake_path():

    points = []

    for y in range(ROWS):

        py = y * STEP + STEP / 2 + 10

        if y % 2 == 0:

            x_range = range(COLUMNS)

        else:

            x_range = range(COLUMNS - 1, -1, -1)

        for x in x_range:

            px = x * STEP + STEP / 2

            points.append((px, py))


    path = f"M {points[0][0]} {points[0][1]}"

    for px, py in points[1:]:

        path += f" L {px} {py}"

    return path


PATH = create_snake_path()


# ============================================================
# EATING ANIMATION
# ============================================================

def create_eating_effect():

    output = []

    total_cells = COLUMNS * ROWS

    duration = 24.0

    cell_time = duration / total_cells

    index = 0

    for y in range(ROWS):

        if y % 2 == 0:

            x_range = range(COLUMNS)

        else:

            x_range = range(COLUMNS - 1, -1, -1)

        for x in x_range:

            item = grid[x][y]

            if item["count"] > 0:

                px = x * STEP
                py = y * STEP + 10

                center_x = px + CELL / 2
                center_y = py + CELL / 2

                delay = index * cell_time

                output.append(
                    f'''
                    <g>

                        <!-- Bite flash -->

                        <circle
                            cx="{center_x}"
                            cy="{center_y}"
                            r="2"
                            fill="{WHITE}"
                            opacity="0"
                        >

                            <animate
                                attributeName="r"
                                values="2;8;2"
                                dur="0.35s"
                                begin="{delay:.3f}s"
                                repeatCount="indefinite"
                            />

                            <animate
                                attributeName="opacity"
                                values="0;1;0"
                                dur="0.35s"
                                begin="{delay:.3f}s"
                                repeatCount="indefinite"
                            />

                        </circle>


                        <!-- Cell gets eaten -->

                        <rect
                            x="{px}"
                            y="{py}"
                            width="{CELL}"
                            height="{CELL}"
                            rx="3"
                            fill="{BACKGROUND}"
                            opacity="0"
                        >

                            <animate
                                attributeName="opacity"
                                values="0;0;1;1;0"
                                keyTimes="0;0.45;0.55;0.95;1"
                                dur="{duration:.2f}s"
                                begin="{delay:.3f}s"
                                repeatCount="indefinite"
                            />

                        </rect>

                    </g>
                    '''
                )

            index += 1

    return "\n".join(output)


# ============================================================
# MONSTER BODY
# ============================================================

def create_body():

    output = []

    segments = 9

    for i in range(segments):

        delay = -(i * 0.10)

        radius = 6.5 - (i * 0.25)

        output.append(
            f'''
            <circle
                cx="0"
                cy="0"
                r="{radius:.2f}"
                fill="{GREEN}"
                opacity="0.95"
            >

                <animateMotion
                    dur="24s"
                    begin="{delay:.2f}s"
                    repeatCount="indefinite"
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

        <!-- Glow -->

        <circle
            cx="0"
            cy="0"
            r="15"
            fill="{GREEN}"
            opacity="0.15"
        >

            <animateMotion
                dur="24s"
                repeatCount="indefinite"
                path="{PATH}"
            />

        </circle>


        <!-- Head -->

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
            fill="#06140d"
        />


        <!-- LEFT EYE -->

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


        <!-- RIGHT EYE -->

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


        <!-- MOUTH -->

        <path
            d="
                M -6 2
                Q 0 9 6 2
                Q 0 5 -6 2
            "
            fill="#170008"
            stroke="{BLACK}"
            stroke-width="1"
        />


        <!-- TEETH -->

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
        />


        <!-- TONGUE -->

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


        <!-- HORNS -->

        <path
            d="
                M -6 -7
                L -9 -12
                L -3 -9

                M 6 -7
                L 9 -12
                L 3 -9
            "
            fill="{GREEN}"
            stroke="{BLACK}"
            stroke-width="1"
        />


        <!-- MOVEMENT -->

        <animateMotion
            dur="24s"
            repeatCount="indefinite"
            path="{PATH}"
        />

    </g>
    '''


# ============================================================
# SVG
# ============================================================

def create_svg():

    grid_svg = create_grid()

    eating_svg = create_eating_effect()

    body_svg = create_body()

    head_svg = create_head()

    return f'''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="100%"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="Animated monster GitHub contribution snake"
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
        x="10"
        y="{HEIGHT - 7}"
        font-family="Arial, sans-serif"
        font-size="8"
        fill="#6b7280"
    >
        🐍 MONSTER MODE • {USERNAME} • EATING CONTRIBUTIONS
    </text>

</svg>
'''


# ============================================================
# SAVE
# ============================================================

light_file = OUTPUT_DIR / "github-contribution-monster.svg"

dark_file = OUTPUT_DIR / "github-contribution-monster-dark.svg"


svg = create_svg()


light_file.write_text(
    svg,
    encoding="utf-8"
)

dark_file.write_text(
    svg,
    encoding="utf-8"
)


print("========================================")
print(" MONSTER SNAKE GENERATED")
print("========================================")
print("User:", USERNAME)
print("Contributions:", calendar["totalContributions"])
print("Output:", light_file)
print("Output:", dark_file)
