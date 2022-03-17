# ========== (c) JP Hwang 17/3/2022  ==========

import logging
import pandas as pd
import numpy as np
import utils
from nba_api.stats.static import teams
import plotly.express as px
import re

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

df = utils.load_pbp_jsons()
df = utils.add_pbp_oncourt_columns(df)

# Only filter for shot data
shots_df = df[(df["actionType"] == "2pt") | (df["actionType"] == "3pt")]
shots_df["shot_made"] = False
shots_df.loc[shots_df["shotResult"] == "Made", "shot_made"] = True

# Group shots by distance
# Put twos and threes into separate bins
zone_bins = {"2pt": [0, 4, 12], "3pt": [22, 23.75, 26]}

shots_df = shots_df.assign(shot_zone=np.nan)
counter = 1
for zone_bin_key, zone_bin_vals in zone_bins.items():
    for i in range(len(zone_bin_vals)):
        if i == len(zone_bin_vals)-1:
            zone_name = f"{zone_bin_vals[i]}+"
            max_dist = 94
        else:
            zone_name = f"{zone_bin_vals[i]}-{zone_bin_vals[i + 1]}"
            max_dist = zone_bin_vals[i + 1]

        shots_df.loc[
            (shots_df["actionType"] == zone_bin_key) &
            (shots_df["shotDistance"] >= zone_bin_vals[i]) &
            (shots_df["shotDistance"] < max_dist),
            "shot_zone"
        ] = f"{counter}_{zone_bin_key}_{zone_name}"
        counter += 1

gdf = shots_df.groupby("shot_zone").agg({"shot_made": "sum", "period": "count"})
gdf = gdf.reset_index().rename({"period": "shot_atts"}, axis=1)
gdf = gdf.assign(team="NBA")
gdf = gdf.assign(shot_freq=gdf.shot_atts / gdf.shot_atts.sum())
gdf = gdf.assign(shot_acc=gdf.shot_made / gdf.shot_atts)

# ========================================
# Now let's do the same for each team
# ========================================
shots_df["teamId"] = shots_df["teamId"].astype(int)
gdf_list = list()
for tm_id in shots_df.teamId.unique():
    tm_df = shots_df[shots_df.teamId == tm_id]
    tm_gdf = tm_df.groupby("shot_zone").agg({"shot_made": "sum", "period": "count"})
    tm_gdf = tm_gdf.reset_index().rename({"period": "shot_atts"}, axis=1)
    tm_name = teams.find_team_name_by_id(tm_id)["abbreviation"]
    tm_gdf = tm_gdf.assign(team=tm_name)
    tm_gdf = tm_gdf.assign(shot_freq=tm_gdf.shot_atts / tm_gdf.shot_atts.sum())
    tm_gdf = tm_gdf.assign(shot_acc=tm_gdf.shot_made / tm_gdf.shot_atts)
    tm_gdf = tm_gdf.assign(rel_freq=tm_gdf.shot_freq - gdf.shot_freq)
    tm_gdf = tm_gdf.assign(rel_acc=tm_gdf.shot_acc - gdf.shot_acc)
    tm_gdf = tm_gdf.assign(rel_ev=tm_gdf.rel_acc * 2)
    tm_gdf.loc[tm_gdf["shot_zone"].str.contains("3pt"), "rel_ev"] = tm_gdf[tm_gdf["shot_zone"].str.contains("3pt")]["rel_acc"] * 3
    gdf_list.append(tm_gdf)
gdf_tot = pd.concat(gdf_list)

tm_ranks = gdf_tot.groupby("team").sum()["rel_pts"].sort_values().index.to_list()
fig = px.bar(gdf_tot, x="team", facet_row="shot_zone", y="shot_freq", color="rel_ev",
                 color_continuous_scale=px.colors.diverging.RdYlBu_r, color_continuous_midpoint=0,
                 category_orders={"team": tm_ranks})
fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
fig.show()


def get_shot_dist(df_in, grp_label):
    # Build more granular shot bins
    filt_start = 0
    filt_width = 2
    filt_inc = 0.25
    ser_list = list()
    for i in range(1 + 120):
        for shot_type in ["2pt", "3pt"]:
            filt_df = df_in[
                (df_in["shotDistance"] >= filt_start) &
                (df_in["shotDistance"] < (filt_start + filt_width)) &
                (df_in["actionType"] == shot_type)
                ]
            if len(filt_df) > 0:
                ser = pd.Series({"shot_made": filt_df["shot_made"].sum(), "shot_atts": len(filt_df)})
                ser["group"] = grp_label
                ser["shot_type"] = shot_type
                ser["filt_start"] = filt_start
                ser["shot_freq"] = ser.shot_atts / len(df_in)
                ser["shot_acc"] = ser.shot_made / ser.shot_atts
                ser_list.append(ser)
        filt_start += filt_inc
    df_out = pd.DataFrame(ser_list)
    return df_out


gdf = get_shot_dist(shots_df, "NBA")
fig = px.scatter(gdf, x="filt_start", y="shot_freq", color="shot_type")
fig.show()

# Do the same with team data also
tm_gdfs = list()
for tm_id in shots_df.teamId.unique():
    tm_df = shots_df[shots_df.teamId == tm_id]
    tm_name = teams.find_team_name_by_id(tm_id)["abbreviation"]
    tm_gdf = get_shot_dist(tm_df, tm_name)
    # Set relative freqs
    tm_gdf = tm_gdf.merge(gdf[["shot_type", "filt_start", "shot_freq", "shot_acc"]], how="inner", on=["shot_type", "filt_start"])
    tm_gdf = tm_gdf.assign(rel_freq=tm_gdf.shot_freq_x - tm_gdf.shot_freq_y)
    tm_gdf = tm_gdf.assign(rel_acc=tm_gdf.shot_acc_x - tm_gdf.shot_acc_y)
    tm_gdfs.append(tm_gdf)

all_gdfs = pd.concat(tm_gdfs)

fig = px.scatter(all_gdfs, y="filt_start", x="group", color="rel_freq", facet_row="shot_type",
                 title="Relative shot frequencies by distance",
                 color_continuous_scale=px.colors.diverging.RdYlBu_r,
                 template="plotly_white",
                 category_orders={"group": tm_ranks})
for k in fig.layout:
    if re.search('yaxis[1-9]+', k):
        fig.layout[k].update(matches=None)
fig.show()

all_gdfs = all_gdfs.assign(rel_pts=all_gdfs.rel_acc * all_gdfs.shot_freq_x * 2)
all_gdfs.loc[all_gdfs["shot_type"] == "3pt", "rel_pts"] = all_gdfs[all_gdfs["shot_type"] == "3pt"]["rel_pts"] * 1.5

fig = px.scatter(all_gdfs, y="filt_start", x="group", color="rel_pts", facet_row="shot_type",
                 title="Where each team gains/loses points vs others",
                 color_continuous_scale=px.colors.diverging.RdYlBu_r,
                 template="plotly_white",
                 category_orders={"group": tm_ranks})
for k in fig.layout:
    if re.search('yaxis[1-9]+', k):
        fig.layout[k].update(matches=None)
fig.show()
