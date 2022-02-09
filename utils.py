# ========== (c) JP Hwang 2/2/2022  ==========

file_prefixes = {
    'pl_list': 'common_all_players',
    'pl_gamelogs': 'pl_gamelogs'
}

dl_dir = 'dl_data'

logfile_prefix = 'dl_log_'


def year_to_season_suffix(season_yr):
    """
    Convert year to season suffix as used in the API
    * Note - will not work for pre-2000
    :param season_yr: Season - year in integer (first year in common season name e.g. 2020 for 2020-21)
    :return: Season suffix as string
    """
    return f'{season_yr}-{str(season_yr + 1)[-2:]}'


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
