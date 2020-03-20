from statistics import median
from math import ceil, floor
from copy import deepcopy
import datetime


def trends(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    if race:
        race_replays = []
        for replay in account_replays:
            player_id = str(replay.user_match_id)
            if race == replay.players[player_id]['race'].lower():
                race_replays.append(replay)
        account_replays = race_replays

    weekly_data = {}

    if not account_replays:
        return None

    one_week = 604800
    initial_date = int(account_replays[0].played_at.timestamp())
    weekly_data[initial_date] = []
    current_week = initial_date
    for r in account_replays:
        current_date = int(r.played_at.timestamp())

        if current_week > current_date > current_week - one_week:
            weekly_data[current_week].append(r)
        else:
            while current_date < current_week - one_week:
                current_week -= one_week
                weekly_data[current_week] = []

            weekly_data[current_week] = [r]

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

        days = datetime.timedelta(
            seconds=datetime.datetime.timestamp(datetime.datetime.now()) - week
        ).days
        weeks = int(round(days / 7, 0))
        months = int(floor(weeks / 4))

        # if months == 6:
        #     trends['date'] = '6mo ago'
        if months > 0:
            if weeks - (months * 4) == 0:
                trends['date'] = f'{months}m'
            else:
                trends['date'] = f'{months} *{weeks - (months * 4)}/4*'
        else:
            trends['date'] = f'{weeks}w'

        if not replays:
            weekly_trends.append({'date': trends['date'], 'count': 0})
            if months >= 12 and weeks % 4 != 0 and days % 7 != 0:
                break
            else:
                continue

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

            if win_loss_medians['win'][stat] != 0 and stat_medians[stat] !=0:
                win_loss_difference['win'][stat] = ceil(win_diff/stat_medians[stat]*100)
            else:
                win_loss_difference['win'][stat] = 0

            if win_loss_medians['loss'][stat] != 0 and stat_medians[stat] !=0:
                win_loss_difference['loss'][stat] = ceil(loss_diff/stat_medians[stat]*100)
            else:
                win_loss_difference['loss'][stat] = 0

        trends['win_diff'] = win_loss_difference['win']
        trends['loss_diff'] = win_loss_difference['loss']

        trends['count'] = len(replays)
        winrate = round((len(win_loss_values['win']['sq']) / len(replays)) * 100, 1)
        trends['winrate'] = winrate
        weekly_trends.append(trends)

        if months >= 12 and weeks % 4 != 0 and days % 7 != 0:
            break

    weekly_trends = weekly_trends[::-1]
    weekly_trend_diff = []

    def period_avg(weekly_data, week_index):
        weekly_totals = {}
        weekly_avg = {'date': weekly_data[week_index]['date']}

        for i in range(week_index, week_index + 10):
            try:
                week = weekly_data[i]
            except IndexError:
                break

            if len(week) == 2:
                continue

            if 'winrate' not in weekly_totals:
                weekly_totals['winrate'] = []
            weekly_totals['winrate'].append(week['winrate'])

            for stat_name, value in week['total_median'].items():
                if stat_name not in weekly_totals:
                    weekly_totals[stat_name] = []
                weekly_totals[stat_name].append(value)

        for stat_name, value_list in weekly_totals.items():
            weekly_avg[stat_name] = median(value_list)

        return weekly_avg

    blank_trends = []
    for i, t in enumerate(weekly_trends):
        if 'total_median' in t:
            current_weekly_avg = period_avg(weekly_trends, i)
            break
        else:
            blank_trends.append(i)

    for index in sorted(blank_trends, reverse=True):
        weekly_trends.pop(index)

    def period_trends(current_avg, week):
        current_trends = {}

        for calculated_stats, raw_stats in week.items():
            if calculated_stats not in ['count', 'date']:
                if calculated_stats == 'total_median':
                    for stat, values in raw_stats.items():
                        if values > 0:
                            if current_avg[stat] > 0:
                                diff = round(
                                    ((week['total_median'][stat] / current_avg[stat]) - 1) * 100, 1)
                                # limit difference to +-50%
                                if diff > 50:
                                    diff = 50
                                elif diff < -50:
                                    diff = -50
                            else:
                                diff = 0
                            current_trends[stat] = (week['total_median'][stat], diff)
                        else:
                            current_trends[stat] = (week['total_median'][stat], 0)

        current_trends['count'] = week['count']
        current_trends['date'] = week['date']
        if current_avg['winrate'] == 0 or week['count'] < 5:
            current_trends['winrate'] = (week['winrate'], 0)
        else:
            winrate_diff = round(((week['winrate'] / current_avg['winrate']) - 1) * 100, 1)
            # limit difference to +-50%
            if winrate_diff > 50:
                winrate_diff = 50
            elif winrate_diff < -50:
                winrate_diff = -50
            current_trends['winrate'] = (week['winrate'], winrate_diff)
        return current_trends

    print(current_weekly_avg, current_weekly_avg['date'])

    set_next = False
    week_count = 0
    for i in range(1, len(weekly_trends)):
        if len(weekly_trends[i]) == 2:
            weekly_trend_diff.append(weekly_trends[i])

            # 3 month average
            print('week modulus', (week_count + 2) % 12)
            if (week_count + 2) % 12 == 0:
                print('found 3mo', weekly_trends[i]['date'])
                set_next = True
            week_count += 1
            continue

        current_trends = period_trends(current_weekly_avg, weekly_trends[i])
        weekly_trend_diff.append(current_trends)

        # 3 month average
        print('week modulus', (week_count + 2) % 12)
        if (week_count + 2) % 12 == 0 or set_next:
            print('found 3mo', weekly_trends[i]['date'])
            current_weekly_avg = period_avg(weekly_trends, i)
            week_count = 0

            if set_next:
                set_next = False
        week_count += 1

    return {'weekly': weekly_trend_diff, 'recent': weekly_trends[-1]}
