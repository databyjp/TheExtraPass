# ========== (c) JP Hwang 3/4/2022  ==========

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

# LOOP THROUGH TO CALCULATE SIMILARITIES FOR EACH TEAM
tm_dists_dfs = list()
tm_ids = day_df.teamId.unique().tolist()
for tm_id in tm_ids:  # OUTER LOOP FOR EACH TEAM
    # TEAM'S OVERALL SHOT PROFILE DATA
    tm_abv = teams.find_team_name_by_id(tm_id)["abbreviation"]
    tm_gdf = gdf[gdf["group"] == tm_abv]
    tm_freq_vec = tm_gdf.rel_freq.values
    tm_pts_vec = tm_gdf.rel_pts.values

    # GET GAME-SPECIFIC SHOT PROFILE DATA FOR EACH GAME
    tm_df = day_df[day_df.teamId == tm_id]
    gm_freq_dists = list()
    gm_pts_dists = list()
    gm_ids = tm_df.GAME_ID.unique().tolist()
    for gm_id in gm_ids:  # INNER LOOP FOR EACH GAME
        logger.info(f"Calculating shot profile for {tm_abv} in game {gm_id}")
        tm_gm_df = tm_df[tm_df.GAME_ID == gm_id]
        tm_gm_gdf = utils.get_shot_dist_df(tm_gm_df, shots_df)
        tm_gm_freq_vec = tm_gm_gdf.rel_freq.values
        tm_gm_pts_vec = tm_gm_gdf.rel_pts.values

        # DISTANCE
        gm_freq_dist = cosine(tm_freq_vec, tm_gm_freq_vec)
        gm_freq_dists.append(gm_freq_dist)
        gm_pts_dist = cosine(tm_pts_vec, tm_gm_pts_vec)
        gm_pts_dists.append(gm_pts_dist)
    tm_dists_df = pd.DataFrame({"game_id": gm_ids, "freq_cos_dist": gm_freq_dists, "pts_cos_dist": gm_pts_dists, "tm_abv": tm_abv})
    tm_dists_dfs.append(tm_dists_df)
dists_df = pd.concat(tm_dists_dfs)

# IDENTIFY GAMES WITH THE MOST ATYPICAL PROFILES
dists_df.sort_values("pts_cos_dist", inplace=True)


