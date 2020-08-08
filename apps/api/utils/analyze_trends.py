from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
from zephyrus.settings import TIMELINE_STORAGE, API_KEY
import time


def analyze_trends(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)
    replay_file_hashes = list(map(lambda replay: replay.file_hash, account_replays))

    def fetch_timeline(session, file_hash):
        headers = {'Content-Type': 'application/json'}
        payload = {
            'key': API_KEY,
            'alt': 'media',
        }
        # REPLACE BUCKET STORAGE
        url = f'https://storage.googleapis.com/storage/v1/b/sc2-timelines/o/{file_hash}.json.gz'
        response = session.get(url, headers=headers, params=payload)
        return response

    start = time.time()

    with FuturesSession() as session:
        cached_timelines = {}
        futures = [fetch_timeline(session, file_hash) for file_hash in replay_file_hashes]
        for future in as_completed(futures):
            timeline_response = future.result()
            # split on params, then slice hash out leaving .json.gz behind
            response_file_hash = timeline_response.url.split('?')[0][-72:-8]
            cached_timelines[response_file_hash] = timeline_response.json()['timeline']

        print(f'{len(cached_timelines)} Timelines, {len(account_replays)} Replays')

    end = time.time()
    print(f'Time elapsed fetching timelines: {end - start}')

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
                'win': [],
                'winrate': [],
                'mmr': [],
                'match_length': [],
                'apm': [],
                'spm': [],
                'sq': [],
                'unspent_resources': [],
                'collection_rate': [],
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
                        if s == 'win':
                            stat_values[s].append(1 if replay.win else 0)
                        elif s == 'winrate':
                            stat_values[s].append(round(wins / (wins + losses), 3) if wins + losses else None)
                        elif s == 'mmr':
                            stat_values[s].append(replay.match_data[s][user_player_id])
                        elif s == 'unspent_resources':
                            total_resources = replay.match_data['avg_unspent_resources']['minerals'][user_player_id] + replay.match_data['avg_unspent_resources']['gas'][user_player_id]
                            stat_values[s].append(total_resources)
                        elif s == 'collection_rate':
                            total_resources = replay.match_data['avg_resource_collection_rate']['minerals'][user_player_id] + replay.match_data['avg_resource_collection_rate']['gas'][user_player_id]
                            stat_values[s].append(total_resources)
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
                # if stat == 'mmr':
                #     filtered_values = values
                # else:
                #     indexed_values = []
                #     for index, v in enumerate(values):
                #         indexed_values.append({
                #             'index': index,
                #             'value': v,
                #         })
                #     indexed_values.sort(key=lambda x: x['value'])
                #     slice_index_offset = round(len(indexed_values) / 20) if len(indexed_values) / 20 > 1 else 1
                #     filtered_values = indexed_values[slice_index_offset:-slice_index_offset]
                #     filtered_values.sort(key=lambda x: x['index'])
                #     filtered_values = list(map(lambda x: x['value'], filtered_values))

                filtered_values = values
                trends[stat] = {'values': filtered_values[::-1]}
            season_trends[season].update(trends)
        matchup_trends[matchup] = {'seasons': season_trends}

    # if at least one trends exist, return them otherwise None
    for trends in matchup_trends.values():
        if trends:
            return matchup_trends

    return None
