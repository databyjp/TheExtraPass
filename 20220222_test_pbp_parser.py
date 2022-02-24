# ========== (c) JP Hwang 22/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import json
import os
import sys
sys.path.append("/Users/jphwang/PycharmProjects/projects/prettyplotly")
from prettyplotly import looks
import dataproc

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

json_dir = "dl_data/pbp/json"
json_files = [i for i in os.listdir(json_dir) if i.endswith("json")]


def pbp_json_to_df(content):
    df = pd.DataFrame(content['game']['actions'])
    df["GAME_ID"] = content["game"]['gameId']
    return df


df_list = list()
for json_file in json_files:
    json_path = os.path.join(json_dir, json_file)
    with open(json_path, 'r') as f:
        content = json.load(f)
    tdf = pbp_json_to_df(content)
    df_list.append(tdf)
df = pd.concat(df_list)

import viz
import plotly.express as px
shots_df = df[(df["actionType"] == "2pt") | (df["actionType"] == "3pt")]
shots_df["original_x"] = shots_df["xLegacy"]
shots_df["original_y"] = shots_df["yLegacy"]
shots_df["shot_made"] = 0
shots_df = shots_df.assign(shot_zone=dataproc.get_zones(shots_df["original_x"].tolist(), shots_df["original_y"].tolist(), excl_angle=True))

shots_df = shots_df.assign(dist_bin=1.5 + (shots_df["shotDistance"]/3).apply(np.floor).astype(int) * 3)

shots_df.loc[shots_df["shotResult"] == "Made", "shot_made"] = 1

# fig = viz.plot_hex_shot_chart(shots_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
# fig = viz.add_shotchart_note(fig, title_txt="Shot chart", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
# fig.show()

color_dict = {
    "Jazz": ["#00471B", "#F9A01B"],
    "Nets": ["gray", "black"],
    "Heat": ["#f9a01b", "#98002e"],
    "Bucks": ["#0077c0", "#00471B"],
    "76ers": ["#006bb6", "#ed174c"],
    "Celtics": ["#007A33", "#BA9653"],
    "Suns": ["#1d1160", "#e56020"],
    "Warriors": ["#ffc72c", "#1D428A"],
    "Bulls": ["#000000", "#CE1141"],
    "Clippers": ["#c8102E", "#1d428a"],
    "Grizzlies": ["#5D76A9", "#12173F"],
    "Cavaliers": ["#860038", "#FDBB30"],
}

tm_name = 'Warriors'
tm_ids = pd.read_csv("data/team_id_list.csv")
tm_id = tm_ids[tm_ids["TEAM_NAME"] == tm_name]["TEAM_ID"].values[0]

tm_df = shots_df[shots_df["teamId"] == tm_id]
# fig = viz.plot_hex_shot_chart(tm_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
# fig = viz.add_shotchart_note(fig, title_txt="Team Shot chart", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
# fig.show()


json_dir = "dl_data/box_scores/json"
json_files = [i for i in os.listdir(json_dir) if i.endswith("json")]

import utils
gldf = utils.load_tm_gamelogs()


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
    df_out = pd.DataFrame(rows)
    df_out.columns = headers
    return df_out


df_list = list()
for json_file in json_files:
    json_path = os.path.join(json_dir, json_file)
    with open(json_path, 'r') as f:
        content = json.load(f)
    tdf = box_json_to_df(content, data="team")
    df_list.append(tdf)
box_df = pd.concat(df_list)
box_df = box_df[box_df["GAME_ID"].str[:5] == "00221"]

gldf["GAME_ID"] = '00' + gldf["GAME_ID"].astype(str)
box_df = pd.merge(
    box_df,
    gldf[["GAME_ID", "gamedate_dt"]],
    left_on="GAME_ID",
    right_on="GAME_ID",
    how="left",
)

from datetime import datetime
box_df = box_df.assign(days_since_game=(datetime.today() - box_df["gamedate_dt"]).dt.days)
box_df = box_df.assign(inv_days_since_game=box_df["days_since_game"].max()-box_df["days_since_game"]+1)

tm_df = box_df[box_df["TEAM_ID"] == tm_id]
tm_games = tm_df["GAME_ID"].unique()
threshold = 30
rec_games = tm_df[tm_df["days_since_game"] < 30]["GAME_ID"].unique()
old_games = tm_df[tm_df["days_since_game"] >= 30]["GAME_ID"].unique()

opp_df = shots_df[(shots_df["GAME_ID"].isin(tm_games)) & (shots_df["teamId"] != tm_id)]
rec_opp_df = shots_df[(shots_df["GAME_ID"].isin(rec_games)) & (shots_df["teamId"] != tm_id)]
old_opp_df = shots_df[(shots_df["GAME_ID"].isin(old_games)) & (shots_df["teamId"] != tm_id)]

# fig = viz.plot_hex_shot_chart(opp_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
# fig = viz.add_shotchart_note(fig, title_txt="Opponent Shot chart", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
# fig.show()

# fig = viz.plot_hex_shot_chart(rec_opp_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
# fig = viz.add_shotchart_note(fig, title_txt="Opponent Shot chart - Last 30 days", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
# fig.show()

# fig = viz.plot_hex_shot_chart(old_opp_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
# fig = viz.add_shotchart_note(fig, title_txt="Opponent Shot chart - 30+ days ago", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
# fig.show()

# gdf_rec = rec_opp_df.groupby(["dist_bin", "actionType"]).agg({"shot_made": "sum", "actionNumber": "count"}).reset_index()
# gdf_rec = gdf_rec.assign(shot_freq=gdf_rec["actionNumber"] / gdf_rec["actionNumber"].sum())
# gdf_rec = gdf_rec.assign(shot_acc=gdf_rec["shot_made"] / gdf_rec["actionNumber"])
# gdf_rec = gdf_rec.assign(pps=gdf_rec["shot_acc"] * 2)
# gdf_rec.loc[gdf_rec["actionType"] == "3pt", "pps"] = gdf_rec[gdf_rec["actionType"] == "3pt"]["shot_acc"] * 3
#
# gdf_old = old_opp_df.groupby(["dist_bin", "actionType"]).agg({"shot_made": "sum", "actionNumber": "count"}).reset_index()
# gdf_old = gdf_old.assign(shot_freq=gdf_old["actionNumber"] / gdf_old["actionNumber"].sum())
# gdf_old = gdf_old.assign(shot_acc=gdf_old["shot_made"] / gdf_old["actionNumber"])
# gdf_old = gdf_old.assign(pps=gdf_old["shot_acc"] * 2)
# gdf_old.loc[gdf_old["actionType"] == "3pt", "pps"] = gdf_old[gdf_old["actionType"] == "3pt"]["shot_acc"] * 3
#
# gdf_rel = gdf_rec[["dist_bin", "actionType"]]
# gdf_rel = gdf_rel.assign(rel_freq=gdf_rec["shot_freq"] - gdf_old["shot_freq"])
# gdf_rel = gdf_rel.assign(rel_pps=gdf_rec["pps"] - gdf_old["pps"])
# gdf_rel = gdf_rel.assign(abs_freq=(gdf_rec["actionNumber"] + gdf_old["actionNumber"]) / (gdf_rec["actionNumber"] + gdf_old["actionNumber"]).sum())
# gdf_rel = gdf_rel.assign(rel_acc=gdf_rec["shot_acc"] - gdf_old["shot_acc"])
#
# gdf_rec = gdf_rec.assign(dataset="Within last 30 days")
# gdf_old = gdf_old.assign(dataset="30+ days ago")
#
# gdf = pd.concat([gdf_rec, gdf_old])
#
# fig = px.bar(gdf, y="pps", x="dist_bin",
#              facet_row="dataset", facet_col="actionType", barmode="group", color="shot_acc",
#              range_x=[0, 32], range_y=[0, 1.5])
# fig = looks.like_d3(fig)
# fig.show()
#
# fig = px.bar(gdf_rel, y="rel_freq", x="dist_bin", color="rel_pps",
#              range_x=[0, 32], range_y=[gdf_rel["rel_freq"].min(), gdf_rel["rel_freq"].max()],
#              color_continuous_scale=px.colors.diverging.RdYlBu_r, color_continuous_midpoint=0)
# fig = looks.like_d3(fig)
# fig.show()
#
# fig = px.scatter(gdf, y="shot_acc", x="dist_bin", size="shot_freq",
#                  facet_col="actionType", color="dataset",
#                  range_x=[0, 37], range_y=[0, 1])
# fig = looks.like_d3(fig)
# fig.show()
# for i in range(df.shape[0]):
#     fig.add_shape(
#         type='line',
#         x0=df['Women'].iloc[i], y0=df['School'].iloc[i],
#         x1=df['Men'].iloc[i], y1=df['School'].iloc[i],
#         line_color="#cccccc"
#     )
# fig.show()
#
# fig = px.scatter(gdf_rel[gdf_rel["dist_bin"] < 36], y="rel_acc", x="abs_freq",
#                  color="actionType")
# fig = looks.like_d3(fig)
# fig.show()
#


gdf_rec = rec_opp_df.groupby("shot_zone").agg({"shot_made": "sum", "actionNumber": "count"}).reset_index()
gdf_rec = gdf_rec.assign(shot_freq=gdf_rec["actionNumber"] / gdf_rec["actionNumber"].sum())
gdf_rec = gdf_rec.assign(shot_acc=gdf_rec["shot_made"] / gdf_rec["actionNumber"])
gdf_rec = gdf_rec.assign(pps=gdf_rec["shot_acc"] * 2)
# gdf_rec.loc[gdf_rec["actionType"] == "3pt", "pps"] = gdf_rec[gdf_rec["actionType"] == "3pt"]["shot_acc"] * 3

gdf_old = old_opp_df.groupby("shot_zone").agg({"shot_made": "sum", "actionNumber": "count"}).reset_index()
gdf_old = gdf_old.assign(shot_freq=gdf_old["actionNumber"] / gdf_old["actionNumber"].sum())
gdf_old = gdf_old.assign(shot_acc=gdf_old["shot_made"] / gdf_old["actionNumber"])
gdf_old = gdf_old.assign(pps=gdf_old["shot_acc"] * 2)
# gdf_old.loc[gdf_old["actionType"] == "3pt", "pps"] = gdf_old[gdf_old["actionType"] == "3pt"]["shot_acc"] * 3

gdf_rel = gdf_rec[["shot_zone"]]
gdf_rel = gdf_rel.assign(rel_freq=gdf_rec["shot_freq"] - gdf_old["shot_freq"])
gdf_rel = gdf_rel.assign(rel_pps=gdf_rec["pps"] - gdf_old["pps"])
gdf_rel = gdf_rel.assign(abs_freq=(gdf_rec["actionNumber"] + gdf_old["actionNumber"]) / (gdf_rec["actionNumber"] + gdf_old["actionNumber"]).sum())
gdf_rel = gdf_rel.assign(rel_acc=gdf_rec["shot_acc"] - gdf_old["shot_acc"])

gdf_rec = gdf_rec.assign(dataset="Within last 30 days")
gdf_old = gdf_old.assign(dataset="30+ days ago")

gdf = pd.concat([gdf_rec, gdf_old])

gdf["shot_freq"] = gdf["shot_freq"] * 100
gdf["shot_acc"] = gdf["shot_acc"] * 100
# fig = px.bar(gdf, title=f"{tm_name} - Trends in opponents' shot locations".upper() + " (as of All-Star break)",
#              y="shot_freq", x="shot_zone",
#              color="dataset", barmode="group",
#              labels={"shot_freq": "Portion of Oppnent Shots Taken (%)", "shot_zone": "Zone",
#                      "shot_acc": "Shot Accuracy (%)"},
#              color_discrete_sequence=color_dict[tm_name],
#              )
# fig = looks.like_d3(fig)
# fig.show()
#
# fig = px.bar(gdf, title=f"{tm_name} - Trends in opponents' shot accuracy".upper() + " (as of All-Star break)",
#              y="shot_acc", x="shot_zone",
#              color="dataset", barmode="group",
#              labels={"shot_freq": "Portion of Oppnent Shots Taken (%)", "shot_zone": "Zone",
#                      "shot_acc": "Shot Accuracy (%)"},
#              color_discrete_sequence=color_dict[tm_name],
#              )
# fig = looks.like_d3(fig)
# fig.show()


# fig = px.scatter(gdf, x="shot_zone", size="shot_freq", y="shot_acc", color="dataset")
# fig = looks.like_d3(fig)
# fig.show()

# In more detail
grp_vars = ["shot_zone", "subType", "descriptor"]
grp_vars = ["shot_zone", "subType"]

gdf_rec = rec_opp_df.groupby(grp_vars).agg({"shot_made": "sum", "actionNumber": "count"}).reset_index()
gdf_rec = gdf_rec.assign(shot_freq=gdf_rec["actionNumber"] / gdf_rec["actionNumber"].sum())
gdf_rec = gdf_rec.assign(shot_acc=gdf_rec["shot_made"] / gdf_rec["actionNumber"])
gdf_rec = gdf_rec.assign(pps=gdf_rec["shot_acc"] * 2)
gdf_rec.loc[gdf_rec["shot_zone"].str[0].astype(int) > 3, "pps"] = gdf_rec.loc[gdf_rec["shot_zone"].str[0].astype(int) > 3]["shot_acc"] * 3

gdf_old = old_opp_df.groupby(grp_vars).agg({"shot_made": "sum", "actionNumber": "count"}).reset_index()
gdf_old = gdf_old.assign(shot_freq=gdf_old["actionNumber"] / gdf_old["actionNumber"].sum())
gdf_old = gdf_old.assign(shot_acc=gdf_old["shot_made"] / gdf_old["actionNumber"])
gdf_old = gdf_old.assign(pps=gdf_old["shot_acc"] * 2)
gdf_old.loc[gdf_old["shot_zone"].str[0].astype(int) > 3, "pps"] = gdf_old.loc[gdf_old["shot_zone"].str[0].astype(int) > 3]["shot_acc"] * 3

gdf_rel = gdf_rec[grp_vars]
gdf_rel = gdf_rel.assign(rel_freq=gdf_rec["shot_freq"] - gdf_old["shot_freq"])
gdf_rel = gdf_rel.assign(rel_pps=gdf_rec["pps"] - gdf_old["pps"])
gdf_rel = gdf_rel.assign(abs_freq=(gdf_rec["actionNumber"] + gdf_old["actionNumber"]) / (gdf_rec["actionNumber"] + gdf_old["actionNumber"]).sum())
gdf_rel = gdf_rel.assign(rel_acc=gdf_rec["shot_acc"] - gdf_old["shot_acc"])

gdf_rec = gdf_rec.assign(dataset="Within last 30 days")
gdf_old = gdf_old.assign(dataset="30+ days ago")

gdf = pd.concat([gdf_rec, gdf_old])

gdf["shot_freq"] = gdf["shot_freq"] * 100
gdf["shot_acc"] = gdf["shot_acc"] * 100

# fig = px.bar(gdf, title=f"{tm_name} - Trends in opponents' shot locations".upper() + " (as of All-Star break)",
#              y="shot_freq", x="shot_zone", color="subType",
#              facet_row="dataset", barmode="group",
#              labels={"shot_freq": "Portion of Oppnent Shots Taken (%)", "shot_zone": "Zone",
#                      "shot_acc": "Shot Accuracy (%)"},
#              color_discrete_sequence=px.colors.qualitative.Safe,
#              )
# fig = looks.like_d3(fig)
# fig.show()


fig = px.bar(gdf_rel, title=f"{tm_name} - Trends in opponents' shot locations".upper() + " (as of All-Star break)",
             y="rel_freq", x="shot_zone", color="subType",
             barmode="group",
             labels={"shot_freq": "Portion of Oppnent Shots Taken (%)", "shot_zone": "Zone",
                     "shot_acc": "Shot Accuracy (%)"},
             color_discrete_sequence=px.colors.qualitative.Safe,
             )
fig = looks.like_d3(fig)
fig.show()

fig = px.bar(gdf_rel, title=f"{tm_name} - Trends in opponents' shot accuracies".upper() + " (as of All-Star break)",
             y="rel_acc", x="shot_zone", color="subType",
             barmode="group",
             labels={"shot_freq": "Portion of Oppnent Shots Taken (%)", "shot_zone": "Zone",
                     "shot_acc": "Shot Accuracy (%)"},
             color_discrete_sequence=px.colors.qualitative.Safe,
             )
fig = looks.like_d3(fig)
fig.show()


fig = px.scatter(gdf_rel, title=f"{tm_name} - Trends in opponents' shot accuracies".upper() + " (as of All-Star break)",
             y="rel_acc", x="shot_zone", color="subType",
             size="abs_freq",
             labels={"shot_freq": "Portion of Oppnent Shots Taken (%)", "shot_zone": "Zone",
                     "shot_acc": "Shot Accuracy (%)"},
             color_discrete_sequence=px.colors.qualitative.Safe,
             )
fig = looks.like_d3(fig)
fig.show()



