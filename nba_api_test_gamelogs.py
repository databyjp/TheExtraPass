# ========== (c) JP Hwang 2/2/2022  ==========
# Created with help from https://github.com/swar/nba_api/issues/150

import pandas as pd
import utils
dl_dir = utils.dl_dir

desired_width = 320
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', desired_width)

# Get player IDs
from nba_api.stats.endpoints import commonallplayers
for season in range(2015, 2022):
    season_suffix = f'{season}-{str(season+1)[-2:]}'
    common_all_players = commonallplayers.CommonAllPlayers(league_id='00', season=season_suffix)
    df_cap = common_all_players.common_all_players.get_data_frame()
    df_cap.drop_duplicates().sort_values(by=['PERSON_ID'])
    df_cap = df_cap[df_cap.TEAM_ID != 0]
    print(f'Saving player list for {season_suffix} with {len(df_cap)} players')
    df_cap.to_csv(f'{dl_dir}/{utils.file_prefixes["pl_list"]}_{season_suffix}.csv', index=False)


# Start to grab players
import os
from nba_api.stats.endpoints import playergamelog

counter = 0
counter_limit = 5

pl_lists = [f for f in os.listdir(dl_dir) if utils.file_prefixes["pl_list"] in f]
for fname in pl_lists:
    fpath = os.path.join(dl_dir, fname)
    season_suffix = fname.split('.')[0][-7:]
    tdf = pd.read_csv(fpath)
    for pid in tdf['PERSON_ID'].values.tolist():
        df_gl = playergamelog.PlayerGameLog(season=season_suffix, player_id=pid).player_game_log.get_data_frame()

        df_gl.to_csv(f'{dl_dir}/game_logs/{utils.file_prefixes["pl_gamelog"]}_{pid}_{season_suffix}.csv', index=False)
        counter += 1
        if counter > counter_limit:
            break
    if counter > counter_limit:
        break
