# ========== (c) JP Hwang 2/2/2022  ==========
import pandas as pd
import os
import logging

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
            t_df = pd.read_csv(f"dl_data/tm_gamelogs_{yr_suffix}.csv")
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
