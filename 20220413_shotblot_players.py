# ========== (c) JP Hwang 14/4/2022  ==========

import logging
import pandas as pd
import utils
import json
from nba_api.stats.static import teams, players

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

# =========== DETERMINE REFERENCE (NBA-AVERGE) SHOT PROFILE ==========
ref_gdf = utils.calc_shot_dist_profile(shots_df, "NBA")

# =========== DETERMINE SHOT PROFILES FOR EACH TEAM ==========
gdf = utils.get_shot_dist_df(shots_df)
gdf.to_csv("temp/shot_profiles_by_dist_teams.csv")

# =========== DETERMINE SHOT PROFILES FOR PLAYERS ==========
pl_limit = 10
tm_abvs = [i["abbreviation"] for i in teams.get_teams()]
pl_gdfs = list()
pl_ranks_dict = dict()
for tm_abv in tm_abvs:
    tm_id = teams.find_team_by_abbreviation(tm_abv)["id"]
    tm_df = shots_df[shots_df.teamId == tm_id]
    pl_gdf = utils.get_pl_shot_dist_df(tm_df, shots_df)
    pl_ranks = pl_gdf.groupby("group").sum()["shot_atts"].sort_values().index.to_list()[::-1]
    pl_ranks = pl_ranks[:pl_limit]
    pl_ranks_dict[tm_abv] = pl_ranks
    pl_gdf = pl_gdf[pl_gdf["group"].isin(pl_ranks)]
    pl_gdf = pl_gdf.assign(team=tm_abv)
    pl_gdfs.append(pl_gdf)
comb_pl_gdf = pd.concat(pl_gdfs)
comb_pl_gdf.to_csv("temp/shot_profiles_by_dist_players.csv")
with open("temp/pl_shot_profiles_players.json", "w") as f:
    json.dump(pl_ranks_dict, f)  # Save ordered list of players

# =========== DETERMINE SHOT PROFILES FOR SPECIAL CASES ==========
pl_limit = 10
tm_abvs = [i["abbreviation"] for i in teams.get_teams()]
pl_gdfs = list()
pl_ranks_dict = dict()

tm_abv = "GSW"
pl_name = "Klay Thompson"
key_pl = players.find_players_by_full_name(pl_name)[0]

tm_id = teams.find_team_by_abbreviation(tm_abv)["id"]
tm_df = shots_df[(shots_df.teamId == tm_id)]
pl_games = tm_df[tm_df.personId == key_pl["id"]].GAME_ID.unique().tolist()
for pl_present in [True, False]:
    if pl_present:
        tmp_df = tm_df[tm_df.GAME_ID.isin(pl_games)]
        subset_name = f"Games with {key_pl['last_name']}"
    else:
        tmp_df = tm_df[-tm_df.GAME_ID.isin(pl_games)]
        subset_name = f"Without {key_pl['last_name']}"

    pl_gdf = utils.get_pl_shot_dist_df(tmp_df, shots_df)

    # Normalise data
    pl_gdf = pl_gdf.assign(pts_pct_x=pl_gdf["pts_pct_x"] / pl_gdf["pts_pct_x"].sum())

    pl_ranks = pl_gdf.groupby("group").sum()["shot_atts"].sort_values().index.to_list()[::-1]
    pl_ranks = pl_ranks[:pl_limit]
    pl_ranks_dict[subset_name] = pl_ranks

    pl_gdf = pl_gdf[pl_gdf["group"].isin(pl_ranks)]
    pl_gdf = pl_gdf.assign(team=subset_name)
    pl_gdfs.append(pl_gdf)
comb_pl_gdf = pd.concat(pl_gdfs)
comb_pl_gdf.to_csv(f"temp/shot_profiles_by_dist_{pl_name}_factor.csv")
with open(f"temp/pl_shot_profiles_players_{pl_name}_factor.json", "w") as f:
    json.dump(pl_ranks_dict, f)  # Save ordered list of players
