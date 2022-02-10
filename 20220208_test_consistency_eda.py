# ========== (c) JP Hwang 8/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import plotly.express as px

import utils

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
root_logger.addHandler(sh)

desired_width = 320
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", desired_width)

# Look at histograms
yr = utils.curr_season_yr()
yr_suffix = utils.year_to_season_suffix(yr)

df = pd.read_csv(f"dl_data/pl_gamelogs_{yr_suffix}.csv")
pdf = df.groupby("Player_ID").sum()["MIN"].reset_index()

fig = px.histogram(pdf, x="MIN", width=1200, height=700,)
fig.show()

# What about MPG
pdf = df.groupby("Player_ID").agg({"Game_ID": "count", "MIN": "sum"}).reset_index()
pdf = pdf.assign(mpg=pdf["MIN"] / pdf["Game_ID"])

fig = px.histogram(pdf, x="mpg", width=1200, height=700,)
fig.show()

# Let's use a larger dataset
df_list = list()
pldf_list = list()
for yr in range(2015, 2022):
    yr_suffix = utils.year_to_season_suffix(yr)
    t_df = pd.read_csv(f"dl_data/pl_gamelogs_{yr_suffix}.csv")
    t_df = t_df.assign(season=yr_suffix)
    t_df = t_df.assign(eFG_PCT=((t_df["FGM"] * 2) + (t_df["FG3M"] * 3)) / ((t_df["FGA"] * 2) + (t_df["FG3A"] * 3)))
    df_list.append(t_df)
    t_pldf = pd.read_csv(f"dl_data/common_all_players_{yr_suffix}.csv")
    pldf_list.append(t_pldf)
df = pd.concat(df_list)
pldf = pd.concat(pldf_list)
pldf.drop_duplicates(inplace=True)

pdf = df.groupby(["Player_ID", "season"]).agg({"Game_ID": "count", "MIN": "sum"}).reset_index()
pdf = pdf.assign(mpg=pdf["MIN"] / pdf["Game_ID"])

# Histograms by season
fig = px.histogram(pdf, x="mpg", width=1200, height=700,
                   color="season", facet_col="season", facet_col_wrap=3)
fig.show()

# Histograms - data together
fig = px.histogram(pdf, x="mpg", width=1200, height=700)
fig.show()

pdf = pdf[(pdf["Game_ID"] >= 20)]
fig = px.histogram(pdf, x="mpg", width=1200, height=700)
fig.show()

"""
Based on the above, let's filter the data to only include 24+ mpg, 20+ game seasons
Now, to take a look at what to expect
"""

# What about MPG
pdf = df.groupby(["Player_ID", "season"]).agg({
    "Game_ID": "count", "MIN": ["sum", "mean"], "PTS": ["mean", "std"],
    "eFG_PCT": ["mean", "std"], "FGA": "sum", "FG3A": ["sum", "mean"],
    "FGM": "sum", "FG3M": ["sum", "mean"],
}).reset_index()
pdf.columns = ["_".join(i).strip("_") for i in pdf.columns.to_flat_index()]
pdf = pdf[(pdf["Game_ID_count"] >= 20) & (pdf["MIN_mean"] > 24)]

fig = px.scatter(pdf, x="PTS_mean", y="PTS_std", width=1200, height=700, size="FGA_sum")
fig.show()

# Oh, let's add player names
pdf = pd.merge(
    pdf,
    pldf[["PERSON_ID", "DISPLAY_FIRST_LAST"]].drop_duplicates(),
    left_on="Player_ID",
    right_on="PERSON_ID",
    how="inner",
)

fig = px.scatter(pdf, x="PTS_mean", y="PTS_std", width=1200, height=700, size="FGA_sum",
                 hover_data=["DISPLAY_FIRST_LAST", "season"])
fig.show()

# KD and Kyrie stand out, so let's take a quick look at the stats visualised:
df = pd.merge(
    df,
    pldf[["PERSON_ID", "DISPLAY_FIRST_LAST"]].drop_duplicates(),
    left_on="Player_ID",
    right_on="PERSON_ID",
    how="inner",
)

fdf = df[(
    (df["DISPLAY_FIRST_LAST"] == "Kyrie Irving") & (df["season"] == "2019-20") |
    (df["DISPLAY_FIRST_LAST"] == "Kevin Durant") & (df["season"] == "2015-16")
)]

fig = px.scatter(fdf, x="PTS", y="DISPLAY_FIRST_LAST", width=960, height=350,
                 size="FGA", color="DISPLAY_FIRST_LAST",
                 title="A picture of (IN)consistency - Kyrie '15-16 v Durant '19-20".upper(),
                 labels={"PTS": "Points", "DISPLAY_FIRST_LAST": "Player"}
                 )
fig.show()
