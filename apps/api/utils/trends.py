from statistics import median
from math import ceil
from copy import deepcopy


def main(account_replays, battlenet_id_list):
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
    for replay in account_replays:
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
                    stat_values[stat] = {'minerals': [], 'gas': []}
                    win_loss_values['win'][stat] = {'minerals': [], 'gas': []}
                    win_loss_values['loss'][stat] = {'minerals': [], 'gas': []}
                else:
                    stat_values[stat] = []
                    win_loss_values['win'][stat] = []
                    win_loss_values['loss'][stat] = []

            if 'minerals' in values:
                stat_values[stat]['minerals'].append(values['minerals'][user_player_id])
                stat_values[stat]['gas'].append(values['gas'][user_player_id])

                if replay.win:
                    win_loss_values['win'][stat]['minerals'].append(values['minerals'][user_player_id])
                    win_loss_values['win'][stat]['gas'].append(values['gas'][user_player_id])
                elif not replay.win:
                    win_loss_values['loss'][stat]['minerals'].append(values['minerals'][user_player_id])
                    win_loss_values['loss'][stat]['gas'].append(values['gas'][user_player_id])
            else:
                stat_values[stat].append(values[user_player_id])

                if replay.win:
                    win_loss_values['win'][stat].append(values[user_player_id])
                elif not replay.win:
                    win_loss_values['loss'][stat].append(values[user_player_id])

    stat_medians = {}
    stat_MAD = {}
    for stat, values in stat_values.items():
        if 'minerals' in values:
            stat_medians[stat] = {
                'minerals': ceil(median(values['minerals'])),
                'gas': ceil(median(values['gas']))
            }

            median_diff = {'minerals': [], 'gas': []}
            for resource, info in values.items():
                for value in info:
                    diff = abs(stat_medians[stat][resource] - value)
                    median_diff[resource].append(diff)

            stat_MAD[stat] = {
                'minerals': ceil(median(median_diff['minerals'])),
                'gas': ceil(median(median_diff['gas']))
            }
        else:
            stat_medians[stat] = ceil(median(values))

            median_diff = []
            for v in values:
                diff = abs(stat_medians[stat] - v)
                median_diff.append(diff)

            if stat_medians[stat] > 0:
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
            if 'minerals' in values:
                win_loss_medians[result][stat] = {
                    'minerals': ceil(median(values['minerals'])),
                    'gas': ceil(median(values['gas']))
                }

                median_diff = {'minerals': [], 'gas': []}
                for resource, info in values.items():
                    for value in info:
                        diff = abs(win_loss_medians[result][stat][resource] - value)
                        median_diff[resource].append(diff)

                win_loss_MAD[result][stat] = {
                    'minerals': ceil(median(median_diff['minerals'])),
                    'gas': ceil(median(median_diff['gas']))
                }
            else:
                win_loss_medians[result][stat] = ceil(median(values))

                median_diff = []
                for v in values:
                    diff = abs(win_loss_medians[result][stat] - v)
                    median_diff.append(diff)

                if win_loss_medians[result][stat] > 0:
                    win_loss_MAD[result][stat] = ceil(median(median_diff))
                else:
                    win_loss_MAD[result][stat] = 0

    trends['win_median'] = win_loss_medians['win']
    trends['win_MAD'] = win_loss_MAD['win']
    trends['loss_median'] = win_loss_medians['loss']
    trends['loss_MAD'] = win_loss_MAD['loss']

    # print()
    # for result, info in win_loss_medians.items():
    #     print(result)
    #     for stat, values in info.items():
    #         mad = win_loss_MAD[result][stat]
    #         print(stat, values, f'MAD: {mad}')
    #     print()

    win_loss_difference = deepcopy(win_loss_medians)
    for stat, values in stat_medians.items():
        if type(values) is dict:
            win_diff_min = win_loss_medians['win'][stat]['minerals'] - values['minerals']
            win_diff_gas = win_loss_medians['win'][stat]['gas'] - values['gas']
            loss_diff_min = win_loss_medians['loss'][stat]['minerals'] - values['minerals']
            loss_diff_gas = win_loss_medians['loss'][stat]['gas'] - values['gas']

            win_loss_difference['win'][stat] = {
                'minerals': ceil(win_diff_min/stat_medians[stat]['minerals']*100),
                'gas': ceil(win_diff_gas/stat_medians[stat]['gas']*100)
            }
            win_loss_difference['loss'][stat] = {
                'minerals': ceil(loss_diff_min/stat_medians[stat]['minerals']*100),
                'gas': ceil(loss_diff_gas/stat_medians[stat]['gas']*100)
            }
        else:
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

    # print()
    # for result, info in win_loss_difference.items():
    #     print(result)
    #     for stat, values in info.items():
    #         print(stat, values)
    #     print()

    return trends
