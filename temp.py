# ========== (c) JP Hwang 2/2/2022  ==========

import logging
import pandas as pd
import numpy as np
import os
import utils

logger = logging.getLogger(__name__)

desired_width = 320
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', desired_width)


def main():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)

    ddir = 'dl_data/game_logs'
    for season_yr in range(2015, 2022):
        season_suffix = utils.season_suffix(season_yr)
        fnames = [f for f in os.listdir(ddir) if f"pl_gamelog_{season_suffix}" in f]
        dfs = list()
        for f in fnames:
            tdf = pd.read_csv(os.path.join(ddir, f))
            dfs.append(tdf)
        df = pd.concat(dfs)
        outpath = os.path.join('dl_data', f'{utils.file_prefixes["pl_gamelogs"]}_{season_suffix}.csv')
        df.to_csv(outpath, index=False)


if __name__ == '__main__':
    main()
