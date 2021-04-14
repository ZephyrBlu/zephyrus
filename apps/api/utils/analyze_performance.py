import math
from statistics import median
import numpy as np


def analyze_performance(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    prev_season_start = 1611644400
    current_season_start = 1617692400

    matchups = ['all', 'protoss', 'zerg', 'terran']
    matchup_trends = {
        'all': None,
        'protoss': None,
        'zerg': None,
        'terran': None,
    }

    for matchup in matchups:
        replays = {
            'previous': [],
            'current': [],
        }

        if race:
            for replay in account_replays:
                player_id = str(replay.user_match_id)
                opp_id = '1' if replay.user_match_id == 2 else '2'
                if (
                    race == replay.players[player_id]['race'].lower()
                    and (matchup == 'all' or matchup == replay.players[opp_id]['race'].lower())
                ):
                    # if prev_season_start <= replay.played_at.timestamp() < current_season_start:
                    #     replays['previous'].append(replay)
                    # elif replay.played_at.timestamp() >= current_season_start:
                    #     replays['current'].append(replay)
                    replays['previous'].append(replay)
                    replays['current'].append(replay)

        def is_ladder_replay(replay):
            is_not_ai = len(list(filter(lambda x: 'A.I.' not in x, list(map(lambda x: x['name'], replay.players.values()))))) == 2
            has_mmr = bool(list(filter(lambda x: x, replay.match_data['mmr'].values())))
            return is_not_ai and has_mmr

        replays['previous'] = list(filter(is_ladder_replay, replays['previous']))
        replays['current'] = list(filter(is_ladder_replay, replays['current']))

        if not replays['previous'] and not replays['current']:
            continue

        season_trends = {
            'previous': {'count': len(replays['previous'])},
            'current': {'count': len(replays['current'])},
        }
        for season, season_replays in replays.items():
            if not season_replays:
                season_trends[season] = None
                continue

            stat_values = {
                'winrate': None,
                'mmr': [],
                'match_length': [],
                'apm': [],
                'spm': [],
                'sq': [],
                'workers_produced': [],
                'workers_lost': [],
                'workers_killed': [],
            }

            wins = 0
            losses = 0
            for replay in season_replays:
                for player_id, info in replay.players.items():
                    if info['profile_id'] in battlenet_id_list:
                        user_player_id = player_id

                if replay.win:
                    wins += 1
                else:
                    losses += 1

                auto_leave = False
                if replay.match_length < 60:
                    auto_leave = True

                for s in stat_values.keys():
                    if s in stat_values and s != 'winrate':
                        if s == 'mmr':
                            mmr = replay.match_data[s][user_player_id]
                            if mmr < 0:
                                continue
                            stat_values[s].append(mmr)

                        elif not auto_leave:
                            if s == 'workers_killed_lost_diff':
                                value = replay.match_data['workers_killed'][user_player_id] - replay.match_data['workers_lost'][user_player_id]
                                stat_values[s].append({
                                    'win': replay.win,
                                    'value': value,
                                })
                            else:
                                if s == 'match_length':
                                    value = replay.match_length
                                else:
                                    value = replay.match_data[s][user_player_id]

                                stat_values[s].append({
                                    'win': replay.win,
                                    'value': value,
                                })

            stat_values['winrate'] = wins / (wins + losses) if wins + losses else None

            trends = {}
            for stat, values in stat_values.items():
                if not values:
                    season_trends[season] = None
                    break

                if stat == 'winrate':
                    if values is not None:
                        trends[stat] = round(values * 100, 1)
                    continue
                if stat == 'mmr':
                    trends[stat] = {
                        'end': season_replays[0].match_data['mmr'][user_player_id],
                        'avg': round(median(values), 0),
                        'values': list(map(lambda x: {'value': x}, values))[::-1],
                    }
                else:
                    # slice_index_offset = round(len(values) / 20) if len(values) / 20 > 1 else 1
                    # filtered_values = sorted(values, key=lambda x: x['value'])[slice_index_offset:-slice_index_offset]
                    # raw_hist = histogram(list(map(lambda x: x['value'], filtered_values)), bins=10)
                    # stat_counts = map(lambda x: x / len(filtered_values) if x != 0 else 0, raw_hist[0])
                    # raw_stat_edges = raw_hist[1]

                    percentile_values = list([i * 10 for i in range(0, 11)])
                    filtered_values = list(map(lambda x: x['value'], values))
                    percentiles = np.percentile(filtered_values, percentile_values)
                    counts, bins = np.histogram(filtered_values, bins=percentiles)
                    hist = list(zip(list(counts), list(bins)))

                    def to_minutes(val):
                        mins = math.floor(val / 60)
                        secs = val - (math.floor(val / 60) * 60)
                        if secs < 10:
                            secs = f'0{secs}'
                        return f'{mins}:{secs}'

                    win_values = list(map(lambda x: x['value'], list(filter(lambda x: x['win'], values))))
                    win_percentiles = np.percentile(win_values, percentile_values)
                    win_counts, win_bins = np.histogram(win_values, bins=win_percentiles)
                    win_hist = list(zip(list(win_counts), list(win_bins)))

                    loss_values = list(map(lambda x: x['value'], list(filter(lambda x: not x['win'], values))))
                    loss_percentiles = np.percentile(loss_values, percentile_values)
                    loss_counts, loss_bins = np.histogram(loss_values, bins=loss_percentiles)
                    loss_hist = list(zip(list(loss_counts), list(loss_bins)))

                    def hist_to_data(hist, hist_type):
                        print(stat, hist)
                        # if hist_type == 'win':
                        #     return list(map(lambda x: {'win': int(x[0]), 'percentile': int(x[2])}, hist))
                        # elif hist_type == 'loss':
                        #     return list(map(lambda x: {'loss': int(x[0]), 'percentile': int(x[2])}, hist))
                        if len(hist[0]) == 2:
                            return list(map(lambda x: {'series': hist_type, 'value': int(x[0]), 'percentile': float(x[1])}, hist))
                        return list(map(lambda x: {'series': hist_type, 'win': int(x[0]), 'loss': int(x[1]), 'percentile': float(x[2])}, hist))

                    if stat == 'match_length':
                        stat_avg = to_minutes(round(median(list(map(lambda x: x['value'], values))), 0))
                    else:
                        stat_avg = round(median(list(map(lambda x: x['value'], values))), 0)
                    trends[stat] = {
                        'avg': stat_avg,
                        'values': {
                            'all': hist_to_data(hist, 'all'),
                            'win': hist_to_data(win_hist, 'win'),
                            'loss': hist_to_data(loss_hist, 'loss'),
                        },
                    }
            if season_trends[season]:
                season_trends[season].update(trends)
        matchup_trends[matchup] = {'seasons': season_trends}

    # if at least one trends exist, return them otherwise None
    for trends in matchup_trends.values():
        if trends:
            return matchup_trends

    return None
