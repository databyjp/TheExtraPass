# ========== (c) JP Hwang 7/4/2022  ==========

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

# LOOP THROUGH EACH GAME TO CALCULATE SIMILARITIES FOR EACH TEAM
summ_dicts = list()
tm_gdfs = list()
tm_gm_gdf = list()
for gm_id in gm_ids:  # OUTER LOOP FOR EACH GAME
    gm_df = day_df[day_df.GAME_ID == gm_id]
    tm_ids = gm_df.teamId.unique().tolist()
    for tm_id in tm_ids:  # INNER LOOP FOR EACH TEAM PLAYING
        tm_abv = teams.find_team_name_by_id(tm_id)["abbreviation"]
        tm_gdf = gdf[gdf["group"] == tm_abv]
        tm_freq_vec = tm_gdf.rel_freq.values
        tm_pts_vec = tm_gdf.rel_pts.values

        logger.info(f"Calculating shot profile for {tm_abv} in game {gm_id}")
        tm_gm_df = gm_df[gm_df.teamId == tm_id]
        tm_gm_gdf = utils.get_shot_dist_df(tm_gm_df, shots_df)
        tm_gm_freq_vec = tm_gm_gdf.rel_freq.values
        tm_gm_pts_vec = tm_gm_gdf.rel_pts.values

        # CALCULATE DISTANCE
        gm_freq_dist = cosine(tm_freq_vec, tm_gm_freq_vec)
        gm_pts_dist = cosine(tm_pts_vec, tm_gm_pts_vec)

        summ_data = {"game_id": gm_id, "tm_abv": tm_abv,
                     "freq_cos_dist": gm_freq_dist, "pts_cos_dist": gm_pts_dist}
        summ_dicts.append(summ_data)

dists_df = pd.DataFrame(summ_dicts)

# IDENTIFY GAMES WITH THE MOST ATYPICAL PROFILES
dists_df.sort_values("pts_cos_dist", inplace=True)
key_gms = dists_df[-3:]  # 3 Games with the highest cos distances

# DOES IT MAKE SENSE?
box_df = utils.load_box_scores()  # Load box score data
for _, r in key_gms.iterrows():
    key_gm_id = r.game_id
    gamebox = box_df[box_df.GAME_ID == key_gm_id]
    print(gamebox)
    print(r.tm_abv)
