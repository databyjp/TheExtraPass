# ========== (c) JP Hwang 2/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import utils
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

desired_width = 320
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", desired_width)

dl_dir = utils.dl_dir


def fetch_pl_list(season_suffix):
    """
    Fetch the player list for a list, from the 'commonallplayers' endpoint
    :param season_suffix: The season to use - e.g. 2020-21
    :return: Pandas Dataframe
    """
    logger.info(f"Getting player list for {season_suffix}...")

    from nba_api.stats.endpoints import commonallplayers

    common_all_players = commonallplayers.CommonAllPlayers(
        league_id="00", season=season_suffix
    )
    df_pl = common_all_players.common_all_players.get_data_frame()
    df_pl.drop_duplicates().sort_values(by=["PERSON_ID"])
    df_pl = df_pl[df_pl.TEAM_ID != 0]

    logger.info(
        f"Fetched the players list for {season_suffix} with {len(df_pl)} players."
    )
    return df_pl


def fetch_season_pl_gamelogs(pid_list, season_suffix, test_mode=False):
    """
    Fetch players' game logs for a given season
    :param pid_list: List of API PERSON_IDs
    :param season_suffix: Season suffix string (e.g. '2020-21')
    :param test_mode: Bool for just getting a few logs
    :return: One dataframe with all the game log data
    """
    from nba_api.stats.endpoints import playergamelog

    counter = 0  # Counter for test mode
    counter_limit = 10
    df_gls = list()
    for pid in pid_list:
        df_gl = playergamelog.PlayerGameLog(
            season=season_suffix, player_id=pid
        ).player_game_log.get_data_frame()
        if len(df_gl) == 0:
            logger.warning(f"No games fetched for player {pid} in {season_suffix}!!")
        else:
            df_gls.append(df_gl)
            logger.info(
                f"Found game logs for {pid} in {season_suffix} with {len(df_gl)} games"
            )
        if test_mode:
            counter += 1
            if counter >= counter_limit:  # Limit for test mode
                break

    if len(df_gls) > 0:
        df_gl = pd.concat(df_gls)
    else:
        df_gl = None
    return df_gl


def update_season_pl_list(start_yr, end_yr):
    """
    Get player lists for all seasons
    :return:
    """
    for season_yr in range(start_yr, end_yr + 1):
        season_suffix = utils.year_to_season_suffix(season_yr)
        pl_list_outpath = os.path.join(
            dl_dir, f'{utils.file_prefixes["pl_list"]}_{season_suffix}.csv'
        )
        if not os.path.exists(pl_list_outpath) or season_yr == utils.curr_season_yr():
            df = fetch_pl_list(season_suffix)
            logger.info(f"Saving player data for {season_suffix}.")
            df.to_csv(pl_list_outpath, index=False)
        else:
            logger.info(f"Found player data for {season_suffix}, skipping download.")
    return True


def update_season_pl_gamelogs():
    """
    Update gamelogs for all seasons based on existing player list; skip any existing seasons
    :return: True
    """
    pl_lists = [f for f in os.listdir(dl_dir) if utils.file_prefixes["pl_list"] in f]
    pl_lists.sort()
    for fname in pl_lists[::-1]:  # Start from latest season
        fpath = os.path.join(dl_dir, fname)
        season_suffix = fname.split(".")[0][-7:]
        season_yr = utils.season_suffix_to_year(season_suffix)
        pl_gl_outpath = os.path.join(
            dl_dir, f'{utils.file_prefixes["pl_gamelogs"]}_{season_suffix}.csv'
        )

        if not os.path.exists(pl_gl_outpath) or season_yr == utils.curr_season_yr():
            pl_df = pd.read_csv(fpath)
            pid_list = pl_df["PERSON_ID"].to_list()
            df_gl = fetch_season_pl_gamelogs(pid_list, season_suffix, test_mode=False)
            if df_gl is not None:
                logger.info(
                    f"Finished fetching {len(df_gl)} game logs for {season_suffix}"
                )
                logger.info(f"Saving game log data for {season_suffix}.")
                df_gl.to_csv(pl_gl_outpath, index=False)
            else:
                logger.warning(
                    f"Was not able to fetch any game logs for {season_suffix}!"
                )
        else:
            logger.info(f"Found game log data for {season_suffix}, skipping download.")
    return True


def update_gamedata(json_dir, datatype):
    """
    Download availble game-based data from NBA API
    :param json_dir: Directory to save downloads to
    :return:
    """
    logger.info("Starting download of game box scores...")
    gldf = utils.load_tm_gamelogs()
    gldf = gldf.sort_values("gamedate_dt")
    gm_ids = gldf["GAME_ID"].unique()

    err_counter = 0
    for gm_id in gm_ids[::-1]:
        dl_succ = utils.fetch_data_w_gameid(json_dir, gm_id, datatype=datatype)
        if dl_succ is False:
            err_counter += 1
    logger.info(f"Finished downloading game box scores. {err_counter} errors encountered.")

    return True


def get_season_gamelogs(season_yr=None):
    """
    Downloads game logs for a given season
    :param season_yr:
    :return:
    """
    from nba_api.stats.endpoints import teamgamelogs
    tm_list = pd.read_csv("data/team_id_list.csv")
    if season_yr is None:
        season_yr = utils.curr_season_yr()
    season_suffix = utils.year_to_season_suffix(season_yr)

    tm_df_list = list()
    for i, row in tm_list.iterrows():
        team_id = row["TEAM_ID"]
        response = teamgamelogs.TeamGameLogs(
            team_id_nullable=str(team_id), season_nullable=season_suffix
        )
        content = json.loads(response.get_json())
        tm_df = utils.json_to_df(content)
        tm_df_list.append(tm_df)
    df = pd.concat(tm_df_list)
    df.to_csv(f"dl_data/tm_gamelogs_{season_suffix}.csv", index=False)
    return True


def process_pbp_logs():
    """
    Process all existing pbp data and save to file
    TODO - add parameter to process different seasons; also to save each season to different files
    :return:
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
    for pl_c in [c for c in gm_df.columns if "_player" in c]:
        proc_df[pl_c] = proc_df[pl_c].astype(int)
    proc_df.to_csv("data/proc_data/proc_pbp.csv", index=False)
    return True


def main():
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    log_fname = datetime.now().strftime("dl_log_%Y_%m_%d_%H_%M.log")
    fh = logging.FileHandler(f"logs/{log_fname}")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # update_season_pl_list(2015, 2021)
    get_season_gamelogs()
    update_gamedata(json_dir="dl_data/box_scores/json", datatype="boxscore")
    update_gamedata(json_dir="dl_data/pbp/json", datatype="pbp")
    process_pbp_logs()


if __name__ == "__main__":
    main()
