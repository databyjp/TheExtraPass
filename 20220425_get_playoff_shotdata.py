# ========== (c) JP Hwang 25/4/2022  ==========

import logging
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import teamgamelogs
from nba_api.stats.static import teams
import utils
import json

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

tm_abv = "MIA"
team = teams.find_team_by_abbreviation(tm_abv)
tid = team["id"]
season_suffix = "2021-22"

response = teamgamelogs.TeamGameLogs(team_id_nullable=str(tid), season_nullable=season_suffix)
content = json.loads(response.get_json())
tm_df = utils.json_to_df(content)

response = teamgamelogs.TeamGameLogs(team_id_nullable=str(tid), season_nullable=season_suffix, season_type_nullable="Playoffs")
content = json.loads(response.get_json())
tm_df = utils.json_to_df(content)
