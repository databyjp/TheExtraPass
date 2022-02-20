# ========== (c) JP Hwang 14/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import plotly.express as px
import json
import os
import utils
from PIL import Image

import sys
sys.path.append("/Users/jphwang/PycharmProjects/projects/prettyplotly")
from prettyplotly import looks

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

json_dir = "dl_data/box_scores/json"
json_files = [i for i in os.listdir(json_dir) if i.endswith("json")]

gldf = utils.load_pl_gamelogs()


def add_logo(fig_in, img_in, tm_name, logo_size, xloc, yloc, opacity=0.5):
    fig_in.add_layout_image(
        dict(
            source=img_in,
            xref="x",
            yref="y",
            xanchor="center",
            yanchor="middle",
            x=xloc,
            y=yloc,
            sizex=logo_size,
            sizey=logo_size,
            sizing="contain",
            layer="above",
            opacity=opacity,
        )
    )
    return fig_in


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


df_list = list()
for json_file in json_files:
    json_path = os.path.join(json_dir, json_file)
    with open(json_path, 'r') as f:
        content = json.load(f)
    tdf = box_json_to_df(content, data="team")
    df_list.append(tdf)
df = pd.concat(df_list)
df = df[df["GAME_ID"].str[:5] == "00221"]

df = pd.merge(
    df,
    gldf[["Game_ID", "gamedate_dt"]].drop_duplicates(),
    left_on="GAME_ID",
    right_on="Game_ID",
    how="left",
)

from datetime import datetime
df = df.assign(days_since_game=(datetime.today() - df["gamedate_dt"]).dt.days)
df = df.assign(inv_days_since_game=df["days_since_game"].max()-df["days_since_game"]+1)

rtg_mid = df["OFF_RATING"].median()
rtg_max = df["OFF_RATING"].max() + 10
rtg_min = df["OFF_RATING"].min() - 10

# VISUALISE INDIVIDUAL TEAM'S RATING

thresh_days = 20
highlight_tm = "Grizzlies"
color_dict = {
    "Jazz": ["#00471B", "#F9A01B"],
    "Nets": ["black", "#CD1041"],
    "Heat": ["#f9a01b", "#98002e"],
    "Bucks": ["#00471B", "#0077c0"],
    "76ers": ["#006bb6", "#ed174c"],
    "Celtics": ["#BA9653", "#007A33"],
    "Suns": ["#1d1160", "#e56020"],
    "Warriors": ["#1D428A", "#ffc72c"],
    "Bulls": ["#000000", "#CE1141"],
    "Clippers": ["#c8102E", "#1d428a"],
    "Grizzlies": ["#12173F", "#5D76A9"],
    "Cavaliers": ["#860038", "#FDBB30"],
}

for highlight_tm in ["Heat", "Bulls", "Bucks", "Cavaliers", "Suns", "Warriors", "Grizzlies", "Jazz", "Celtics", "Nets"]:
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

    fig = looks.like_d3(fig)

    fig['data'][0]['marker']['line']['color'] = "#b0b0b0"
    fig['data'][0]['marker']['opacity'] = 0.5
    fig['data'][1]['marker']['line']['color'] = "#333333"
    fig['data'][2]['marker']['line']['color'] = "#333333"
    # Add reference lines
    fig.add_hline(y=rtg_mid, line_width=0.5, line_color="#b0b0b0")
    fig.add_vline(x=rtg_mid, line_width=0.5, line_color="#b0b0b0")

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

    fig.update_layout(width=1000, height=850)
    fig.show()




# VISUALISE ALL RATINGS - by team
df = df.assign(win=0)
df.loc[df["NET_RATING"] > 0, "win"] = 1
agg_dict = {"OFF_RATING": "mean", "DEF_RATING": "mean", "win": "sum"}
gdf = df.groupby("TEAM_NAME").agg(agg_dict).reset_index()
gdf_30 = df[(df.days_since_game < 30)].groupby("TEAM_NAME").agg(agg_dict).reset_index()
gdf_30.columns = [i + "_Last30" if "TEAM" not in i else i for i in gdf_30.columns]

gdf = gdf.merge(
    gdf_30,
    on="TEAM_NAME",
    how="left"
)

gdf = gdf.assign(NET_RATING=gdf.OFF_RATING-gdf.DEF_RATING)
gdf = gdf.assign(NET_RATING_Last30=gdf.OFF_RATING_Last30-gdf.DEF_RATING_Last30)
gdf = gdf.assign(NET_NET_RATING=gdf.NET_RATING_Last30-gdf.NET_RATING)

gdf = gdf.rename({"NET_RATING": "Season", "NET_RATING_Last30": "Last 30 days", "NET_NET_RATING": "Recent vs season form"}, axis=1)

flatdf = gdf[["TEAM_NAME", "Season", "Last 30 days"]].melt(id_vars="TEAM_NAME", value_vars=["Season", "Last 30 days"])

fig = px.bar(flatdf[flatdf["variable"] == "Last 30 days"], x="TEAM_NAME", y="value", color="variable", barmode="group",
             title="NBA Form Guide (by net rating), as of Feb 14",
             category_orders={"TEAM_NAME": gdf.sort_values("Last 30 days", ascending=False)["TEAM_NAME"].to_list()},
             color_discrete_sequence=["#FF4500"],
             labels={"value": "Net rating", "TEAM_NAME": "Team", "variable": ""})

fig = looks.like_d3(fig)

for i in range(len(fig['data'])):
    fig['data'][i]['marker']['line']['color'] = 'dimgray'
    fig['data'][i]['marker']['line']['width'] = 1

fig.show()

gdf = gdf.assign(last_30_rel=gdf["Last 30 days"] - gdf["Last 30 days"].min() + 0.1)
fig = px.bar(gdf, x="TEAM_NAME", color="Recent vs season form", y="Last 30 days",
             title="NBA Form Guide (by net rating), as of Feb 16",
             category_orders={"TEAM_NAME": gdf.sort_values("win", ascending=False)["TEAM_NAME"].to_list()},
             color_continuous_scale=px.colors.diverging.RdYlBu[::-1],
             color_continuous_midpoint=0,
             labels={"value": "Net rating", "TEAM_NAME": "Team", "variable": "",
                     "Recent vs season form": "Form v Season", "Last 30 days": "Net rating - last 30 days"})

fig = looks.like_d3(fig)
fig['data'][0]['marker']['line']['width'] = 1
fig['data'][0]['marker']['line']['color'] = 'dimgray'

fig.add_annotation(x=-0.03, y=1.085,
                   yref="paper",
                   xref="paper",
                   text="<B>Bar length</B>: Net rating over the last 30 days<BR><B>Color</B>: Recent net rating - Season net rating".upper(),
                   xanchor="left",
                   showarrow=False)
fig.show()





gdf_std = df.groupby("TEAM_NAME").agg({"OFF_RATING": "std", "DEF_RATING": "std"}).reset_index()
gdf_std = gdf_std.rename({"OFF_RATING": "OFF_RATING_std", "DEF_RATING": "DEF_RATING_std"}, axis=1)

gdf = gdf.merge(
    gdf_std,
    on="TEAM_NAME",
    how="left"
)

tm_df = df[["TEAM_NAME", "TEAM_ABBREVIATION"]].drop_duplicates()
gdf = gdf.merge(
    tm_df,
    on="TEAM_NAME",
    how="left"
)

gdf = gdf.assign(std=(gdf["OFF_RATING_std"] + gdf["DEF_RATING_std"])/2)

fig = px.scatter(gdf, x="std", y="Recent vs season form",  size="win",
             title="Consistency vs Recent form - regression at work? (as of Feb 16)",
             category_orders={"TEAM_NAME": gdf.sort_values("win", ascending=False)["TEAM_NAME"].to_list()},
             color_continuous_scale=px.colors.diverging.RdYlBu[::-1],
             color_continuous_midpoint=0,
             labels={"value": "Net rating", "TEAM_NAME": "Team", "variable": "",
                     "OFF_RATING_std": "Offensive variance (higher -> LESS consistent)",
                     "DEF_RATING_std": "DEfensive variance (right -> LESS consistent)",
                     "std": "Consistency (lower is more consistent)",
                     "Recent vs season form": "Form v Season", "Last 30 days": "Net rating - last 30 days"})

fig = looks.like_d3(fig)
fig.add_annotation(x=-0.01, y=1.088,
                   yref="paper",
                   xref="paper",
                   text="Comparing recent form (last 30 days) vs consistency up until that point".upper(),
                   xanchor="left",
                   align="left",
                   showarrow=False)

team_list = gdf["TEAM_ABBREVIATION"].unique()
fig['data'][0]['marker']['size'] = 0.0001


for tmp_tm in team_list:
    tmpImg = Image.open(f"logos/{tmp_tm}-2021.png")
    fig = add_logo(
        fig,
        tmpImg,
        tmp_tm,
        2.2,
        xloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm]["std"].values[0],
        yloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm]["Recent vs season form"].values[0],
    )

fig.show()


fig = px.scatter(gdf, x="OFF_RATING_std", y="DEF_RATING_std", size="win",
             title="The most up & down NBA teams, as of Feb 16",
             category_orders={"TEAM_NAME": gdf.sort_values("win", ascending=False)["TEAM_NAME"].to_list()},
             labels={"value": "Net rating", "TEAM_NAME": "Team", "variable": "",
                     "OFF_RATING_std": "Offensive variance (higher -> LESS consistent)",
                     "DEF_RATING_std": "DEfensive variance (right -> LESS consistent)",
                     "Recent vs season form": "Form v Season", "Last 30 days": "Net rating - last 30 days"})

fig = looks.like_d3(fig)
fig.add_annotation(x=-0.01, y=1.088,
                   yref="paper",
                   xref="paper",
                   text="This chart captures how (in)consistent teams have been throughout the 2021-22 season to date".upper(),
                   xanchor="left",
                   align="left",
                   showarrow=False)
fig['data'][0]['marker']['size'] = 0.0001
for tmp_tm in team_list:
    tmpImg = Image.open(f"logos/{tmp_tm}-2021.png")
    fig = add_logo(
        fig,
        tmpImg,
        tmp_tm,
        0.75,
        xloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm]["OFF_RATING_std"].values[0],
        yloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm]["DEF_RATING_std"].values[0],
    )
fig.show()


xvar = "Season"
yvar = "Recent vs season form"
fig = px.scatter(gdf, x=xvar, y=yvar,
             title="Who's up & who's down in the NBA?".upper() + " (As of Feb 16)",
             category_orders={"TEAM_NAME": gdf.sort_values("win", ascending=False)["TEAM_NAME"].to_list()},
             labels={"value": "Net rating", "TEAM_NAME": "Team", "variable": "",
                     "OFF_RATING_std": "Offensive variance (higher -> LESS consistent)",
                     "DEF_RATING_std": "DEfensive variance (right -> LESS consistent)",
                     "Recent vs season form": "Form v Season", "Last 30 days": "Net rating - last 30 days"})

fig = looks.like_d3(fig)
fig.add_annotation(x=-0.01, y=1.088,
                   yref="paper",
                   xref="paper",
                   text="<B>Y-AXIS</B>: Team form by net rating (higher is better)<BR><B>X-AXIS</B>: Season-long net rating (right is better)",
                   xanchor="left",
                   align="left",
                   showarrow=False)
fig['data'][0]['marker']['size'] = 0.0001
for tmp_tm in team_list:
    tmpImg = Image.open(f"logos/{tmp_tm}-2021.png")
    fig = add_logo(
        fig,
        tmpImg,
        tmp_tm,
        2.1,
        xloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm][xvar].values[0],
        yloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm][yvar].values[0],
    )
fig.update_layout(width=1000)
fig.show()




xvar = "DEF_RATING_std"
yvar = "OFF_RATING_std"
fig = px.scatter(gdf, x=xvar, y=yvar,
             title="Which are the most inconsistent teams in the NBA?".upper() + " (As of Feb 16)",
             category_orders={"TEAM_NAME": gdf.sort_values("win", ascending=False)["TEAM_NAME"].to_list()},
             labels={"value": "Net rating", "TEAM_NAME": "Team", "variable": "",
                     "OFF_RATING_std": "Offensive variance (higher -> LESS consistent)",
                     "DEF_RATING_std": "Defensive variance (right -> LESS consistent)",
                     "Recent vs season form": "Form v Season", "Last 30 days": "Net rating - last 30 days"})

fig = looks.like_d3(fig)
fig.add_annotation(x=-0.01, y=1.088,
                   yref="paper",
                   xref="paper",
                   text="<B>X-AXIS</B>: Offensive variance (higher -> LESS consistent)<BR><B>Y-AXIS</B>: Defensive variance (right -> LESS consistent)",
                   xanchor="left",
                   align="left",
                   showarrow=False)
fig['data'][0]['marker']['size'] = 0.0001
for tmp_tm in team_list:
    tmpImg = Image.open(f"logos/{tmp_tm}-2021.png")
    fig = add_logo(
        fig,
        tmpImg,
        tmp_tm,
        2.1,
        xloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm][xvar].values[0],
        yloc=gdf[gdf.TEAM_ABBREVIATION == tmp_tm][yvar].values[0],
    )
fig.update_layout(width=1000)
fig.show()
