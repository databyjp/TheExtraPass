# ========== (c) JP Hwang 24/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import json
import os
import utils

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
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

box_df = utils.load_box_scores(data="player")

gm_dfs = list()
for gm_id in df["GAME_ID"].unique():
    logger.info(f"Processing game {gm_id}")
    gm_df = df[df["GAME_ID"] == gm_id]

    tm_ids = [i for i in gm_df["teamId"].unique() if not np.isnan(i)]

    for tm_i in range(2):
        tm_id = tm_ids[tm_i]
        subs_df = gm_df[gm_df["actionType"] == "substitution"]
        subs_df = subs_df[subs_df["teamId"] == tm_id]
        tm_df = gm_df[gm_df["teamId"] == tm_id]

        starter_list = box_df[
            (box_df["TEAM_ID"] == tm_id) & (box_df["GAME_ID"] == gm_id) & (box_df["START_POSITION"] != "")
            ]["PLAYER_ID"].unique().tolist()

        for i in range(5):
            tm_df.loc[:, "player" + str(i+1)] = starter_list[i]

        subout_buffer = list()
        subin_buffer = list()
        for row in tm_df.itertuples():
            if row.actionType == "substitution":
                if row.subType == "out":
                    subout_buffer.append(row.personId)
                else:
                    subin_buffer.append(row.personId)

                if len(subin_buffer) > 0 and len(subout_buffer) > 0:
                    subout = subout_buffer.pop(0)
                    subin = subin_buffer.pop(0)
                    for j in range(5):
                        tmpcol = "player" + str(j+1)
                        if getattr(row, tmpcol) == subout:
                            tm_df.loc[tm_df["actionNumber"] >= row.actionNumber, tmpcol] = subin

        if len(subout_buffer) != 0 or len(subin_buffer) != 0:
            logger.warning(f"Something went wrong parsing {gm_id} for {tm_id}! subin_buffer: {subin_buffer}, subout_buffer: {subout_buffer}")

        tm_df.rename({"player" + str(j+1): f"tm_{tm_i}_player" + str(j+1) for j in range(5)}, axis=1, inplace=True)
        gm_df = pd.merge(
            gm_df,
            tm_df[["actionNumber"] + [f"tm_{tm_i}_player" + str(j+1) for j in range(5)]],
            left_on="actionNumber",
            right_on="actionNumber",
            how="left",
        )

    for tm_i in range(2):
        for j in range(5):
            gm_df[f"tm_{tm_i}_player{j+1}"] = gm_df[f"tm_{tm_i}_player{j+1}"].ffill().bfill()

    gm_dfs.append(gm_df)

proc_df = pd.concat(gm_dfs)
for pl_c in [c for c in gm_df.columns if "_player" in c]:
    proc_df[pl_c] = proc_df[pl_c].astype(int)
proc_df.to_csv("data/proc_data/proc_pbp.csv", index=False)
