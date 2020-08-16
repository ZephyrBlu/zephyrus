from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
from zephyrus.settings import TIMELINE_STORAGE, MAX_TRENDS_REPLAYS, API_KEY
import time


def analyze_trends(account_replays, battlenet_id_list, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    # current_season_start = 1591747200

    replays = []
    replay_file_hashes = []

    def is_ladder_replay(replay):
        is_not_ai = len(list(filter(lambda x: 'A.I.' not in x, list(map(lambda x: x['name'], replay.players.values()))))) == 2
        has_mmr = bool(list(filter(lambda x: x, replay.match_data['mmr'].values())))
        return is_not_ai and has_mmr

    if race:
        for replay in account_replays:
            player_id = str(replay.user_match_id)
            opp_id = '1' if replay.user_match_id == 2 else '2'
            if (
                # replay.played_at.timestamp() >= current_season_start
                replay.match_length >= 60
                and race == replay.players[player_id]['race'].lower()
                and is_ladder_replay(replay)
            ):
                replays.append(replay)
                replay_file_hashes.append(replay.file_hash)

                if len(replays) >= MAX_TRENDS_REPLAYS:
                    break

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

    # 2 base, 16 patches (32 workers) + 2 geysers (6 workers) = (660 + 228) * 2 = 1776
    # 3 base, 24 patches (48 workers) + 3 geysers (18 workers) = (660 + 228) * 3 = 2664
    # 3 base + 4 workers, 26 patches (52 workers) + 3 geysers (18 workers) = 2664 + (4 * 75) = 2964
    # Source: https://liquipedia.net/starcraft2/Mining_Minerals
    def check_match_stage(max_values):
        if max_values['player'] >= 2964 and max_values['opp'] >= 2964:
            return 'late'
        elif max_values['player'] >= 1776 and max_values['opp'] >= 1776:
            return 'mid'
        else:
            return 'early'

    replay_values = []
    match_values = {
        'workers_active': {},
        'workers_killed': {},
        'workers_lost': {},
        'total_army_value': {},
        'total_resources_lost': {},
        'total_unspent_resources': {},
        'total_collection_rate': {},
    }

    for replay in replays:
        for player_id, info in replay.players.items():
            if info['profile_id'] in battlenet_id_list:
                user_player_id = player_id
                opp_id = '1' if player_id == '2' else '2'

        max_collection_rate = {
            'player': 0,
            'opp': 0,
        }
        replay_timeline = cached_timelines[replay.file_hash]
        for game_state in replay_timeline:
            player_game_state = game_state[user_player_id]
            opp_game_state = game_state[opp_id]
            player_collection_rate = player_game_state['resource_collection_rate']['minerals'] + player_game_state['resource_collection_rate']['gas']
            opp_collection_rate = opp_game_state['resource_collection_rate']['minerals'] + opp_game_state['resource_collection_rate']['gas']

            if player_collection_rate > max_collection_rate['player']:
                max_collection_rate['player'] = player_collection_rate

            if opp_collection_rate > max_collection_rate['opp']:
                max_collection_rate['opp'] = opp_collection_rate

        replay_value = {
            'win': replay.win,
            'matchup': replay.players[opp_id]['race'].lower(),
            'stage': check_match_stage(max_collection_rate),
        }
        replay_values.append(replay_value)

        for game_state in replay_timeline:
            player_game_state = game_state[user_player_id]
            opp_game_state = game_state[opp_id]
            for stat in match_values.keys():
                if stat == 'total_unspent_resources':
                    player_unspent_resources = player_game_state['unspent_resources']['minerals'] + player_game_state['unspent_resources']['gas']
                    # player_collection_rate = player_game_state['resource_collection_rate']['minerals'] + player_game_state['resource_collection_rate']['gas']
                    stat_value = player_unspent_resources
                elif stat == 'total_collection_rate':
                    player_value = player_game_state['resource_collection_rate']['minerals'] + player_game_state['resource_collection_rate']['gas']
                    opp_value = opp_game_state['resource_collection_rate']['minerals'] + opp_game_state['resource_collection_rate']['gas']
                    stat_value = player_value - opp_value
                elif stat == 'total_army_value':
                    player_value = player_game_state['total_army_value']
                    opp_value = opp_game_state['total_army_value']
                    stat_value = player_value - opp_value
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

                rounded_gameloop = int(round(round(player_game_state['gameloop'] / 22.4, 0) * 22.4, 0))
                if rounded_gameloop not in match_values[stat]:
                    match_values[stat][rounded_gameloop] = []
                match_values[stat][rounded_gameloop].append({
                    'value': stat_value,
                    'win': replay.win,
                    'matchup': replay.players[opp_id]['race'].lower(),
                    'stage': check_match_stage(max_collection_rate),
                    'max_rate': max_collection_rate,
                })

    # if at least one trends exist, return them otherwise None
    for values in match_values.values():
        if values:
            return {
                'replays': replay_values,
                'trends': match_values,
            }
    return None
