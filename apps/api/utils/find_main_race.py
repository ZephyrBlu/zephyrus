from apps.user_profile.models import Replay


def find_main_race(user):
    account_replays = Replay.objects.filter(user_account_id=user.email).exclude(battlenet_account_id__isnull=True)
    race_count = {'protoss': 0, 'terran': 0, 'zerg': 0}

    for replay in account_replays:
        user_race = replay.players[str(replay.user_match_id)]['race']
        race_count[user_race.lower()] += 1
    counts = list(race_count.values())
    races = list(race_count.keys())
    max_count_index = counts.index(max(counts))
    return races[max_count_index]
