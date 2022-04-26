# ========== (c) JP Hwang 25/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import utils
from nba_api.stats.static import players
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

import utils
from nba_api.stats.static import players
from nba_api.stats.static import teams

df = utils.load_pbp_jsons()
df = utils.add_pbp_oncourt_columns(df)

team = teams.find_teams_by_city("Philadelphia")[0]
player = players.find_players_by_full_name("Rudy Gobert")[0]

tm_df = df[df["teamId"] == team["id"]]
tm_df = tm_df.assign(pl_concat=tm_df[[c for c in tm_df.keys() if "_player" in c]].astype(str).agg('_'.join, axis=1))

pl_on_df = tm_df[tm_df["pl_concat"].str.contains(str(player["id"]))]
pl_off_df = tm_df[-tm_df["pl_concat"].str.contains(str(player["id"]))]



# Preprocess data
df.scoreHome = df.scoreHome.astype(int)
df.scoreAway = df.scoreAway.astype(int)
df = df.assign(rem_time_qtr=0)
df.loc[df["period"] < 5, "rem_time_qtr"] = df[df["period"] < 5]["clock"].str[2:4].astype(int) * 60 + df[df["period"] < 5]["clock"].str[5:9].astype(float)
df.loc[df["period"] >= 5, "rem_time_qtr"] = df[df["period"] >= 5]["clock"].str[2:4].astype(int) * 60 + df[df["period"] >= 5]["clock"].str[5:9].astype(float)

## Get garbage time / low-leverage time:
garb_thresh = 25
garb_min_int = 5
garb_min_mult = 5
# Define as garb_thresh pts down or more than (garb_min_int + (minutes left * garb_min_mult))
df = df.assign(net_score=df.scoreHome-df.scoreAway)
df = df.assign(garbage_time=
               (df["net_score"].abs() > garb_thresh) |
               ((df["period"] > 3) & (garb_min_int + (df["rem_time_qtr"] / 60) * garb_min_mult < df["net_score"].abs()))
               )

## Filter
garb_df = df[df.garbage_time]


# TEMP


# ====================
# Now show this as a matrix / heatmap:
# ver1: with teams in on x-axis
# ====================
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

gdf_tot = gdf_tot.assign(rel_pts=gdf_tot.shot_freq * gdf_tot.rel_ev)
tm_ranks = gdf_tot.groupby("team").sum()["rel_pts"].sort_values().index.to_list()


fig = px.scatter(gdf_tot, x="team", y="shot_zone", size="shot_freq", color="rel_ev",
                 color_continuous_scale=px.colors.diverging.RdYlBu_r, color_continuous_midpoint=0,
                 category_orders={"team": tm_ranks})
fig.show()


fig = px.scatter(gdf_tot, x="team", y="shot_zone", size="shot_freq", color="rel_ev",
                 color_continuous_scale=px.colors.diverging.RdYlBu_r, color_continuous_midpoint=0,
                 category_orders={"team": tm_ranks})

fig.show()
# Not so great - bubble chart makes it hard to tell apart the

import re
fig = px.bar(gdf_tot, x="team", facet_row="shot_zone", y="shot_freq", color="rel_ev",
                 color_continuous_scale=px.colors.diverging.RdYlBu_r, color_continuous_midpoint=0,
                 category_orders={"team": tm_ranks})
fig = looks.like_d3(fig)
for k in fig.layout:
    if re.search('yaxis[1-9]+', k):
        fig.layout[k].update(matches=None)
fig.show()
# Okay - but hard to tell teams apart

for cat in gdf_tot["shot_zone"].unique():
    fig = px.scatter(gdf_tot[gdf_tot["shot_zone"].str.contains(cat)], x="shot_freq", y="rel_ev", color="team",
                     title=f"{cat}",
                     category_orders={"team": tm_ranks})
    fig = looks.like_d3(fig)
    fig = looks.update_scatter_markers(fig)
    fig.show()
# Good - but hard to tell teams apart still


def add_logo(fig_in, img_in, sizex, sizey, xloc, yloc, opacity=0.5):
    fig_in.add_layout_image(
        dict(
            source=img_in,
            xref="x",
            yref="y",
            xanchor="center",
            yanchor="middle",
            x=xloc,
            y=yloc,
            sizex=sizex,
            sizey=sizey,
            sizing="contain",
            layer="above",
            opacity=opacity,
        )
    )
    return fig_in

from PIL import Image


team_list = gdf_tot.team.unique()
for cat in gdf_tot["shot_zone"].unique():
    xvar = "shot_freq"
    yvar = "rel_ev"
    tmp_gdf = gdf_tot[gdf_tot["shot_zone"].str.contains(cat)]
    fig = px.scatter(tmp_gdf, x=xvar, y=yvar, color="team",
                     title=f"{cat}",
                     category_orders={"team": tm_ranks})
    fig = looks.like_d3(fig)
    fig = looks.update_scatter_markers(fig)
    xrange = tmp_gdf[xvar].max() - tmp_gdf[xvar].min()
    yrange = tmp_gdf[yvar].max() - tmp_gdf[yvar].min()
    avg_range = (xrange + yrange) / 2
    for tmp_tm in team_list:
        tmpImg = Image.open(f"logos/{tmp_tm}-2021.png")
        fig = add_logo(
            fig,
            tmpImg,
            xrange / 10,
            yrange / 10,
            xloc=tmp_gdf[tmp_gdf.team == tmp_tm][xvar].values[0],
            yloc=tmp_gdf[tmp_gdf.team == tmp_tm][yvar].values[0],
        )
    fig.show()


# ====================
# Now show this as a matrix / heatmap:
# ver2: with players (one team only) on x-axis
# ====================

# ====================
# Now show this as a matrix / heatmap:
# ver1: with teams in on x-axis
# ====================

for team in ["PHX", "GSW", "BOS", "PHI", "MIA"]:
    team_id = teams.find_team_by_abbreviation(team)["id"]
    tm_df = shots_df[shots_df.teamId == team_id]
    tm_gdf = tm_df.groupby("shot_zone").agg({"shot_made": "sum", "period": "count"})
    tm_gdf = tm_gdf.reset_index().rename({"period": "shot_atts"}, axis=1)
    gdf_list = list()

    pl_list = tm_df.personId.unique()
    pl_list = [i for i in pl_list if len(tm_df[tm_df.personId == i]) > 200]

    for pl_id in pl_list:
        pl_df = tm_df[tm_df.personId == pl_id]
        pl_gdf = pl_df.groupby("shot_zone").agg({"shot_made": "sum", "period": "count"})
        pl_gdf = pl_gdf.reset_index().rename({"period": "shot_atts"}, axis=1)
        try:
            pl_name = players.find_player_by_id(pl_id)["full_name"]
        except:
            pl_name = f"Player {pl_id}"
        pl_gdf = pl_gdf.assign(player=pl_name)
        pl_gdf = pl_gdf.assign(shot_freq=pl_gdf.shot_atts / tm_gdf.shot_atts.sum())
        pl_gdf = pl_gdf.assign(shot_acc=pl_gdf.shot_made / pl_gdf.shot_atts)
        # pl_gdf = pl_gdf.assign(rel_freq=pl_gdf.shot_freq - gdf.shot_freq)
        pl_gdf = pl_gdf.assign(rel_acc=pl_gdf.shot_acc - gdf.shot_acc)
        pl_gdf = pl_gdf.assign(rel_ev=pl_gdf.rel_acc * 2)
        pl_gdf.loc[pl_gdf["shot_zone"].str.contains("3pt"), "rel_ev"] = pl_gdf[pl_gdf["shot_zone"].str.contains("3pt")]["rel_acc"] * 3
        gdf_list.append(pl_gdf)
    gdf_tot = pd.concat(gdf_list)


    import re
    fig = px.bar(gdf_tot, x="player", facet_row="shot_zone", y="shot_freq", color="shot_freq",
                     color_continuous_scale=px.colors.diverging.RdYlBu_r, color_continuous_midpoint=0,
                 range_color=[-0.5, 0.5],
                     category_orders={"team": tm_ranks})
    fig = looks.like_d3(fig)
    # for k in fig.layout:
    #     if re.search('yaxis[1-9]+', k):
    #         fig.layout[k].update(matches=None)
    fig.show()








# Let's see if things change for garbage time
# Preprocess data
shots_df.scoreHome = shots_df.scoreHome.astype(int)
shots_df.scoreAway = shots_df.scoreAway.astype(int)
shots_df = shots_df.assign(rem_time_qtr=0)
shots_df.loc[shots_df["period"] < 5, "rem_time_qtr"] = shots_df[shots_df["period"] < 5]["clock"].str[2:4].astype(int) * 60 + shots_df[shots_df["period"] < 5]["clock"].str[5:9].astype(float)
shots_df.loc[shots_df["period"] >= 5, "rem_time_qtr"] = shots_df[shots_df["period"] >= 5]["clock"].str[2:4].astype(int) * 60 + shots_df[shots_df["period"] >= 5]["clock"].str[5:9].astype(float)

## Get garbage time / low-leverage time:
garb_thresh = 25
garb_min_int = 5
garb_min_mult = 5
# Define as garb_thresh pts down or more than (garb_min_int + (minutes left * garb_min_mult))
shots_df = shots_df.assign(net_score=shots_df.scoreHome-shots_df.scoreAway)
shots_df = shots_df.assign(garbage_time=
               (shots_df["net_score"].abs() > garb_thresh) |
               ((shots_df["period"] > 3) & (garb_min_int + (shots_df["rem_time_qtr"] / 60) * garb_min_mult < shots_df["net_score"].abs()))
               )

## Filter
garb_df = shots_df[shots_df.garbage_time]

ggdf = garb_df.groupby("shot_zone").agg({"shot_made": "sum", "period": "count"})
ggdf = ggdf.reset_index().rename({"period": "shot_atts"}, axis=1)
ggdf = ggdf.assign(team="NBA")
ggdf = ggdf.assign(shot_freq=ggdf.shot_atts / ggdf.shot_atts.sum())
ggdf = ggdf.assign(shot_acc=ggdf.shot_made / ggdf.shot_atts)
