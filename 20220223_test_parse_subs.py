# ========== (c) JP Hwang 24/2/2022  ==========

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

df = df.assign(realtime_dt=pd.to_datetime(df["timeActual"]))

# ========== ADD ON-COURT PLAYERS ==========

df = df.sort_values(["GAME_ID", "actionNumber"])
df = df.reset_index(drop=True)

gm_id = df["GAME_ID"].unique()[0]
gm_df = df[df["GAME_ID"] == gm_id]

tm_ids = [i for i in gm_df["teamId"].unique() if not np.isnan(i)]

subs_df = gm_df[gm_df["actionType"] == "substitution"]

i = 1
subs_df = subs_df[subs_df["teamId"] == tm_ids[i]]
gm_df = gm_df[gm_df["teamId"] == tm_ids[i]]

starter_list = list()
sub_list = list()
for row in gm_df.itertuples():
    if row.actionType == "substitution":
        if row.subType == "out":
            if row.personId not in starter_list and row["personId"] not in sub_list:
                starter_list.append(row.personId)
        else:
            if row.personId not in sub_list:
                sub_list.append(row.personId)

for i in range(5):
    gm_df.loc[:, "player" + str(i+1)] = starter_list[i]

subout_buffer = list()
for row in gm_df.itertuples():
    if row.actionType == "substitution":
        if row.subType == "out":
            subout_buffer.append(row.personId)
        else:
            subout = subout_buffer.pop(0)
            for j in range(5):
                tmpcol = "player" + str(j+1)
                if getattr(row, tmpcol) == subout:
                    gm_df.loc[gm_df["actionNumber"] >= row.actionNumber, tmpcol] = row.personId

gm_df.to_csv("temp/sub_test.csv")

"""
Iterate from first row down
Main challenge: Need to infer starting player list; others known/knowable
"""
