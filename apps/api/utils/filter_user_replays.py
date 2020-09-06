import copy
import datetime
from math import floor
from base64 import urlsafe_b64encode
from allauth.account.models import EmailAddress
from apps.user_profile.models import Replay, BattlenetAccount
from ..models import ReplaySerializer


def filter_user_replays(request, race=None, target=None):
    user = request.user
    user_id = EmailAddress.objects.get(email=user.email)

    # check that user has a battlenet account linked
    if BattlenetAccount.objects.filter(user_account_id=user_id).exists():
        battlenet_account = BattlenetAccount.objects.filter(
            user_account_id=user_id
        ).order_by('-linked_at').first()
    # if not return 404 response
    else:
        return False

    if target == 'verify' or target == 'summary':
        replay_queryset = Replay.objects.filter(
            user_account_id=user_id,
        )
    else:
        replay_queryset = Replay.objects.filter(
            user_account_id=user_id,
            battlenet_account_id=battlenet_account
        )

    def is_ladder_replay(replay):
        is_not_ai = len(list(filter(lambda x: 'A.I.' not in x, list(map(lambda x: x['name'], replay.players.values()))))) == 2
        has_mmr = bool(list(filter(lambda x: x, replay.match_data['mmr'].values())))
        return is_not_ai and has_mmr

    serialized_replays = []
    replay_queryset = list(replay_queryset)
    replay_queryset.sort(key=lambda x: x.played_at, reverse=True)

    # if there was a race param in the endpoint URL,
    # filter out irrelevant replays
    if race:
        races = ['protoss', 'terran', 'zerg']
        if race not in races:
            return None

        # use .filter() method?
        race_replay_queryset = []
        for replay in replay_queryset:
            if not is_ladder_replay(replay):
                continue

            if not target and replay.match_length < 60:
                continue

            player_id = str(replay.user_match_id)
            if race == replay.players[player_id]['race'].lower():
                race_replay_queryset.append(replay)
        replay_queryset = race_replay_queryset

    # for count only return early
    if target == 'count':
        return len(replay_queryset)

    if target == 'verify':
        def is_unlinked(replay):
            if not replay.battlenet_account:
                return True
            return False

        return list(filter(is_unlinked, replay_queryset))

    if target == 'summary':
        linked_replays = 0
        unlinked_replays = 0
        other_account = 0

        for replay in replay_queryset:
            if replay.battlenet_account == battlenet_account:
                linked_replays += 1
            elif replay.battlenet_account:
                other_account += 1
            else:
                unlinked_replays += 1

        return {
            'linked': linked_replays,
            'unlinked': unlinked_replays,
            'other': other_account,
        }

    # limit returned replays to 100 for performance reasons
    limited_queryset = replay_queryset[:100]

    # calculate how long ago since each match was played
    # replace with native HTML?
    for replay in limited_queryset:
        date = replay.played_at
        days = datetime.timedelta(
            seconds=datetime.datetime.timestamp(datetime.datetime.now()) - datetime.datetime.timestamp(date)
        ).days

        if days != -1:
            weeks = int(round(days / 7, 0))
            months = int(floor(weeks / 4))
        else:
            weeks = 0
            months = 0

        if months > 0:
            if weeks - (months * 4) == 0:
                date_diff = f'{months}m'
            else:
                date_diff = f'{months}m'  # *{weeks - (months * 4)}/4*'
        elif weeks > 0:
            date_diff = f'{weeks}w'
        else:
            if days == -1:
                date_diff = 'Today'
            elif days == 1:
                date_diff = 'Yesterday'
            else:
                date_diff = f'{days}d'

        serializer = ReplaySerializer(replay)
        serializer = copy.deepcopy(serializer.data)
        serializer['played_at'] = date_diff
        serializer['url'] = urlsafe_b64encode(bytes.fromhex(serializer['file_hash'][:18])).decode('utf-8')

        new_serializer = {}
        for stat, info in serializer.items():
            if stat == 'match_data':
                new_serializer['match_data'] = {}

                # replace nested dict structure with flat one
                # only resource stats are nested
                for name, values in info.items():
                    if type(values) is dict and 'minerals' in values:
                        for resource, value in values.items():
                            new_serializer[stat][f'{name}_{resource}'] = value
                    else:
                        new_serializer[stat][name] = values
            else:
                new_serializer[stat] = info
        serializer = new_serializer
        serialized_replays.append(serializer)
    return serialized_replays
