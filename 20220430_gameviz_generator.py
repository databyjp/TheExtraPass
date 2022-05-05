# ========== (c) JP Hwang 1/5/2022  ==========

import logging
import pandas as pd
import utils
from nba_api.stats.static import teams, players
import datetime


logger = logging.getLogger(__name__)

desired_width = 320
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', desired_width)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
root_logger.addHandler(sh)

# Load data
season_df = pd.read_csv("data/proc_data/shots_pbp_2021-22.csv")
playoffs_df = pd.read_csv("data/proc_data/shots_pbp_2021-22_playoffs.csv")

# Add team name columns
season_df = utils.add_tm_name_cols(season_df)
playoffs_df = utils.add_tm_name_cols(playoffs_df)

"""
# ===== GENERATE GAME REVIEW CHART
# For each game:
#   Get season-long team stripcharts
#   Get playoff team charts
#   Get team charts
#   Develop strip charts for players also
"""

# Filter data for the latest day
playoffs_df = playoffs_df.assign(realtime_dt=pd.to_datetime(playoffs_df["realtime_dt"]))
latest_day = playoffs_df["realtime_dt"].max().date()

# latest_day = latest_day - datetime.timedelta(days=1)
# day_df = playoffs_df[playoffs_df["realtime_dt"].dt.date == latest_day]
# latest_day_str = f"{latest_day.day}_{latest_day.strftime('%b')}_{latest_day.strftime('%Y')}"
#
# # Get game IDs
# gm_ids = day_df.GAME_ID.unique()

gm_ids = playoffs_df.GAME_ID.unique()
for gm_id in gm_ids:
    shot_blot_dfs = list()
    gm_df = playoffs_df[playoffs_df.GAME_ID == gm_id]
    game_date = gm_df["realtime_dt"].min().date()
    game_date_str = f"{game_date.day}_{game_date.strftime('%b')}_{game_date.strftime('%Y')}"
    tm_ids = gm_df.teamId.unique()
    tm_abvs = [teams.find_team_name_by_id(tm_id)['abbreviation'] for tm_id in tm_ids]
    for tm_id in tm_ids:
        tmp_dfs = list()
        tm = teams.find_team_name_by_id(tm_id)
        logger.info(f'Analysing game {gm_id} for {tm["full_name"]}')
        tm_gm_df = gm_df[gm_df.teamId == tm_id]
        tm_gm_gdf = utils.get_shot_dist_df(tm_gm_df, playoffs_df)
        tm_gm_gdf = tm_gm_gdf.assign(segment=game_date_str)
        pl_gdf = utils.get_pl_shot_dist_df(tm_gm_df, season_df)
        pl_gdf = pl_gdf.assign(segment=game_date_str)
        pl_ranks = pl_gdf.groupby("group").sum()["shot_atts"].sort_values().index.to_list()[::-1]
        tm_playoffs_df = playoffs_df[playoffs_df.teamId == tm_id]
        tm_playoffs_gdf = utils.get_shot_dist_df(tm_playoffs_df, season_df)
        tm_playoffs_gdf = tm_playoffs_gdf.assign(group=f'{tm["abbreviation"]}_playoffs')
        tm_playoffs_gdf = tm_playoffs_gdf.assign(segment="Playoffs")
        tm_season_df = season_df[season_df.teamId == tm_id]
        tm_season_gdf = utils.get_shot_dist_df(tm_season_df, season_df)
        tm_season_gdf = tm_season_gdf.assign(group=f'{tm["abbreviation"]}_season')
        tm_season_gdf = tm_season_gdf.assign(segment="Regular Season")

        # Add dataframes together
        tmp_dfs.append(tm_gm_gdf)
        tmp_dfs.append(pl_gdf)
        tmp_dfs.append(tm_season_gdf)
        tmp_dfs.append(tm_playoffs_gdf)
        tmp_df = pd.concat(tmp_dfs)
        tmp_df = tmp_df.assign(team=tm["abbreviation"])

        # Add Overall dataframes together
        shot_blot_dfs.append(tmp_df)

    shot_blot_df = pd.concat(shot_blot_dfs)
    shot_blot_df = shot_blot_df.assign(filt_avg=(shot_blot_df["filt_start"] + shot_blot_df["filt_end"])/2)

    shot_blot_df.to_csv(f'temp/{tm_abvs[0]}_{tm_abvs[1]}_{game_date_str}.csv')
