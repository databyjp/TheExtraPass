# ========== (c) JP Hwang 2/2/2022  ==========

import pandas as pd
import numpy as np
import os
import logging
import json

logger = logging.getLogger(__name__)

# Parameters
file_prefixes = {"pl_list": "common_all_players", "pl_gamelogs": "pl_gamelogs"}
dl_dir = "dl_data"
logfile_prefix = "dl_log_"
def_start_year = 2015  # Default start year for multi-year based functions


def year_to_season_suffix(season_yr):
    """
    Convert year to season suffix as used in the API
    * Note - will not work for pre-2000
    :param season_yr: Season - year in integer (first year in common season name e.g. 2020 for 2020-21)
    :return: Season suffix as string
    """
    return f"{season_yr}-{str(season_yr + 1)[-2:]}"


def curr_season_yr():
    """
    Return the current season year (e.g. 2021 if Mar 2022 as still part of 2021-22 season, 2022 if Oct 2022)
    :return:
    """
    from datetime import datetime

    cur_yr = datetime.now().year
    if datetime.now().month <= 8:
        cur_yr -= 1
    return cur_yr


def season_suffix_to_year(season_suffix):
    """
    Convert season suffix as used in the API to year
    * Note - will not work for pre-2000
    :param season_suffix: Season suffix as string
    :return: year (int)
    """
    return int(season_suffix[2:4]) + 2000


def load_pl_gamelogs(st_year=None, end_year=None):
    if st_year is None:
        st_year = def_start_year
    if end_year is None:
        end_year = curr_season_yr() + 1

    gldf_list = list()
    for yr in range(st_year, end_year):
        yr_suffix = year_to_season_suffix(yr)
        t_df = pd.read_csv(f"dl_data/pl_gamelogs_{yr_suffix}.csv", dtype={"SEASON_ID": object, "Player_ID": object, "Game_ID": object})
        t_df = t_df.assign(season=yr_suffix)
        t_df = t_df.assign(eFG_PCT=((t_df["FGM"] * 2) + (t_df["FG3M"] * 3)) / ((t_df["FGA"] * 2) + (t_df["FG3A"] * 3)))
        gldf_list.append(t_df)
    gldf = pd.concat(gldf_list)

    gldf = gldf.assign(gamedate_dt=pd.to_datetime(gldf["GAME_DATE"]))
    return gldf


def load_tm_gamelogs(st_year=None, end_year=None):
    if st_year is None:
        st_year = def_start_year
    if end_year is None:
        end_year = curr_season_yr() + 1

    gldf_list = list()
    for yr in range(st_year, end_year):
        yr_suffix = year_to_season_suffix(yr)
        fpath = os.path.join("dl_data", f"tm_gamelogs_{yr_suffix}.csv")
        if os.path.exists(fpath):
            t_df = pd.read_csv(fpath, dtype={"GAME_ID": "str"})
            gldf_list.append(t_df)
        else:
            logger.warning(f"File not found at {fpath}")
    gldf = pd.concat(gldf_list)
    gldf = gldf.assign(gamedate_dt=pd.to_datetime(gldf["GAME_DATE"]))
    return gldf


def load_pl_list(st_year=None, end_year=None):
    if st_year is None:
        st_year = def_start_year
    if end_year is None:
        end_year = curr_season_yr() + 1

    pldf_list = list()
    for yr in range(st_year, end_year):
        yr_suffix = year_to_season_suffix(yr)
        t_pldf = pd.read_csv(f"dl_data/common_all_players_{yr_suffix}.csv", dtype={"PERSON_ID": object})
        pldf_list.append(t_pldf)
    pldf = pd.concat(pldf_list)
    pldf.drop_duplicates(inplace=True)
    return pldf


def json_to_df(content):
    df_list = list()
    for i in range(len(content["resultSets"])):
        results = content["resultSets"][i]
        headers = results["headers"]
        rows = results["rowSet"]
        tdf = pd.DataFrame(rows)
        tdf.columns = headers
        df_list.append(tdf)
    df_out = pd.concat(df_list)
    return df_out


def fetch_data_w_gameid(json_dir, gm_id, datatype="boxscore"):
    """
    Download a datafile based on gameID as downloaded from NBA API & saves to file
    :param json_dir: Directory for saving downloaded JSON
    :param gm_id: NBA game ID
    :param datatype: What data types to download - determines endpoint to use
    :return:
    """
    from nba_api.stats.endpoints import boxscoreadvancedv2
    from nba_api.live.nba.endpoints import playbyplay

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    if str(gm_id)[:2] != '00':
        gm_id = '00' + str(gm_id)

    dl_path = os.path.join(json_dir, gm_id + ".json")
    if os.path.exists(dl_path):
        logger.info(f"JSON found for game {gm_id}, skipping download.")
    else:
        try:
            logger.info(f"Downloading data for game {gm_id}")
            if datatype == "boxscore":
                response = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=gm_id)
            elif datatype == "pbp":
                response = playbyplay.PlayByPlay(gm_id)
            else:
                logger.warning("No data type supplied, downloading box score data by default")
                response = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=gm_id)

            content = json.loads(response.get_json())
            if type(content) == dict:
                with open(dl_path, 'w') as f:
                    json.dump(content, f)
                logger.info(f"Got data for game {gm_id}")
            else:
                logger.info(f"Saved data for game {gm_id} at {dl_path}")
        except:
            logger.error(f"Error getting data for game {gm_id}")
            return False

    return True


def box_json_to_df(content, data=None):
    """
    Load individual box score JSON to dataframe
    :param content: Content data returned by NBA API
    :param data: Specify player or team level data
    :return: DataFrame of single game box score
    """
    if data is None:
        sel_int = 1
    elif data == "player":
        sel_int = 0
    else:
        logger.warning("Unclear which data to load, loading team data by default.")
        sel_int = 1

    results = content["resultSets"][sel_int]
    headers = results["headers"]
    rows = results["rowSet"]
    df = pd.DataFrame(rows)
    df.columns = headers
    return df


def load_box_scores(data="team"):
    """
    Load all available box score data
    :param data: Specify player or team level data
    :return: DataFrame of multiple game box scores
    """
    json_dir = "dl_data/box_scores/json"
    json_files = [i for i in os.listdir(json_dir) if i.endswith("json")]

    df_list = list()
    for json_file in json_files:
        json_path = os.path.join(json_dir, json_file)
        with open(json_path, 'r') as f:
            content = json.load(f)
        tdf = box_json_to_df(content, data=data)
        df_list.append(tdf)
    df = pd.concat(df_list)
    return df


def load_pbp_jsons(st_year=None, end_year=None):
    """
    Load PBP JSON data
    :param st_year: Year to load data from (e.g. 20 for 2020-21 season)
    :param end_year: Year to load data to (e.g. 21 for 2021-22 season)
    :return: JSON dataframe
    TODO - actually filter JSON data based on year parameters; currently loading all data
    """
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
    return df


def add_pbp_oncourt_columns(df):
    """
    Add on-court player columns to the play-by-play dataframe.
    Players based on substitution data and box-score data (for starters)
    :param df: PBP dataframe
    :return:
    """
    df = df.sort_values(["GAME_ID", "actionNumber"])
    df = df.reset_index(drop=True)

    box_df = load_box_scores(data="player")

    gm_dfs = list()
    for gm_id in df["GAME_ID"].unique():
        logger.info(f"Processing game {gm_id}")
        gm_df = df[df["GAME_ID"] == gm_id]

        tm_ids = [i for i in gm_df["teamId"].unique() if not np.isnan(i)]

        for tm_i in range(2):
            tm_id = tm_ids[tm_i]
            tm_df = gm_df[gm_df["teamId"] == tm_id]

            starter_list = box_df[
                (box_df["TEAM_ID"] == tm_id) & (box_df["GAME_ID"] == gm_id) & (box_df["START_POSITION"] != "")
                ]["PLAYER_ID"].unique().tolist()

            for i in range(5):
                tm_df.loc[:, "player" + str(i + 1)] = starter_list[i]

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
                            tmpcol = "player" + str(j + 1)
                            if getattr(row, tmpcol) == subout:
                                tm_df.loc[tm_df["actionNumber"] >= row.actionNumber, tmpcol] = subin

            if len(subout_buffer) != 0 or len(subin_buffer) != 0:
                logger.warning(
                    f"Something went wrong parsing {gm_id} for {tm_id}! subin_buffer: {subin_buffer}, subout_buffer: {subout_buffer}")

            tm_df.rename({"player" + str(j + 1): f"tm_{tm_i}_player" + str(j + 1) for j in range(5)}, axis=1,
                         inplace=True)
            gm_df = pd.merge(
                gm_df,
                tm_df[["actionNumber"] + [f"tm_{tm_i}_player" + str(j + 1) for j in range(5)]],
                left_on="actionNumber",
                right_on="actionNumber",
                how="left",
            )

        for tm_i in range(2):
            for j in range(5):
                gm_df[f"tm_{tm_i}_player{j + 1}"] = gm_df[f"tm_{tm_i}_player{j + 1}"].ffill().bfill()

        gm_dfs.append(gm_df)

    proc_df = pd.concat(gm_dfs)
    for pl_c in [c for c in proc_df.columns if "_player" in c]:
        proc_df[pl_c] = proc_df[pl_c].astype(int)

    return proc_df
