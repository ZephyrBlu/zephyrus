from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
from zephyrus.settings import TIMELINE_STORAGE, API_KEY, MAX_TRENDS_REPLAYS
import numpy as np
import math
import time


def analyze_trends(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    matchups = ['all', 'protoss', 'zerg', 'terran']
    replays = {
        'all': None,
        'protoss': None,
        'zerg': None,
        'terran': None,
    }
    replay_file_hashes = []

    def is_ladder_replay(replay):
        is_not_ai = len(list(filter(lambda x: 'A.I.' not in x, list(map(lambda x: x['name'], replay.players.values()))))) == 2
        has_mmr = bool(list(filter(lambda x: x, replay.match_data['mmr'].values())))
        return is_not_ai and has_mmr

    start = time.time()

    for matchup in matchups:
        matchup_replays = []

        if race:
            for replay in account_replays:
                player_id = str(replay.user_match_id)
                opp_id = '1' if replay.user_match_id == 2 else '2'
                if (
                    race == replay.players[player_id]['race'].lower()
                    and (matchup == 'all' or matchup == replay.players[opp_id]['race'].lower())
                    and is_ladder_replay(replay)
                ):
                    matchup_replays.append(replay)
                    replay_file_hashes.append(replay.file_hash)

                    if len(matchup_replays) >= MAX_TRENDS_REPLAYS:
                        break

        replays[matchup] = matchup_replays

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

    def parse_timeline(timeline_response, *args, **kwargs):
        # split on params, then slice hash out leaving .json.gz behind
        response_file_hash = timeline_response.url.split('?')[0][-72:-8]
        cached_timelines[response_file_hash] = timeline_response.json()['timeline']

    cached_timelines = {}
    with FuturesSession() as session:
        session.hooks['response'] = parse_timeline
        futures = [fetch_timeline(session, file_hash) for file_hash in replay_file_hashes]
        for future in as_completed(futures):
            future.result()

    match_trends = {
        'all': None,
        'protoss': None,
        'zerg': None,
        'terran': None,
    }

    timeline_start = time.time()

    for matchup, matchup_replays in replays.items():
        if not matchup_replays:
            continue

        match_values = {
            'workers_active': {},
            'workers_killed': {},
            'workers_lost': {},
            'supply_block': {},
            'total_army_value': {},
            'total_resources_lost': {},
            'total_unspent_resources': {},
            'total_collection_rate': {},
        }

        for replay in matchup_replays:
            for player_id, info in replay.players.items():
                if info['profile_id'] in battlenet_id_list:
                    user_player_id = player_id
                    opp_id = '1' if player_id == '2' else '2'

            replay_timeline = cached_timelines[replay.file_hash]
            for game_state in replay_timeline:
                player_game_state = game_state[user_player_id]
                opp_game_state = game_state[opp_id]
                for stat in match_values.keys():
                    if stat == 'total_unspent_resources':
                        player_unspent_resources = player_game_state['unspent_resources']['minerals'] + player_game_state['unspent_resources']['gas']
                        player_collection_rate = player_game_state['resource_collection_rate']['minerals'] + player_game_state['resource_collection_rate']['gas']
                        if player_collection_rate == 0:
                            stat_value = 0
                        else:
                            stat_value = round((player_unspent_resources / (player_collection_rate / 60)), 1)
                    elif stat == 'total_collection_rate':
                        player_value = player_game_state['resource_collection_rate']['minerals'] + player_game_state['resource_collection_rate']['gas']
                        opp_value = opp_game_state['resource_collection_rate']['minerals'] + opp_game_state['resource_collection_rate']['gas']
                        if opp_value == 0:
                            stat_value = 0
                        else:
                            stat_value = round(((player_value / opp_value) - 1) * 100, 1)
                            stat_value = stat_value if stat_value <= 100 else 100
                    elif stat == 'total_army_value':
                        player_value = player_game_state['total_army_value']
                        opp_value = opp_game_state['total_army_value']
                        if opp_value == 0:
                            stat_value = 0
                        else:
                            stat_value = round(((player_value / opp_value) - 1) * 100, 1)
                            stat_value = stat_value if stat_value <= 100 else 100
                    elif stat == 'total_resources_lost':
                        player_value = player_game_state['total_resources_lost']
                        opp_value = opp_game_state['total_resources_lost']
                        stat_value = player_value - opp_value
                    elif stat == 'workers_lost':
                        stat_value = player_game_state['workers_killed']
                    elif stat == 'workers_killed':
                        stat_value = opp_game_state['workers_killed']
                    else:
                        stat_value = player_game_state[stat]

                    if player_game_state['gameloop'] not in match_values[stat]:
                        match_values[stat][player_game_state['gameloop']] = []
                    match_values[stat][player_game_state['gameloop']].append({
                        'value': stat_value,
                        'win': replay.win,
                    })

        collated_values = {
            'workers_active': {},
            'workers_killed': {},
            'workers_lost': {},
            'supply_block': {},
            'total_army_value': {},
            'total_resources_lost': {},
            'total_unspent_resources': {},
            'total_collection_rate': {},
        }
        for stat, gameloop_values in match_values.items():
            for gameloop, values in gameloop_values.items():
                if math.floor(gameloop / 22.4) not in collated_values[stat]:
                    collated_values[stat][math.floor(gameloop / 22.4)] = []
                collated_values[stat][math.floor(gameloop / 22.4)].extend(values)

        matchup_stats = {
            'workers_active': [],
            'workers_killed': [],
            'workers_lost': [],
            'supply_block': [],
            'total_army_value': [],
            'total_resources_lost': [],
            'total_unspent_resources': [],
            'total_collection_rate': [],
        }
        for stat, time_values in collated_values.items():
            for time_s, values in time_values.items():
                if len(values) < 10:
                    continue

                stat_values = {
                    'all': list(map(lambda x: x['value'], values)),
                    'win': list(map(lambda x: x['value'], filter(lambda x: x['win'], values))),
                    'loss': list(map(lambda x: x['value'], filter(lambda x: not x['win'], values))),
                }

                time_stats = {
                    'time': time_s,
                    'count': len(values),
                }
                for outcome, outcome_values in stat_values.items():
                    time_median = np.median(outcome_values) if outcome_values else 0
                    time_upper_quartile = np.quantile(outcome_values, 0.75) if outcome_values else 0
                    time_lower_quartile = np.quantile(outcome_values, 0.25) if outcome_values else 0
                    time_max = np.quantile(outcome_values, 0.9) if outcome_values else 0
                    time_min = np.quantile(outcome_values, 0.1) if outcome_values else 0

                    time_stats[outcome] = {
                        'median': round(int(time_median), 0),
                        'quartile_range': [
                            round(int(time_upper_quartile), 0),
                            round(int(time_lower_quartile), 0),
                        ],
                        'total_range': [
                            round(int(time_max), 0),
                            round(int(time_min), 0),
                        ],
                    }
                matchup_stats[stat].append(time_stats)
            matchup_stats[stat].sort(key=lambda x: x['time'])
        match_trends[matchup] = matchup_stats

    timeline_end = time.time()
    end = time.time()

    print(f'Execution time for total analysis: {end - start}s')
    print(f'Execution time for timeline analysis: {timeline_end - timeline_start}s')

    # if at least one trends exist, return them otherwise None
    for trends in match_trends.values():
        if trends:
            return match_trends
    return None
