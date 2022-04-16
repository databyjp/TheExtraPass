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

pl_limit = 10
tm_abvs = [i["abbreviation"] for i in teams.get_teams()]
for tm_abv in tm_abvs:
    # tm_abv = "CHI"
    tm_id = teams.find_team_by_abbreviation(tm_abv)["id"]
    tm_df = shots_df[shots_df.teamId == tm_id]
    pl_gdf = utils.get_pl_shot_dist_df(tm_df, shots_df)
    pl_ranks = pl_gdf.groupby("group").sum()["shot_atts"].sort_values().index.to_list()[::-1]
    pl_ranks = pl_ranks[:pl_limit]
    pl_gdf = pl_gdf[pl_gdf["group"].isin(pl_ranks)]
    pl_gdf = pl_gdf.assign(team=tm_abv)
    pl_gdf.to_csv(f"temp/{tm_abv}_pl_shot_profile_by_dist.csv")
