from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
import pytz
import datetime
import logging

logger = logging.getLogger(__name__)


def write_replay(replay_data, request):
    user = request.user
    file_hash = replay_data['file_hash']
    players = replay_data['players']
    summary_stats = replay_data['summary_stats']
    metadata = replay_data['metadata']

    user_id = None

    filename = f'{file_hash}.SC2Replay'
    timeline_filename = f'{file_hash}.json.gz'

    user_account = EmailAddress.objects.get(user=user)
    user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user_account)
    replay_query = Replay.objects.filter(file_hash=file_hash, user_account_id=user_account.email)

    match_region = players['1']['region_id']

    # means there is no duplicate
    if not replay_query:
        kwargs = [
            {f'region_profiles__{match_region}__profile_id__contains': players['1']['profile_id']},
            {f'region_profiles__{match_region}__profile_id__contains': players['2']['profile_id']}
        ]
        if user_battlenet_accounts:
            for index, k in enumerate(kwargs):
                try:
                    player_battlenet_account = user_battlenet_accounts.get(**k)
                    bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{filename}'
                    player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']

                    if players[str(metadata['winner'])]['profile_id'] in player_profile_id:
                        win = True
                    else:
                        win = False

                    user_id = index + 1
                    break
                except ObjectDoesNotExist:
                    player_battlenet_account = None
                    win = None
                    bucket_path = f'{user.email}/{filename}'
                    user_id = None
        else:
            player_battlenet_account = None
            win = None
            bucket_path = f'{user.email}/{filename}'

        replay = Replay(
            file_hash=file_hash,
            user_account=user_account,
            battlenet_account=player_battlenet_account,
            players=players,
            user_match_id=user_id,
            match_data=summary_stats,
            match_length=metadata['game_length'],
            played_at=datetime.datetime.fromtimestamp(metadata['time_played_at']).replace(tzinfo=pytz.utc),
            map=metadata['map'],
            region_id=match_region,
            win=win
        )
        replay.save()
        return {'replay_path': bucket_path, 'timeline_path': timeline_filename}
    else:
        return False
