# ========== (c) JP Hwang 14/2/2022  ==========

import logging
import pandas as pd
import plotly.express as px
import json
import os
import utils
from datetime import datetime

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
root_logger.addHandler(sh)

desired_width = 320
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', desired_width)

# ===== PRE-PROCESSING (as briefly described in the blog) =====

json_dir = "dl_data/box_scores/json"
json_files = [i for i in os.listdir(json_dir) if i.endswith("json")]


# Function to load JSON data - will eventually be moved to another module
def box_json_to_df(content, data="team"):
    if data == "team":
        sel_int = 1
    elif data == "player":
        sel_int = 0
    else:
        logger.warning("")

    results = content["resultSets"][sel_int]
    headers = results["headers"]
    rows = results["rowSet"]
    df = pd.DataFrame(rows)
    df.columns = headers
    return df


# Combine all team box scores into one dataframe
df_list = list()
for json_file in json_files:
    json_path = os.path.join(json_dir, json_file)
    with open(json_path, 'r') as f:
        content = json.load(f)
    tdf = box_json_to_df(content, data="team")
    df_list.append(tdf)
df = pd.concat(df_list)
df = df[df["GAME_ID"].str[:5] == "00221"]

# Merge/Join data from player logs as box score data doesn't include dates
gldf = utils.load_tm_gamelogs()
df = pd.merge(
    df,
    gldf[["GAME_ID", "gamedate_dt"]].drop_duplicates(),
    left_on="GAME_ID",
    right_on="GAME_ID",
    how="left",
)

# ===== REAL FUN BEGINS HERE - LET'S VISUALISE BOX SCORE DATA =====

color_dict = {
    "Jazz": ["#00471B", "#F9A01B"],
    "Nets": ["gray", "black"],
    "Heat": ["#f9a01b", "#98002e"],
    "Bucks": ["#0077c0", "#00471B"],
    "76ers": ["#006bb6", "#ed174c"],
    "Celtics": ["#BA9653", "#007A33"],
    "Suns": ["#1d1160", "#e56020"],
    "Warriors": ["#ffc72c", "#1D428A"],
    "Bulls": ["#000000", "#CE1141"],
    "Clippers": ["#c8102E", "#1d428a"],
    "Grizzlies": ["#5D76A9", "#12173F"],
    "Cavaliers": ["#860038", "#FDBB30"],
}

highlight_tm = "Grizzlies"
df = df.assign(legend="Other teams")
df.loc[df["TEAM_NAME"] == highlight_tm, "legend"] = highlight_tm

fig = px.scatter(df, x="DEF_RATING", y="OFF_RATING", color="legend",
                 title=f"The {highlight_tm} game-by-game - '21-'22",
                 color_discrete_sequence=["#dddddd", "#5D76A9"],
                 template="plotly_white", width=800, height=650,
                 labels={"OFF_RATING": "Offensive Rating (higher is better)",
                         "DEF_RATING": "Dffensive Rating (to the left is better)"})
fig.show()

# ========== Let's make some changes ==========
# Add days since game as a column
df = df.assign(days_since_game=(datetime.today() - df["gamedate_dt"]).dt.days)
df = df.assign(inv_days_since_game=df["days_since_game"].max()-df["days_since_game"]+1)

rtg_mid = df["OFF_RATING"].median()
rtg_max = df["OFF_RATING"].max() + 10
rtg_min = df["OFF_RATING"].min() - 10

# VISUALISE INDIVIDUAL TEAM'S RATING

thresh_days = 20
df = df.assign(legend="Other teams")
df.loc[df["TEAM_NAME"] == highlight_tm, "legend"] = f"{thresh_days}+ days ago"
df.loc[(df.days_since_game < thresh_days) & (df["TEAM_NAME"] == highlight_tm), "legend"] = f"In the last {thresh_days} days"

fig = px.scatter(df, x="DEF_RATING", y="OFF_RATING",
                 color="legend",
                 title=f"Game-by-game performances by the {highlight_tm} - '21-'22",
                 color_discrete_sequence=["#eeeeee", color_dict[highlight_tm][0], color_dict[highlight_tm][1]],
                 size="inv_days_since_game",
                 size_max=22,
                 template="plotly_white",
                 width=1200, height=800,
                 labels={"OFF_RATING": "Offensive Rating (higher is better)",
                         "DEF_RATING": "Dffensive Rating (to the left is better)",
                         "legend": ""}
                 )
fig['data'][0]['marker']['line']['color'] = "#b0b0b0"
fig['data'][0]['marker']['opacity'] = 0.5
# Add reference lines
fig.add_hline(y=rtg_mid, line_width=1, line_color="#b0b0b0")
fig.add_vline(x=rtg_mid, line_width=1, line_color="#b0b0b0")
fig.show()

for highlight_tm in ["Heat", "Bulls", "Bucks", "Cavaliers", "Suns", "Warriors", "Grizzlies", "Jazz", "Celtics"]:
    df = df.assign(legend="Other teams")
    df.loc[df["TEAM_NAME"] == highlight_tm, "legend"] = f"{thresh_days}+ days ago"
    df.loc[(df.days_since_game < thresh_days) & (
            df["TEAM_NAME"] == highlight_tm), "legend"] = f"In the last {thresh_days} days"

    fig = px.scatter(df, x="DEF_RATING", y="OFF_RATING",
                     color="legend",
                     title=f"Game-by-game performances by the {highlight_tm} - '21-'22",
                     color_discrete_sequence=["#eeeeee", color_dict[highlight_tm][0], color_dict[highlight_tm][1]],
                     size="inv_days_since_game",
                     size_max=22,
                     template="plotly_white",
                     width=1200, height=800,
                     labels={"OFF_RATING": "Offensive Rating (higher is better)",
                             "DEF_RATING": "Dffensive Rating (to the left is better)",
                             "legend": ""}
                     )

    fig['data'][0]['marker']['line']['color'] = "#b0b0b0"
    fig['data'][0]['marker']['opacity'] = 0.5
    fig['data'][1]['marker']['opacity'] = 0.8
    fig['data'][2]['marker']['opacity'] = 0.8
    fig['data'][1]['marker']['line']['color'] = "#333333"
    fig['data'][2]['marker']['line']['color'] = "#333333"
    # Add reference lines
    fig.add_hline(y=rtg_mid, line_width=0.5, line_color="#b0b0b0")
    fig.add_vline(x=rtg_mid, line_width=0.5, line_color="#b0b0b0")

    # Add further annotations
    fig.add_shape(type="rect",
                  x0=rtg_min, y0=rtg_mid, x1=rtg_mid, y1=rtg_max,
                  fillcolor="LightSeaGreen",
                  opacity=0.25,
                  line_width=0,
                  layer="below"
                  )
    fig.add_shape(type="rect",
                  x0=rtg_mid, y0=rtg_min, x1=rtg_max, y1=rtg_mid,
                  fillcolor="LightSteelBlue",
                  opacity=0.25,
                  line_width=0,
                  layer="below"
                  )

    fig.add_annotation(x=rtg_min + 3, y=rtg_max - 3,
                       text="Very good".upper(),
                       xanchor="left",
                       showarrow=False)
    fig.add_annotation(x=rtg_max - 3, y=rtg_min + 3,
                       text="Very bad".upper(),
                       xanchor="right",
                       showarrow=False)
    fig.add_annotation(x=rtg_min + 3, y=rtg_min + 3,
                       text="Bad O, Good D".upper(),
                       xanchor="left",
                       showarrow=False)
    fig.add_annotation(x=rtg_max - 3, y=rtg_max - 3,
                       text="Good O, Bad D".upper(),
                       xanchor="right",
                       showarrow=False)

    main_font = '"Source Sans Pro", "PT Sans", "Raleway", "Open Sans"'
    fig.update_layout(font_family=main_font)

    fig.show()
