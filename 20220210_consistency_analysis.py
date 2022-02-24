# ========== (c) JP Hwang 10/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import plotly.express as px
import utils

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

# df_list = list()
# pldf_list = list()
# for yr in range(2015, 2022):
#     yr_suffix = utils.year_to_season_suffix(yr)
#     t_df = pd.read_csv(f"dl_data/pl_gamelogs_{yr_suffix}.csv")
#     t_df = t_df.assign(season=yr_suffix)
#     t_df = t_df.assign(eFG_PCT=((t_df["FGM"] * 2) + (t_df["FG3M"] * 3)) / ((t_df["FGA"] * 2) + (t_df["FG3A"] * 3)))
#     df_list.append(t_df)
#     t_pldf = pd.read_csv(f"dl_data/common_all_players_{yr_suffix}.csv")
#     pldf_list.append(t_pldf)
# df = pd.concat(df_list)
# pldf = pd.concat(pldf_list)
# pldf.drop_duplicates(inplace=True)

df = utils.load_pl_gamelogs()
pldf = utils.load_pl_list()

# What about MPG
pdf = df.groupby(["Player_ID", "season"]).agg({
    "Game_ID": "count", "MIN": ["sum", "mean"], "PTS": ["mean", "std"], 
    "eFG_PCT": ["mean", "std"], "FGA": "sum", "FG3A": ["sum", "mean"],
    "FGM": "sum", "FG3M": ["sum", "mean"],
}).reset_index()
pdf.columns = ["_".join(i).strip("_") for i in pdf.columns.to_flat_index()]
pdf = pdf.assign(mpg=pdf["MIN_sum"] / pdf["Game_ID_count"])
pdf = pdf.assign(fg3a_portion=pdf["FG3A_sum"] / pdf["FGA_sum"])
pdf = pdf.assign(eFG_PCT_tot=((pdf["FGM_sum"] * 2) + (pdf["FG3M_sum"] * 3)) / ((pdf["FGA_sum"] * 2) + (pdf["FG3A_sum"] * 3)))

# Not super helpful - let's add player names

pdf = pd.merge(
    pdf,
    pldf[["PERSON_ID", "DISPLAY_FIRST_LAST"]],
    left_on="Player_ID",
    right_on="PERSON_ID",
    how="left",
)
# pdf = pdf[pdf["Game_ID_count"] > (0.5 * pdf["Game_ID_count"].max())]  # Probably not needed for now

pdf = pdf[(pdf["MIN_mean"] > 30) & (pdf["Game_ID_count"] > 50) & (pdf["PTS_mean"] > 20)]
fig = px.scatter(pdf, x="PTS_mean", y="PTS_std", color="fg3a_portion",
                 hover_data=["DISPLAY_FIRST_LAST", "season"],
                 size="mpg")
fig.show()

fig = px.scatter(pdf, x="PTS_mean", y="eFG_PCT_std", color="fg3a_portion",
                 hover_data=["DISPLAY_FIRST_LAST", "season"],
                 size="mpg")
fig.show()

pdf = pdf.assign(norm_PTS_std=pdf["PTS_std"]/pdf["PTS_mean"])
pdf = pdf.assign(norm_eFG_std=pdf["eFG_PCT_std"]/pdf["eFG_PCT_mean"])
fig = px.scatter(pdf, x="eFG_PCT_tot", y="PTS_mean",
                 color="PTS_mean",
                 hover_data=["DISPLAY_FIRST_LAST", "season"],
                 size="FG3A_mean")
fig.show()
