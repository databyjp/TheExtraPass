# ========== (c) JP Hwang 2/2/2022  ==========

import logging
import pandas as pd
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


if __name__ == "__main__":
    main()
