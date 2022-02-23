# ========== (c) JP Hwang 22/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import json
import os

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
shots_df.loc[shots_df["shotResult"] == "Made", "shot_made"] = 1
fig = viz.plot_hex_shot_chart(shots_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
fig = viz.add_shotchart_note(fig, title_txt="Shot chart", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
fig.show()
