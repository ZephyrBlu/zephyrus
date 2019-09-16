from statistics import median
from math import ceil
from copy import deepcopy
import datetime


def main(account_replays, battlenet_id_list):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at)
    weekly_data = {}

    one_week = 604800
    initial_date = int(account_replays[0].played_at.timestamp())
    weekly_data[initial_date] = []
    current_week = initial_date
    for r in account_replays:
        current_date = int(r.played_at.timestamp())

        if current_week <= current_date <= current_week + one_week:
            weekly_data[current_week].append(r)
        else:
            current_week += one_week

            weekly_data[current_week] = [r]

    # for k, v in weekly_data.items():
    #     print(k, len(v))

    weekly_trends = []
    for week, replays in weekly_data.items():
        trends = {
            'total_median': {},
            'total_MAD': {},
            'win_median': {},
            'loss_median': {},
            'win_MAD': {},
            'loss_MAD': {},
            'win_diff': {},
            'loss_diff': {}
        }

        stat_values = {}
        win_loss_values = {'win': {}, 'loss': {}}
        for replay in replays:
            for player_id, info in replay.players.items():
                if info['profile_id'] in battlenet_id_list:
                    user_player_id = player_id

            no_stat_list = ['mmr', 'mmr_diff']
            stats = {}
            for stat, values in replay.match_data.items():
                if stat not in no_stat_list:
                    stats[stat] = values

            for stat, values in stats.items():
                if stat not in stat_values:
                    if 'minerals' in values:
                        stat_values[f'{stat}_minerals'] = []
                        stat_values[f'{stat}_gas'] = []
                        win_loss_values['win'][f'{stat}_minerals'] = []
                        win_loss_values['win'][f'{stat}_gas'] = []
                        win_loss_values['loss'][f'{stat}_minerals'] = []
                        win_loss_values['loss'][f'{stat}_gas'] = []
                    else:
                        stat_values[stat] = []
                        win_loss_values['win'][stat] = []
                        win_loss_values['loss'][stat] = []

                if 'minerals' in values:
                    stat_values[f'{stat}_minerals'].append(values['minerals'][user_player_id])
                    stat_values[f'{stat}_gas'].append(values['gas'][user_player_id])

                    if replay.win:
                        win_loss_values['win'][f'{stat}_minerals'].append(values['minerals'][user_player_id])
                        win_loss_values['win'][f'{stat}_gas'].append(values['gas'][user_player_id])
                    elif not replay.win:
                        win_loss_values['loss'][f'{stat}_minerals'].append(values['minerals'][user_player_id])
                        win_loss_values['loss'][f'{stat}_gas'].append(values['gas'][user_player_id])
                else:
                    stat_values[stat].append(values[user_player_id])

                    if replay.win:
                        win_loss_values['win'][stat].append(values[user_player_id])
                    elif not replay.win:
                        win_loss_values['loss'][stat].append(values[user_player_id])

        stat_medians = {}
        stat_MAD = {}
        for stat, values in stat_values.items():
            if values:
                if 'pac' in stat:
                    stat_medians[stat] = round(median(values), 2)
                else:
                    stat_medians[stat] = ceil(median(values))
            else:
                stat_medians[stat] = 0

            median_diff = []
            for v in values:
                diff = abs(stat_medians[stat] - v)
                median_diff.append(diff)

            if stat_medians[stat] > 0:
                if 'pac' in stat:
                    stat_MAD[stat] = round(median(median_diff), 2)
                else:
                    stat_MAD[stat] = ceil(median(median_diff))
            else:
                stat_MAD[stat] = 0

        trends['total_median'] = stat_medians
        trends['total_MAD'] = stat_MAD

        # for stat, values in stat_medians.items():
        #     print(stat, values)

        win_loss_medians = {'win': {}, 'loss': {}}
        win_loss_MAD = {'win': {}, 'loss': {}}
        for result, info in win_loss_values.items():
            for stat, values in info.items():
                if values:
                    if 'pac' in stat:
                        win_loss_medians[result][stat] = round(median(values), 2)
                    else:
                        win_loss_medians[result][stat] = ceil(median(values))
                else:
                    win_loss_medians[result][stat] = 0

                median_diff = []
                for v in values:
                    diff = abs(win_loss_medians[result][stat] - v)
                    median_diff.append(diff)

                if win_loss_medians[result][stat] > 0:
                    if 'pac' in stat:
                        win_loss_MAD[result][stat] = round(median(median_diff), 2)
                    else:
                        win_loss_MAD[result][stat] = ceil(median(median_diff))
                else:
                    win_loss_MAD[result][stat] = 0

        trends['win_median'] = win_loss_medians['win']
        trends['win_MAD'] = win_loss_MAD['win']
        trends['loss_median'] = win_loss_medians['loss']
        trends['loss_MAD'] = win_loss_MAD['loss']

        win_loss_difference = deepcopy(win_loss_medians)
        for stat, values in stat_medians.items():
            win_diff = win_loss_medians['win'][stat] - values
            loss_diff = win_loss_medians['loss'][stat] - values

            if win_loss_medians['win'][stat] != 0:
                win_loss_difference['win'][stat] = ceil(win_diff/stat_medians[stat]*100)
            else:
                win_loss_difference['win'][stat] = 0

            if win_loss_medians['loss'][stat] != 0:
                win_loss_difference['loss'][stat] = ceil(loss_diff/stat_medians[stat]*100)
            else:
                win_loss_difference['loss'][stat] = 0

        trends['win_diff'] = win_loss_difference['win']
        trends['loss_diff'] = win_loss_difference['loss']
        trends['date'] = datetime.datetime.fromtimestamp(week).strftime('%Y-%m-%d')
        trends['count'] = len(replays)
        winrate = round((len(win_loss_values['win']['sq']) / len(replays)) * 100, 1)
        trends['winrate'] = winrate
        weekly_trends.append(trends)

    weekly_trend_diff = []
    for i in range(1, len(weekly_trends)):
        week = weekly_trends[i]
        prev_week = weekly_trends[i-1]
        current_trends = {}

        for calculated_stats, raw_stats in week.items():
            if calculated_stats not in ['count', 'date']:
                if calculated_stats == 'total_median':
                    for stat, values in raw_stats.items():
                            if values > 0 and week['count'] >= 5:
                                diff = round(((week['total_median'][stat] / prev_week['total_median'][stat]) - 1) * 100, 1)
                                if diff > 50:
                                    current_trends[stat] = (week['total_median'][stat], 50)
                                elif diff < -50:
                                    current_trends[stat] = (week['total_median'][stat], -50)
                                else:
                                    current_trends[stat] = (week['total_median'][stat], diff)
                            else:
                                current_trends[stat] = (week['total_median'][stat], 0)

        current_trends['count'] = week['count']
        current_trends['date'] = week['date']
        if prev_week['winrate'] == 0 or week['count'] < 5:
            current_trends['winrate'] = (week['winrate'], 0)
        else:
            winrate_diff = round(((week['winrate'] / prev_week['winrate']) - 1) * 100, 1)
            if winrate_diff > 50:
                current_trends['winrate'] = (week['winrate'], 50)
            elif winrate_diff < -50:
                current_trends['winrate'] = (week['winrate'], -50)
            else:
                current_trends['winrate'] = (week['winrate'], winrate_diff)
        weekly_trend_diff.append(current_trends)

    return {'weekly': weekly_trend_diff, 'recent': weekly_trends[-1]}
