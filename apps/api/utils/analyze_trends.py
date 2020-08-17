import gzip
import requests
from zephyrus.settings import MAX_TRENDS_REPLAYS


def analyze_trends(account_replays, race=None):
    account_replays = list(account_replays)
    account_replays.sort(key=lambda r: r.played_at, reverse=True)

    # current_season_start = 1591747200

    replays = []
    serialized_replays = []
    replay_file_hashes = []

    def is_ladder_replay(replay):
        is_not_ai = len(list(filter(lambda x: 'A.I.' not in x, list(map(lambda x: x['name'], replay.players.values()))))) == 2
        has_mmr = bool(list(filter(lambda x: x, replay.match_data['mmr'].values())))
        return is_not_ai and has_mmr

    def serialize_replay(replay):
        user_player_id = str(replay.user_match_id)
        opp_id = '1' if replay.user_match_id == 2 else '2'

        return {
            'file_hash': replay.file_hash,
            'user_player_id': user_player_id,
            'opp_id': opp_id,
            'win': replay.win,
            'matchup': replay.players[opp_id]['race'].lower(),
        }

    if race:
        for replay in account_replays:
            player_id = str(replay.user_match_id)
            if (
                # replay.played_at.timestamp() >= current_season_start
                replay.match_length >= 60
                and race == replay.players[player_id]['race'].lower()
                and is_ladder_replay(replay)
            ):
                replays.append(replay)
                serialized_replays.append(serialize_replay(replay))
                replay_file_hashes.append(replay.file_hash)

                if len(replays) >= MAX_TRENDS_REPLAYS:
                    break

    process_timelines_url = 'https://us-central1-reflected-codex-228006.cloudfunctions.net/process-timelines-testing'
    replay_data = {
        'file_hashes': replay_file_hashes,
        'replays': serialized_replays,
    }
    processed_timelines_response = requests.post(process_timelines_url, json=replay_data)
    aggregated_timelines = gzip.decompress(processed_timelines_response.content)
    return aggregated_timelines
