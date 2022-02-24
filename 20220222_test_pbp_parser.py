# ========== (c) JP Hwang 22/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import plotly.express as px
import dataproc
import utils
import viz

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

# NOTE: Hacked together a shot chart for now using my old scripts - data structure is quite different so the viz.py and dataproc.py scripts need a bit of work eventually to recover functionality
shots_df = df[(df["actionType"] == "2pt") | (df["actionType"] == "3pt")]
shots_df["original_x"] = shots_df["xLegacy"]
shots_df["original_y"] = shots_df["yLegacy"]
shots_df["shot_made"] = 0
shots_df = shots_df.assign(shot_zone=dataproc.get_zones(shots_df["original_x"].tolist(), shots_df["original_y"].tolist(), excl_angle=True))

shots_df = shots_df.assign(dist_bin=1.5 + (shots_df["shotDistance"]/3).apply(np.floor).astype(int) * 3)

shots_df.loc[shots_df["shotResult"] == "Made", "shot_made"] = 1

fig = viz.plot_hex_shot_chart(shots_df, teamname='NBA', period="All", stat_type='pps_abs', mode='dark', colorscale_in=px.colors.diverging.RdYlBu_r)
fig = viz.add_shotchart_note(fig, title_txt="Shot chart", title_xloc=0.065, title_yloc=0.92, size=20, textcolor="white")
fig.show()
