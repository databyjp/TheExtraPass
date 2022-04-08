# ========== (c) JP Hwang 3/4/2022  ==========

import logging
import pandas as pd
import utils
from scipy.spatial.distance import cosine

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

# SHOT PROFILE DATA - SINGLE GAME
gm_id = shots_df.GAME_ID.unique()[0]
gm_df = shots_df[shots_df.GAME_ID == gm_id]
gm_gdf = utils.get_shot_dist_df(gm_df, shots_df)

# TEAM'S GAME SHOT PROFILE DATA
tm_abv = gm_gdf["group"].unique()[0]
tm_gm_gdf = gm_gdf[gm_gdf["group"] == tm_abv]
tm_gm_vec = tm_gm_gdf.rel_freq.values

# TEAM'S OVERALL SHOT PROFILE DATA
tm_gdf = gdf[gdf["group"] == tm_abv]
tm_vec = tm_gdf.rel_freq.values

# CALCULATE COSINE DISTANCE
tm_dist = cosine(tm_gm_vec, tm_vec)
