import math
from statistics import median
from numpy import histogram


def analyze_performance(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    prev_season_start = 1591747200
    current_season_start = 1601377200

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
                    if prev_season_start <= replay.played_at.timestamp() < current_season_start:
                        replays['previous'].append(replay)
                    elif replay.played_at.timestamp() >= current_season_start:
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
                'supply_block': [],
                'workers_produced': [],
                'workers_lost': [],
                'workers_killed': [],
                'workers_killed_lost_diff': [],
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
                    slice_index_offset = round(len(values) / 20) if len(values) / 20 > 1 else 1
                    filtered_values = sorted(values, key=lambda x: x['value'])[slice_index_offset:-slice_index_offset]
                    raw_hist = histogram(list(map(lambda x: x['value'], filtered_values)), bins=7)
                    stat_counts = raw_hist[0]
                    raw_stat_edges = raw_hist[1]
                    stat_edges = []

                    def to_minutes(val):
                        mins = math.floor(val / 60)
                        secs = val - (math.floor(val / 60) * 60)
                        if secs < 10:
                            secs = f'0{secs}'
                        return f'{mins}:{secs}'

                    for i in range(1, len(raw_stat_edges)):
                        if stat == 'match_length':
                            stat_edges.append(f'{to_minutes(int(round(raw_stat_edges[i-1], 0)))} - {to_minutes(int(round(raw_stat_edges[i], 0)) - 1)}')
                        else:
                            stat_edges.append(f'{int(round(raw_stat_edges[i-1], 0))} - {int(round(raw_stat_edges[i], 0)) - 1}')
                    win_values = list(filter(lambda x: x['win'], filtered_values))
                    win_hist = histogram(list(map(lambda x: x['value'], win_values)), bins=7, range=(raw_stat_edges[0], raw_stat_edges[-1]))
                    win_counts = win_hist[0]

                    loss_values = list(filter(lambda x: not x['win'], filtered_values))
                    loss_hist = histogram(list(map(lambda x: x['value'], loss_values)), bins=7, range=(raw_stat_edges[0], raw_stat_edges[-1]))
                    loss_counts = loss_hist[0]

                    def hist_to_data(hist):
                        if len(hist[0]) == 2:
                            return list(map(lambda x: {'value': int(x[0]), 'bin': x[1]}, hist))
                        return list(map(lambda x: {'win': int(x[0]), 'loss': int(x[1]), 'bin': x[2]}, hist))

                    if stat == 'match_length':
                        stat_avg = to_minutes(round(median(list(map(lambda x: x['value'], values))), 0))
                    else:
                        stat_avg = round(median(list(map(lambda x: x['value'], values))), 0)
                    trends[stat] = {
                        'avg': stat_avg,
                        'values': {
                            'all': hist_to_data(list(zip(stat_counts, stat_edges))),
                            'win_loss': hist_to_data(list(zip(win_counts, loss_counts, stat_edges))),
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
