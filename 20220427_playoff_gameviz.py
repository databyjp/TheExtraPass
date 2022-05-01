# ========== (c) JP Hwang 27/4/2022  ==========

import logging
import pandas as pd
import utils
from nba_api.stats.static import teams

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

"""
# Go through all the playoff games

# Identify & isolate PBP data for today's games

# Build shot blots for those games
# For each game:
#   For each team:
#       Build shot blots for regular season (Offence & Defence)
#       Build shot blots for regular season match-ups
#       Build shot blots for series to date (Offence only - defence is just the inverse of each other)
#       Build shot blots for game

# Identify interesting facets
# What stands out?
#   Which team has deviated the most from their usual pattern?

# Put together game summary viz 
#   Compare viz with width as a dimension - Width: shot freq? Colour: Accuracy? Points?
"""


# Load data
season_df = pd.read_csv("data/proc_data/shots_pbp_2021-22.csv")
playoffs_df = pd.read_csv("data/proc_data/shots_pbp_2021-22_playoffs.csv")

# ============================================================
# Identify & isolate PBP data for today's games
# ============================================================

# Filter data for the latest day
playoffs_df = playoffs_df.assign(realtime_dt=pd.to_datetime(playoffs_df["realtime_dt"]))
latest_day = playoffs_df["realtime_dt"].max().date()
day_df = playoffs_df[playoffs_df["realtime_dt"].dt.date == latest_day]

latest_day_str = f"{latest_day.day-1} {latest_day.strftime('%b')} {latest_day.strftime('%Y')}"

# Get game IDs
gm_ids = day_df.GAME_ID.unique()

# ============================================================
# Build shot blots for those games
# ============================================================
def get_shotblot_dists(gdf_a, gdf_b, col_name):
    from scipy.spatial.distance import cosine
    vec_a = gdf_a[col_name].values
    vec_b = gdf_b[col_name].values
    dist = cosine(vec_a, vec_b)
    return dist


shot_blot_dfs = list()
for gm_id in gm_ids:
    gm_df = day_df[day_df.GAME_ID == gm_id]
    tm_ids = gm_df.teamId.unique()
    for tm_id in tm_ids:
        tm = teams.find_team_name_by_id(tm_id)
        logger.info(f'Analysing game {gm_id} for {tm["full_name"]}')
        tm_gm_df = gm_df[gm_df.teamId == tm_id]
        tm_gm_gdf = utils.get_shot_dist_df(tm_gm_df, playoffs_df)
        tm_gm_gdf = tm_gm_gdf.assign(segment=latest_day_str)
        tm_playoffs_df = playoffs_df[playoffs_df.teamId == tm_id]
        tm_playoffs_gdf = utils.get_shot_dist_df(tm_playoffs_df, season_df)
        tm_playoffs_gdf = tm_playoffs_gdf.assign(segment="Playoffs")
        tm_season_df = season_df[season_df.teamId == tm_id]
        tm_season_gdf = utils.get_shot_dist_df(tm_season_df, season_df)
        tm_season_gdf = tm_season_gdf.assign(segment="Regular Season")

        # Compare shot blots
        cos_dist = get_shotblot_dists(tm_gm_gdf, tm_season_gdf, "shot_freq_x")
        logger.info(f'Cosine distance between game and reg season: {cos_dist}')
        cos_dist = get_shotblot_dists(tm_playoffs_gdf, tm_season_gdf, "shot_freq_x")
        logger.info(f'Cosine distance between playoffs and reg season: {cos_dist}')

        shot_blot_dfs.append(tm_gm_gdf)
        shot_blot_dfs.append(tm_playoffs_gdf)
        shot_blot_dfs.append(tm_season_gdf)

shot_blot_df = pd.concat(shot_blot_dfs)
shot_blot_df = shot_blot_df.assign(filt_avg=(shot_blot_df["filt_start"] + shot_blot_df["filt_end"])/2)

# ============================================================
# Initial viz
# ============================================================
import plotly.express as px
fig = px.scatter(shot_blot_df,
                 title=f'{latest_day_str} - Playoff game shot profiles',
                 x="filt_avg", y="segment", size="shot_freq_x",
                 color="shot_acc_x", color_continuous_scale=px.colors.sequential.Blues,
                 facet_row="group",
                 template="plotly_white", width=1200, height=750,
                 labels={'filt_avg': 'Distance from the rim', 'segment': 'Sample size',
                         'pts_pct_x': 'Proportion of points', 'shot_ev': 'Expected<BR>points<BR>per shot'}
                 )
fig.show()

# ============================================================
# Revised viz
# ============================================================
fig = px.scatter(shot_blot_df,
                 title=f'{latest_day_str} - Playoff game shot profiles',
                 x="filt_avg", y="segment", size="pts_pct_x",
                 color="shot_ev", color_continuous_scale=px.colors.sequential.Blues,
                 facet_row="group", facet_col="shot_type",
                 template="plotly_white", width=1200, height=750,
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
