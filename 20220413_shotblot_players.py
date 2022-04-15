# ========== (c) JP Hwang 14/4/2022  ==========

import logging
import pandas as pd
import utils
from scipy.spatial.distance import cosine
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

shots_df = utils.load_shots_df()
ref_gdf = utils.calc_shot_dist_profile(shots_df, "NBA")
gdf = utils.get_shot_dist_df(shots_df)

# FILTER GAMES FOR THE LATEST DAY
day_df = shots_df[shots_df["timeActual"].dt.date == shots_df["timeActual"].dt.date.max()]
gm_ids = day_df.GAME_ID.unique().tolist()

# for gm_id in gm_ids:  # OUTER LOOP FOR EACH GAME
gm_id = gm_ids[0]
gm_df = day_df[day_df.GAME_ID == gm_id]

tm_ids = gm_df.teamId.unique().tolist()
# for tm_id in tm_ids:
tm_id = tm_ids[0]

tm_abv = teams.find_team_name_by_id(tm_id)["abbreviation"]
tm_gdf = gdf[gdf["group"] == tm_abv]

tm_gm_df = gm_df[gm_df.teamId == tm_id]

from nba_api.stats.static import players

pl_ids = tm_gm_df.personId.unique()
pl_gdfs = list()
for pl_id in pl_ids:
    pl_gm_df = tm_gm_df[tm_gm_df.personId == pl_id]
    if (len(pl_gm_df)) > 0:
        pl_gm_gdf = utils.get_shot_dist_df(pl_gm_df, shots_df)
        pl_gm_gdf = pl_gm_gdf.assign(personId=pl_id)
        pl_name = players.find_player_by_id(pl_id)["full_name"]
        pl_gm_gdf = pl_gm_gdf.assign(player=pl_name)
        pl_gdfs.append(pl_gm_gdf)

pl_gdf = pd.concat(pl_gdfs)
pl_ranks = pl_gdf.groupby("player").sum()["shot_atts"].sort_values().index.to_list()[::-1]

import plotly.express as px
import sys
sys.path.append("/Users/jphwang/PycharmProjects/projects/prettyplotly")
from prettyplotly import looks

fig = px.scatter(pl_gdf, y="filt_start", x="player", size="shot_atts",
                 color="pts_pct_x", color_continuous_scale=px.colors.sequential.Blues, template="plotly_white",
                 category_orders={"player": pl_ranks})
fig = looks.like_d3(fig)
# fig = looks.update_scatter_markers(fig)
fig.show()
