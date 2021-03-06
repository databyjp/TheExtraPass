# ========== (c) JP Hwang 1/8/20  ==========

import logging
import pandas as pd
import numpy as np

# ===== START LOGGER =====
logger = logging.getLogger(__name__)


def load_log_df(logpath):

    log_df = pd.read_csv(logpath)

    return log_df


def load_df_from_logfile_list(logdir, logfiles_list, testmode=False):

    import os

    temp_list = list()
    if testmode:
        logfiles_list = logfiles_list[:100]

    for f in logfiles_list:
        try:
            logger.info(f'Loading & processing {f}')
            logpath = os.path.join(logdir, f)
            log_df = load_log_df(logpath)
            log_df['logfile'] = f
            temp_list.append(log_df)
        except:
            logger.error(f'Weird, error loading {f}')

    log_df = pd.concat(temp_list, axis=0, ignore_index=True)

    return log_df


def mark_df_threes(in_df):

    # Mark threes
    # 22 ft - corner 3s
    in_df.loc[:, 'is_three'] = False

    if 'simple_zone' not in in_df.columns and 'shot_zone' not in in_df.columns:
        in_df.loc[
            (
                    (in_df.original_x < -220) &
                    ((in_df.event_type == 'shot') | (in_df.event_type == 'miss'))
            )
            , 'is_three'] = True
        in_df.loc[
            (
                    (in_df.original_x > 220) &
                    ((in_df.event_type == 'shot') | (in_df.event_type == 'miss'))
            )
            , 'is_three'] = True

        # 23.75 ft - 3 pt arc
        in_df.loc[
            (
                    (in_df.shot_distance >= 23.75) &
                    ((in_df.event_type == 'shot') | (in_df.event_type == 'miss'))
            )
            , 'is_three'] = True
    else:
        for zone_col in ['simple_zone', 'shot_zone']:
            if zone_col in in_df.columns:
                for zone_txt in ['Short 3', '3s', '30+']:
                    in_df.loc[
                        (in_df[zone_col].str.contains(zone_txt))
                        , 'is_three'] = True

    return in_df


def flip_x_coords(log_df):

    log_df = log_df.assign(unflipped_x=log_df.original_x)
    log_df = log_df.assign(original_x=-log_df.original_x)

    return log_df


def filter_error_rows(log_df, filt_cols=('original_x', 'original_y', 'shot_distance')):

    logger.info(f"Filtering {len(log_df)} rows")
    log_df = log_df[(log_df["original_y"].notna()) & (log_df["original_x"].notna()) & (log_df["shot_distance"].notna())]
    logger.info(f"{len(log_df)} rows remaining after filtering NA values")

    for filt_col in filt_cols:
        logger.info(f"Processing {filt_col}")

        log_df[filt_col] = log_df[filt_col].astype(str)
        log_df = log_df[-log_df[filt_col].str.contains(r"[^0-9./-]", regex=True)]
        log_df[filt_col] = log_df[filt_col].astype(float)

        logger.info(f"{len(log_df)} rows remaining after filtering string values with {filt_col}")

    return log_df


def filter_oncourt_pl(in_df, playername, playeron=True, exclude_player=True):

    oncourt_names = (
            in_df['a1'] + in_df['a2'] + in_df['a3'] + in_df['a4'] + in_df['a5']
            + in_df['h1'] + in_df['h2'] + in_df['h3'] + in_df['h4'] + in_df['h5']
    )
    # in_df['oncourt'] = oncourt_names
    in_df = in_df.assign(oncourt=oncourt_names)

    player_filter = in_df.oncourt.str.contains(playername)
    if playeron is False:
        player_filter = -player_filter

    in_df = in_df[player_filter]

    in_df = in_df.drop(labels='oncourt', axis=1)

    if exclude_player:
        in_df = in_df[in_df['player'] != playername]

    return in_df


def get_zones(x, y, excl_angle=False):

    def append_name_by_angle(temp_angle):

        if excl_angle:
            temp_text = ''
        else:
            if temp_angle < 60 and temp_angle >= -90:
                temp_text = '_right'
            elif temp_angle < 120 and temp_angle >= 60:
                temp_text = '_middle'
            else:
                temp_text = '_left'
        return temp_text

    import math

    zones_list = list()
    for i in range(len(x)):

        temp_angle = math.atan2(y[i], x[i]) / math.pi * 180
        temp_dist = ((x[i] ** 2 + y[i] ** 2) ** 0.5) / 10

        if temp_dist > 30:
            zone = '7 - 30+ ft'
        elif (x[i] < -220 or x[i] > 220) and y[i] < 90:
            zone = '4 - Corner 3s'
            zone += append_name_by_angle(temp_angle)
        elif temp_dist > 27:
            zone = '6 - Long 3s'
            zone += append_name_by_angle(temp_angle)
        elif temp_dist > 23.75:
            zone = '5 - Short 3 (<27 ft)'
            zone += append_name_by_angle(temp_angle)
        elif temp_dist > 14:
            zone = '3 - Long 2 (14+ ft)'
            zone += append_name_by_angle(temp_angle)
        elif temp_dist > 4:
            zone = '2 - Short 2 (4-14 ft)'
            zone += append_name_by_angle(temp_angle)
        else:
            zone = '1 - Within 4 ft'

        zones_list.append(zone)

    return zones_list


def get_season_yr(log_df):

    import re
    yr_nums = re.findall("[0-9]+", log_df.iloc[0]["data_set"]) + re.findall("[0-9]+", log_df.iloc[-1]["data_set"])
    yr_nums = [yr[:-2] for yr in yr_nums]
    max_yr = int(max(yr_nums))

    return max_yr


def process_shots_df(log_df):

    import pandas as pd
    """
    :param log_df:
    :return:
    """

    # Filter out rows where shots are string values or unknown
    log_df = filter_error_rows(log_df)

    # Add 'shots_made' column - boolean for shot being made
    log_df['shot_made'] = 0
    log_df['shot_made'] = log_df.shot_made.mask(log_df.event_type == 'shot', 1)

    shots_df = log_df[(log_df.event_type == 'shot') | (log_df.event_type == 'miss')]

    if 'unflipped_x' not in shots_df.columns:
        logger.info('Flipping x_coordinates because they are reversed somehow :(')
        shots_df = flip_x_coords(shots_df)

    shots_df = shots_df.assign(shot_zone=get_zones(list(shots_df['original_x']), list(shots_df['original_y'])))
    shots_df = shots_df.assign(simple_zone=get_zones(list(shots_df['original_x']), list(shots_df['original_y']), excl_angle=True))
    shots_df = mark_df_threes(shots_df)

    # Set up total time (game time) column & score difference column
    remaining_time = [i.split(':') for i in list(shots_df['remaining_time'])]
    tot_time = list()
    for i in range(len(shots_df)):
        if shots_df.iloc[i]['period'] < 5:
            tmp_gametime = ((shots_df.iloc[i]['period'] - 1) * 12) + (11 - int(remaining_time[i][1])) + (1 - (int(remaining_time[i][2]) / 60))
        else:
            tmp_gametime = 48.0 + ((shots_df.iloc[i]['period'] - 5) * 5) + (4 - int(remaining_time[i][1])) + (1 - (int(remaining_time[i][2]) / 60))
        tot_time.append(tmp_gametime)
    shots_df['tot_time'] = tot_time
    shots_df = shots_df.assign(score_diff=abs(shots_df.home_score - shots_df.away_score))

    # Mark garbage time shots: Rule: up 13 with a minute left, increasing by one each minute
    garbage_marker = pd.Series([False] * len(shots_df))
    for i, row in shots_df.iterrows():
        if (row["period"] == 4):
            rem_mins = row["remaining_time"].split(":")[1]
            score_threshold = 13 + int(rem_mins)
            if row["score_diff"] >= score_threshold:
                garbage_marker[i] = True
    shots_df['garbage'] = garbage_marker

    return shots_df


def load_latest_logfile(logfile_dir):

    import re
    import os
    import datetime

    def get_latest_date(fname):
        date_strs = re.findall("[0-9]{2}-[0-9]{2}-[0-9]{4}", fname)
        tmp_dates = [datetime.datetime.strptime(i, "%m-%d-%Y") for i in date_strs]
        temp_date = max(tmp_dates)
        return temp_date

    # ===== Find the latest file to read
    comb_logfiles = [f for f in os.listdir(logfile_dir) if 'combined-stats.csv' in f]

    latest_date = get_latest_date(comb_logfiles[0])
    latest_file = comb_logfiles[0]

    for i in range(1, len(comb_logfiles)):
        fname = comb_logfiles[i]
        temp_date = get_latest_date(fname)
        if temp_date > latest_date:
            latest_date = temp_date
            latest_file = fname

    logger.info(f"Processing data from {latest_file} to build our DataFrame.")

    # ===== Read logfile
    logfile = os.path.join(logfile_dir, latest_file)
    loaded_df = pd.read_csv(logfile)

    return loaded_df


def build_shots_df(logs_df, outfile='procdata/shots_df.csv', sm_df=False, overwrite=True):

    # Convert full court to half court => y=89 == y=5
    # If y > 47: flip x, y = y-52
    import os
    import sys

    logger.info("Building a DataFrame of all shots")

    shots_df = process_shots_df(logs_df)
    shots_df.reset_index(inplace=True, drop=True)

    # ===== Write processed file
    if sm_df == True:
        shots_df = shots_df[[
            'date', 'period', 'away_score', 'home_score', 'remaining_time', 'elapsed', 'team', 'event_type',
            'assist', 'away', 'home', 'block', 'opponent', 'player',
            'shot_distance', 'original_x', 'original_y', 'shot_made', 'is_three', 'shot_zone', 'simple_zone'
        ]]
    shots_df = shots_df.assign(on_court=shots_df["a1"] + shots_df["a2"] + shots_df["a3"] + shots_df["a4"] + shots_df["a5"] + shots_df["h1"] + shots_df["h2"] + shots_df["h3"] + shots_df["h4"] + shots_df["h5"])

    if outfile is not None:
        if overwrite is not True:
            if os.path.exists(outfile):
                abort_bool = input(f"Output file {outfile} exists already - overwrite? 'y' for yes, otherwise no.")
                if abort_bool != "y":
                    sys.exit("Okay, exiting script.")
                else:
                    logger.info("Okay, proceeding with overwrite.")

        logger.info(f"Writing {outfile}...")

        shots_df.to_csv(outfile)

    return shots_df


def load_shots_df(shots_df_loc="procdata/shots_df.csv"):

    shots_df = pd.read_csv(shots_df_loc, index_col=0)

    return shots_df


def filter_shots_df(shots_df_in, teamname='NBA', period='All', player=None):

    avail_periods = ['All', 1, 2, 3, 4]

    if teamname == 'NBA':
        filtered_df = shots_df_in
    elif teamname in shots_df_in.team.unique():
        filtered_df = shots_df_in[shots_df_in.team == teamname]
    else:
        logger.error(f'{teamname} not in the list of teamnames! Returning input DF.')
        filtered_df = shots_df_in

    if period == 'All':
        filtered_df = filtered_df
    elif period in avail_periods:
        filtered_df = filtered_df[filtered_df.period == period]
    else:
        logger.error(f'{period} not in the list of possible periods! Returning input DF.')
        filtered_df = filtered_df

    if player is not None:
        filtered_df = filtered_df[filtered_df["player"] == player]

    return filtered_df


def get_pl_shot_counts(shots_df_in, crunchtime_mins=5):

    crunchtime_df = shots_df_in[
        (shots_df_in.tot_time > (48 - crunchtime_mins))
        & (shots_df_in.tot_time <= 48)
    ]
    pl_counts = crunchtime_df.groupby(['player', 'team']).count()['game_id'].sort_values()

    return pl_counts


def get_pl_data_dict(time_df, player, team, pl_acc_dict, pl_pps_dict, min_start, min_end, add_teamname=True):

    temp_df = time_df[time_df.player == player]
    team_temp_df = time_df[time_df.team == team]
    period = (min_start // 12) + 1

    if len(temp_df) == 0:
        shots_acc = 0
    else:
        shots_acc = sum(temp_df.shot_made) / len(temp_df)

    if len(team_temp_df) == 0:
        shots_freq = 0
    else:
        shots_freq = round(len(temp_df) / len(team_temp_df) * 100, 1)

    if add_teamname:
        player_name = player + ' [' + team + ']'
    else:
        player_name = player

    temp_dict = dict(
        player=player_name,
        pl_acc=round(pl_acc_dict[player][period] * 100, 1),  # overall accuracy
        pl_pps=round(pl_pps_dict[player][period] * 100, 1),  # overall PPS
        min_start=min_start + 1,
        min_mid=min_start + 0.5,
        min_end=min_end,
        shots_count=len(temp_df),
        shots_made=sum(temp_df.shot_made),
        shots_freq=shots_freq,
        shots_acc=round(100 * shots_acc, 1),  # acc for the sample only
        # shots_acc=shots_acc,
    )

    return temp_dict


def build_shot_dist_df(shots_df, outfile='procdata/shot_dist_df.csv', overwrite=True):

    import os
    import sys

    logger.info("Building a DataFrame of shot distributions")

    # ========== PROCESS DATA FILE ==========
    shots_df.reset_index(inplace=True, drop=True)
    shots_df = shots_df[shots_df.period <= 4]

    # Get non-garbage time minutes:  Rule: up 13 with a minute left, increasing by one each minute
    shots_df = shots_df[shots_df["garbage"] == False]

    player_counts = get_pl_shot_counts(shots_df, crunchtime_mins=5)  # Sort by crunchtime shots, not just overall

    # Get top players for the summary list
    teams_list = set()
    top_players = list()
    for (player, pl_team) in player_counts.index[::-1]:
        if pl_team not in teams_list:
            top_players.append([player, pl_team])
            teams_list.add(pl_team)
    top_players = top_players[::-1]

    summary_data_list = list()

    # Get player data
    pl_acc_dict = dict()  # accuracies
    pl_pps_dict = dict()  # points per shot

    for player in shots_df.player.unique():
        pl_q_acc_dict = dict()
        pl_q_pps_dict = dict()
        for period in shots_df.period.unique():
            pl_df = shots_df[(shots_df.player == player) & (shots_df.period == period)]
            # Are there are any shots?
            if len(pl_df) > 0:
                pl_q_acc_dict[period] = sum(pl_df.shot_made) / len(pl_df.shot_made)
                pl_q_pps_dict[period] = (
                        (3 * sum(pl_df[pl_df.is_three].shot_made) + 2 * sum(pl_df[pl_df.is_three == False].shot_made))
                        / len(pl_df.shot_made)
                )
            else:
                pl_q_acc_dict[period] = 0
                pl_q_pps_dict[period] = 0

        pl_acc_dict[player] = pl_q_acc_dict
        pl_pps_dict[player] = pl_q_pps_dict

    # Set up range (number of minutes)
    min_range = 1

    for min_start in range(0, 48, min_range):
        min_end = min_start + min_range
        time_df = shots_df[(shots_df.tot_time > min_start) & (shots_df.tot_time <= min_end)]

        for player, team in top_players:
            pl_dict = get_pl_data_dict(time_df, player, team, pl_acc_dict, pl_pps_dict, min_start, min_end)
            summary_data_list.append(pl_dict)

    summary_df = pd.DataFrame(summary_data_list)
    summary_df = summary_df.assign(group="Leaders")

    part_thresh = 1  # Minimum % of team's shots to be shown on the chart
    # For each team:
    team_dfs = list()
    for team in shots_df.team.unique():

        team_df = shots_df[shots_df.team == team]
        player_counts = team_df.groupby('player').count()['game_id'].sort_values(ascending=True)

        # Consolidate non-qualifying players to 'Others'
        others_counts = player_counts[player_counts < sum(player_counts) / 100 * part_thresh]
        for temp_name in list(others_counts.index):
            team_df.player.replace(temp_name, 'Others', inplace=True)

        player_counts = get_pl_shot_counts(team_df, crunchtime_mins=5)  # Sort by crunchtime shots, not just overall

        # Get data for 'Others' as an aggreagate
        others_df = team_df[team_df.player == 'Others']
        pl_q_acc_dict = dict()
        pl_q_pps_dict = dict()
        for period in shots_df.period.unique():
            if len(others_df) > 0:
                pl_q_acc_dict[period] = sum(others_df.shot_made) / len(others_df.shot_made)
                pl_q_pps_dict[period] = (
                        (3 * sum(others_df[others_df.is_three].shot_made) + 2 * sum(others_df[others_df.is_three == False].shot_made))
                        / len(others_df.shot_made)
                )
            else:
                pl_q_acc_dict[period] = 0
                pl_q_pps_dict[period] = 0
        pl_acc_dict['Others'] = pl_q_acc_dict
        pl_pps_dict['Others'] = pl_q_pps_dict

        team_summary_data_list = list()
        min_range = 1

        for min_start in range(0, 48, min_range):
            min_end = min_start + min_range
            time_df = team_df[(team_df.tot_time > min_start) & (team_df.tot_time <= min_end)]

            for player, team in player_counts.index:
                pl_dict = get_pl_data_dict(time_df, player, team, pl_acc_dict, pl_pps_dict, min_start, min_end, add_teamname=False)
                team_summary_data_list.append(pl_dict)

        team_summary_df = pd.DataFrame(team_summary_data_list)
        team_summary_df = team_summary_df.assign(group=team)
        team_dfs.append(team_summary_df)

        # ===== END - COMPILE PLAYER DATA =====

    shot_dist_df = pd.concat(team_dfs + [summary_df])

    if outfile is not None:
        if overwrite is not True:
            if os.path.exists(outfile):
                abort_bool = input(f"Output file {outfile} exists already - overwrite? 'y' for yes, otherwise no.")
                if abort_bool != "y":
                    sys.exit("Okay, exiting script.")
                else:
                    logger.info("Okay, proceeding with overwrite.")

        logger.info(f"Writing {outfile}...")

        shot_dist_df.to_csv(outfile)

    return shot_dist_df


def add_polar_columns(shots_df):
    # Generate shot angle & distance data
    if "original_x" in shots_df.columns:  # For BigDataBall type database
        shots_df = shots_df.assign(shot_dist_calc=((shots_df.original_x * shots_df.original_x) + ((shots_df.original_y) * (shots_df.original_y))) ** 0.5)
        shots_df = shots_df.assign(angle=(np.arctan2(shots_df.original_x, shots_df.original_y) * 180 / np.pi))
        shots_df.loc[(shots_df["angle"] == -180), "angle"] = 0  # Adjust for weird coordinate system use on point-blank shots -
    else:  # For Blackport's PBP type database
        shots_df = shots_df.assign(shot_dist_calc=((shots_df.x ** 2) + (shots_df.y ** 2)) ** 0.5)
        shots_df = shots_df.assign(angle=(np.arctan2(shots_df.x, shots_df.y) * 180 / np.pi))
        shots_df.loc[(shots_df["angle"] == 180), "angle"] = 0  # Adjust for weird coordinate system use on point-blank shots -
    return shots_df


def add_polar_bins(shots_df, rbin_size=30, large_tbins=True):
    # Group shots into buckets / bins
    # One challenge is the pesky 3-point line - between 22 and 23.75 feet, some shots are threes and some aren't
    # So let's make sure that no groups have 3s and 2s coexist.
    # The 3pt arc meets the corner 3 line at 22.13 degrees

    if large_tbins:
        tbin_size = 27
    else:
        tbin_size = 9

    shots_df = shots_df.assign(tbin=tbin_size * np.sign(shots_df.angle) * ((np.abs(shots_df.angle) + (tbin_size/2)) // tbin_size))
    shots_df = shots_df.assign(rbin=0.1 * rbin_size * (0.5 + (np.abs(shots_df.shot_dist_calc) // rbin_size)))

    if "is_three" in shots_df.columns:  # BigDataBall data
        three_filt = (shots_df.is_three == True)
    else:
        three_filt = (shots_df.value == 3)

    # For the last bins of twos
    shots_df.loc[(shots_df.shot_dist_calc >= 210) & (three_filt), "rbin"] = 22.5
    shots_df.loc[(shots_df.shot_dist_calc >= 210) & (shots_df.angle < -67.5), "rbin"] = 19.5
    shots_df.loc[(shots_df.shot_dist_calc >= 210) & (shots_df.angle > 67.5), "rbin"] = 19.5

    # For bins of threes
    shots_df.loc[three_filt, "rbin"] = 24 + 0.1 * rbin_size * (0.5 + (np.abs(shots_df[three_filt].shot_dist_calc-240) // rbin_size))

    # For corner threes:
    if large_tbins:
        shots_df.loc[((three_filt) & (shots_df.angle > 67.5)), "rbin"] = 23.5
        shots_df.loc[((three_filt) & (shots_df.angle > 67.5)), "tbin"] = 81
        shots_df.loc[((three_filt) & (shots_df.angle < -67.5)), "rbin"] = 23.5
        shots_df.loc[((three_filt) & (shots_df.angle < -67.5)), "tbin"] = -81
    else:
        for temp_t in [67.5, 76.5, 85.5, 94.5]:
            if temp_t == 67.5:
                new_rbin = 24.5  # This is an awkward bin - between corner and the full length; so show it as such
            else:
                new_rbin = 23.5  # Corner 3
            # Left corner
            shots_df.loc[((three_filt) & (shots_df.angle > -temp_t-9) & (shots_df.angle < -temp_t)), "rbin"] = new_rbin
            shots_df.loc[((three_filt) & (shots_df.angle > -temp_t-9) & (shots_df.angle < -temp_t)), "tbin"] = -temp_t-4.5

            shots_df.loc[((three_filt) & (shots_df.angle > temp_t) & (shots_df.angle < temp_t+9)), "rbin"] = new_rbin
            shots_df.loc[((three_filt) & (shots_df.angle > temp_t) & (shots_df.angle < temp_t+9)), "tbin"] = temp_t+4.5

    return shots_df


def add_polar_bins_new(shots_df):
    # Group shots into buckets / bins
    # One challenge is the pesky 3-point line - between 22 and 23.75 feet, some shots are threes and some aren't
    # So let's make sure that no groups have 3s and 2s coexist.
    # The 3pt arc meets the corner 3 line at 22.13 degrees

    tbin_size = 36
    shots_df = shots_df.assign(tbin=tbin_size * np.sign(shots_df.angle) * ((np.abs(shots_df.angle) + (tbin_size/2)) // tbin_size))
    shots_df = shots_df.assign(rbin_cut=pd.cut(shots_df["shot_dist_calc"], include_lowest=True, right=False, bins=[0, 30, 90, 267.5, 10000]))
    shots_df["rbin_raw"] = shots_df["rbin_cut"].apply(lambda x: (x.left + x.right)/2)
    shots_df["rbin_txt"] = None
    shots_df.loc[shots_df["rbin_raw"] == 15.0, "rbin_txt"] = "0-3 ft"
    shots_df.loc[shots_df["rbin_raw"] == 60.0, "rbin_txt"] = "3-9 ft"

    if "is_three" in shots_df.keys():
        three_filt = (shots_df["is_three"] == True)
    else:
        three_filt = (shots_df["value"] == 3)
    shots_df.loc[-three_filt & (shots_df["rbin_raw"] == 178.75), "rbin_txt"] = "midrange"
    shots_df.loc[three_filt & (shots_df["rbin_raw"] == 178.75), "rbin_txt"] = "regulation 3"
    shots_df.loc[three_filt & (shots_df["rbin_raw"] != 178.75), "rbin_txt"] = "long 3"
    shots_df["rbin"] = shots_df["rbin_txt"]

    return shots_df


def grp_polar_shots(shots_df_in, tbin_smoothing_bins=2, min_shots=0.0005):
    """
    :param shots_df_in:
    :param tbin_smoothing_bins: How many adjacent (anglular) bins to use for data smoothing
    :return:
    """
    if "original_x" in shots_df_in.columns:
        made_col = "shot_made"
    else:
        made_col = "made"

    grp_shots_df_in = shots_df_in.groupby(["tbin", "rbin"]).count()["period"]
    grp_makes_df = shots_df_in.groupby(["tbin", "rbin"]).sum()[made_col]
    grp_pcts_df = grp_makes_df / grp_shots_df_in

    if "original_x" in shots_df_in.columns:
        grp_scores_df = shots_df_in.groupby(["tbin", "rbin", "is_three"]).sum()[made_col].reset_index()
        grp_scores_df = grp_scores_df.assign(points=0)
        grp_scores_df.loc[grp_scores_df["is_three"] == True, "points"] = grp_scores_df[grp_scores_df["is_three"] == True][made_col] * 3
        grp_scores_df.loc[grp_scores_df["is_three"] == False, "points"] = grp_scores_df[grp_scores_df["is_three"] == False][made_col] * 2
    else:
        grp_scores_df = shots_df_in.groupby(["tbin", "rbin", "value"]).sum()[made_col].reset_index()
        grp_scores_df = grp_scores_df.assign(points=0)
        grp_scores_df.loc[grp_scores_df["value"] == 3, "points"] = grp_scores_df[grp_scores_df["value"] == 3][made_col] * 3
        grp_scores_df.loc[grp_scores_df["value"] == 2, "points"] = grp_scores_df[grp_scores_df["value"] == 2][made_col] * 2

    grp_scores_df = grp_scores_df.groupby(["tbin", "rbin"]).sum()["points"]
    # No averaging - at the same distance
    grp_pps_df = grp_scores_df / grp_shots_df_in * 100

    grp_shots_df_in = grp_shots_df_in.reset_index()
    grp_shots_df_in = grp_shots_df_in.rename({"period": "attempts"}, axis=1)
    grp_shots_df_in = grp_shots_df_in.assign(pct=100 * grp_pcts_df.reset_index()[0])
    grp_shots_df_in = grp_shots_df_in.assign(pps=grp_pps_df.values)

    grp_shots_df_in = grp_shots_df_in.assign(rel_pct=0)
    for i, row in grp_shots_df_in.iterrows():
        avg = grp_shots_df_in[(np.abs(grp_shots_df_in["tbin"]) == np.abs(row["tbin"])) & (grp_shots_df_in["rbin"] == row["rbin"])].pct.mean()
        grp_shots_df_in.loc[i, "rel_pct"] = row["pct"] - avg
    grp_shots_df_in = grp_shots_df_in.assign(better_side=np.sign(grp_shots_df_in.rel_pct))
    grp_shots_df_in = grp_shots_df_in.assign(freq_pct=np.round(grp_shots_df_in.attempts/len(shots_df_in) * 100, 2))
    grp_shots_df_in = grp_shots_df_in.assign(pts_pct=np.round((grp_shots_df_in.attempts * grp_shots_df_in.pps) / sum((grp_shots_df_in.attempts * grp_shots_df_in.pps)) * 100, 2))

    # Perform averaging for PPS - keep distance constant, only average by adjacent angle bins
    tbin_thresh = tbin_smoothing_bins * abs(np.sort(shots_df_in.tbin.unique())[0] - np.sort(shots_df_in.tbin.unique())[1])
    for i, row in grp_shots_df_in.iterrows():
        temp_rows = grp_shots_df_in[
            (grp_shots_df_in["rbin"] == row["rbin"]) &
            (grp_shots_df_in["tbin"] <= row["tbin"] + tbin_thresh) &
            (grp_shots_df_in["tbin"] >= row["tbin"] - tbin_thresh)
        ]
        tot_pts = np.sum(temp_rows["pps"] * temp_rows["attempts"])  # Make sure to average using totals
        tot_shots = np.sum(temp_rows["attempts"])
        mean_pps = tot_pts/tot_shots
        grp_shots_df_in.loc[row.name, "pps"] = mean_pps

    if min_shots is not None:
        for i, row in grp_shots_df_in.iterrows():
            min_samples = 0.0005
            if row["attempts"] < (grp_shots_df_in["attempts"].sum() * min_samples):
                grp_shots_df_in.loc[row.name, "attempts"] = 0

    return grp_shots_df_in


def grp_polar_shots_simp(grp_shots_df):
    rbin_grps = [[1.5], [4.5, 7.5], [10.5, 13.5, 16.5, 19.5, 22.5], [23.5, 25.5], [28.5, 31.5, 34.5, 37.5]]
    tmp_dfs = list()
    for rbin_grp in rbin_grps:
        tmp_df = grp_shots_df[grp_shots_df.rbin.isin(rbin_grp)].groupby("tbin").sum()["attempts"].reset_index()
        tmp_df["rbin"] = np.mean(rbin_grp)
        tmp_dfs.append(tmp_df)
    out_df = pd.concat(tmp_dfs)
    return out_df


# def main():
#
# if __name__ == '__main__':
#      main()