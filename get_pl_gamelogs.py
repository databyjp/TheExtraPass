# ========== (c) JP Hwang 2/2/2022  ==========

import logging
import pandas as pd
import utils
from datetime import datetime
import time

dl_dir = utils.dl_dir

logger = logging.getLogger(__name__)

desired_width = 320
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', desired_width)


# TODO - add proxy

def main():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    log_fname = datetime.now().strftime('dl_log_%Y_%m_%d_%H_%M.log')
    fh = logging.FileHandler(f'logs/{log_fname}')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # # Get player lists
    # from nba_api.stats.endpoints import commonallplayers
    # for season in range(2015, 2022):
    #     season_suffix = f'{season}-{str(season+1)[-2:]}'
    #     common_all_players = commonallplayers.CommonAllPlayers(league_id='00', season=season_suffix)
    #     df_cap = common_all_players.common_all_players.get_data_frame()
    #     df_cap.drop_duplicates().sort_values(by=['PERSON_ID'])
    #     df_cap = df_cap[df_cap.TEAM_ID != 0]
    #     logger.info(f'Saving player list for {season_suffix} with {len(df_cap)} players')
    #     df_cap.to_csv(f'{dl_dir}/{utils.file_prefixes["pl_list"]}_{season_suffix}.csv', index=False)

    # Start to grab players
    import os
    from nba_api.stats.endpoints import playergamelog

    counter = 0
    # counter_limit = 2
    counter_limit = 10**10  # Use 10**10 for no limit

    pl_lists = [f for f in os.listdir(dl_dir) if utils.file_prefixes["pl_list"] in f]
    pl_lists.sort()
    # TODO - check for game logs for completed seasons existing & skip if they exist
    # TODO - add flag for which seasons
    for fname in pl_lists[::-1]:  # Start from latest season
        counter = 0  # Reset limiter for inner loop only
        fpath = os.path.join(dl_dir, fname)
        season_suffix = fname.split('.')[0][-7:]
        tdf = pd.read_csv(fpath)
        for i, row in tdf.iterrows():
            pid = row["PERSON_ID"]
            df_gl = playergamelog.PlayerGameLog(season=season_suffix, player_id=pid).player_game_log.get_data_frame()
            if len(df_gl) == 0:
                logger.warning(f'No games fetched for {row["DISPLAY_FIRST_LAST"]} in {season_suffix}!!')
            else:
                logger.info(f'Saving game log for {row["DISPLAY_FIRST_LAST"]} in {season_suffix} with {len(df_gl)} games')
                df_gl.to_csv(f'{dl_dir}/game_logs/{utils.file_prefixes["pl_gamelog"]}_{season_suffix}_{pid}.csv', index=False)
            counter += 1
            if counter > counter_limit:  # Limit for inner loop only; copy to limit overall
                break


if __name__ == '__main__':
    main()
