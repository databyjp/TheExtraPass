# ========== (c) JP Hwang 1/5/2022  ==========

import logging
import pandas as pd
import numpy as np
import utils
from nba_api.stats.static import teams
import plotly.express as px


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


# Add tm name columns
def add_tm_name_cols(pbp_df):
    import os
    tm_gamelogs_files = [f for f in os.listdir(utils.dl_dir) if utils.file_prefixes['tm_gamelogs'] in f]
    tmp_dfs = list()
    for fname in tm_gamelogs_files:
        fpath = os.path.join(utils.dl_dir, fname)
        tmp_df = pd.read_csv(fpath)
        tmp_dfs.append(tmp_df)
    gamelogs_df = pd.concat(tmp_dfs)

    pbp_df = pbp_df.assign(tm_abv=None)
    pbp_df = pbp_df.assign(opp_abv=None)
    for i, row in pbp_df.iterrows():
        pbp_df.loc[row.name, 'tm_abv'] = gamelogs_df[
            (gamelogs_df.GAME_ID == row["GAME_ID"]) &
            (gamelogs_df.TEAM_ID == row["teamId"])
            ]['TEAM_ABBREVIATION'].values[0]
        pbp_df.loc[row.name, 'opp_abv'] = gamelogs_df[
            (gamelogs_df.GAME_ID == row["GAME_ID"]) &
            (gamelogs_df.TEAM_ID != row["teamId"])
            ]['TEAM_ABBREVIATION'].values[0]
    return pbp_df


season_df = add_tm_name_cols(season_df)
playoffs_df = add_tm_name_cols(playoffs_df)
"""
Identify (1st round) matchups

# Build NBA average shot blots
# For each matchup:
#   For each team:
#       Build shot blots for regular season (Offence & Defence)
#       Build shot blots for regular season match-ups
#       Build shot blots for series (Offence only - defence is just the inverse of each other)
#       Build shot blots for game

# Identify interesting facets
# What stands out?
#   Which team has deviated the most from their usual pattern?

# Put together game summary viz 
#   Compare viz with width as a dimension - Width: shot freq? Colour: Accuracy? Points?
"""

nba_gdf = utils.calc_shot_dist_profile(season_df, "NBA")
shot_blot_dfs = [nba_gdf]
playoff_team_ids = playoffs_df.teamId.unique()
playoff_team_abvs = [teams.find_team_name_by_id(tm_id)['abbreviation'] for tm_id in playoff_team_ids]
for tm_id in playoffs_df.teamId.unique():
    tm = teams.find_team_name_by_id(tm_id)
    tm_abv = tm['abbreviation']
    tm_season_df = season_df[season_df.teamId == tm_id]
    tm_season_gdf = utils.calc_shot_dist_profile(tm_season_df, tm_abv + "_season")
    tm_playoffs_df = playoffs_df[playoffs_df.teamId == tm_id]
    tm_playoffs_gdf = utils.calc_shot_dist_profile(tm_playoffs_df, tm_abv + "_playoffs")
    shot_blot_dfs.append(tm_season_gdf)
    shot_blot_dfs.append(tm_playoffs_gdf)

shot_blot_df = pd.concat(shot_blot_dfs)
shot_blot_df = shot_blot_df.assign(filt_avg=(shot_blot_df["filt_start"] + shot_blot_df["filt_end"])/2)

# for tm in playoff_team_abvs:
tm = playoff_team_abvs[0]
tmp_df = shot_blot_df[shot_blot_df.group.str.contains(tm) | shot_blot_df.group.str.contains("NBA")]

fig = px.scatter(tmp_df,
                 title=f'{tm} - Playoff game shot profiles',
                 x="filt_avg", y="group", size="pts_pct",
                 color="shot_ev", color_continuous_scale=px.colors.sequential.Blues,
                 facet_col="shot_type",
                 template="plotly_white", width=1200, height=450,
                 range_color=[0.7, 1.7],
                 labels={'filt_avg': 'Distance from the rim', 'segment': 'Sample size',
                         'pts_pct_x': 'Proportion of points', 'shot_ev': 'Expected<BR>points<BR>per shot'}
                 )
fig.update_traces(marker=dict(line=dict(color="#b0b0b0", width=0.5)))
import re
for k in fig.layout:
    if re.search('xaxis+', k):
        fig.layout[k].update(matches=None)
        print(k)
        if k[-1] == 's' or int(k[-1]) % 2 != 0:
            fig.layout[k].update(domain=[0.0, 0.704])
        else:
            fig.layout[k].update(domain=[0.724, 0.98])
for i in fig.layout.annotations:
    if i['text'] == 'shot_type=3pt':
        i['x'] = 0.852


# Increase the overall top margin, and move the title up slightly
fig.update_layout(
    margin=dict(t=140),
    title={'y':0.95, 'yanchor': 'top'}
)

# Add the subhead
fig.add_annotation(text="Marker size: Percentage of team points from that distance (1ft radius)<BR>Marker colour: Efficiency (points per shot)",
                   xref="paper", yref="paper", align="left",
                   font=dict(color="slategrey"),
                   x=-0.065, y=1.15, showarrow=False)

fig.show()

# ============================================================
# Put together series summary viz
# ============================================================
# Build plot for an individual matchup

# ============================================================
# Put together game summary viz
# ============================================================
