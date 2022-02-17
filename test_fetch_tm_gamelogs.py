# ========== (c) JP Hwang 14/2/2022  ==========

import logging
import pandas as pd
import json
from nba_api.stats.endpoints import boxscoreadvancedv2
import utils
import os

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

gldf = utils.load_gamelogs()
pldf = utils.load_pl_list()

gldf = gldf.sort_values("gamedate_dt")
gm_ids = gldf["Game_ID"].unique()

json_dir = "dl_data/box_scores/json"

for gm_id in gm_ids[-100:][::-1]:
    dl_path = os.path.join(json_dir, gm_id + ".json")
    if os.path.exists(dl_path):
        print(f"JSON found for game {gm_id} at {dl_path}")
    else:
        try:
            print(f"Downloading data for game {gm_id}")
            try:
                response = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=gm_id)
            except:
                print(f"That didn't work - trying again with '00' prepended to game_id: {gm_id}")
                gm_id = "00" + gm_id
                response = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=gm_id)
            content = json.loads(response.get_json())
            if type(content) == json:
                with open(dl_path, 'w') as f:
                    json.dump(content, f)
                print(f"Saved data for game {gm_id} at {dl_path}")
        except:
            print(f"Error getting data for game {gm_id}")
