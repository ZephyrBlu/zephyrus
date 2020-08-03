def analyze_trends(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    prev_season_start = 1584403200
    current_season_start = 1591747200

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
                'winrate': [],
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

                for s in stat_values.keys():
                    if s in stat_values:
                        if s == 'winrate':
                            stat_values[s].append(wins / (wins + losses) if wins + losses else None)
                        elif s == 'mmr':
                            stat_values[s].append(replay.match_data[s][user_player_id])
                        elif s == 'workers_killed_lost_diff':
                            value = replay.match_data['workers_killed'][user_player_id] - replay.match_data['workers_lost'][user_player_id]
                            stat_values[s].append(value)
                        else:
                            if s == 'match_length':
                                value = replay.match_length
                            else:
                                value = replay.match_data[s][user_player_id]
                            stat_values[s].append(value)

            trends = {}
            for stat, values in stat_values.items():
                trends[stat] = list(map(lambda x: {'value': x}, values))[::-1]

            season_trends[season].update(trends)
        matchup_trends[matchup] = {'seasons': season_trends}

    # if at least one trends exist, return them otherwise None
    for trends in matchup_trends.values():
        if trends:
            return matchup_trends

    return None
