import math
from statistics import median
from numpy import histogram


def analyze_winrate(account_replays, race=None):
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
            'previous': None,
            'current': None,
        }
        for season, season_replays in replays.items():
            if not season_replays:
                season_trends[season] = None
                continue

            stat_values = {
                'winrate': None,
                'wins': 0,
                'losses': 0,
                'maps': {}
            }

            for replay in season_replays:
                # filter out auto-leaves
                if replay.match_length >= 60:
                    formatted_map = replay.map.split('LE')[0].strip()
                    if formatted_map not in stat_values['maps']:
                        stat_values['maps'][formatted_map] = {
                            'winrate': None,
                            'wins': 0,
                            'losses': 0,
                        }

                    if replay.win:
                        stat_values['wins'] += 1
                        stat_values['maps'][formatted_map]['wins'] += 1
                    else:
                        stat_values['losses'] += 1
                        stat_values['maps'][formatted_map]['losses'] += 1
            stat_values['winrate'] = round((stat_values['wins'] / (stat_values['wins'] + stat_values['losses']) * 100), 1) if stat_values['wins'] + stat_values['losses'] else None
            for map_name in stat_values['maps'].keys():
                stat_values['maps'][map_name]['winrate'] = round((stat_values['maps'][map_name]['wins'] / (stat_values['maps'][map_name]['wins'] + stat_values['maps'][map_name]['losses']) * 100), 1) if stat_values['maps'][map_name]['wins'] + stat_values['maps'][map_name]['losses'] else None
            season_trends[season] = stat_values
        matchup_trends[matchup] = {'seasons': season_trends}

    # if at least one trends exist, return them otherwise None
    for trends in matchup_trends.values():
        if trends:
            return matchup_trends

    return None
