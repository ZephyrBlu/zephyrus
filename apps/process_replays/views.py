# from .utils.mvp import main as parse_replay
from zephyrus_sc2_parser import parse_replay
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
import json
import gzip
from storages.backends.gcloud import GoogleCloudStorage
from zephyrus.settings import TIMELINE_STORAGE, FAILED_STORAGE
import pytz
import datetime
import logging

logger = logging.getLogger(__name__)


def write_replay(replay_data, request):
    user = request.user

    # players, timeline, summary_stats, metadata = parse_replay(replay_file)

    # if players is None:
    #     logger.info(f'{user.email}, {file_hash}: Replay was aborted')
    #
    #     failed_storage = GoogleCloudStorage(bucket_name=FAILED_STORAGE)
    #     failed_replay_path = f'{user.email}/{replay_file.name}'
    #
    #     file_contents = replay_file.open(mode='rb')
    #     current_replay = failed_storage.open(failed_replay_path, 'w')
    #     current_replay.write(file_contents.read())
    #     current_replay.close()
    #     return 'error'

    # timeline_storage = GoogleCloudStorage(bucket_name=TIMELINE_STORAGE)
    file_hash = replay_data['file_hash']
    players = replay_data['players']
    summary_stats = replay_data['summary_stats']
    metadata = replay_data['metadata']

    user_id = None
    # timeline = {'timeline': timeline}

    # filename = replay_file.name
    # timeline_filename = f'{filename[:-10]}.json.gz'

    user_account = EmailAddress.objects.get(user=user)
    user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user_account)
    replay_query = Replay.objects.filter(file_hash=file_hash, user_account_id=user_account.email)

    match_region = players['1']['region_id']

    duplicate_replay = False
    if replay_query:
        duplicate_replay = True

    if not duplicate_replay:
        kwargs = [
            {f'region_profiles__{match_region}__profile_id__contains': players['1']['profile_id']},
            {f'region_profiles__{match_region}__profile_id__contains': players['2']['profile_id']}
        ]
        if user_battlenet_accounts:
            for index, k in enumerate(kwargs):
                try:
                    player_battlenet_account = user_battlenet_accounts.get(**k)
                    user_id = index + 1
                    break
                except ObjectDoesNotExist:
                    player_battlenet_account = None
                    user_id = None
        else:
            player_battlenet_account = None
        if player_battlenet_account:
            # bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{filename}'

            player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']
            if players[str(metadata['winner'])]['profile_id'] in player_profile_id:
                win = True
            else:
                win = False
        else:
            win = None
            # bucket_path = f'{user.email}/{filename}'

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
        return True

        # file_contents = replay_file.open(mode='rb')
        # current_replay = default_storage.open(bucket_path, 'w')
        # current_replay.write(file_contents.read())
        # current_replay.close()
        #
        # current_timeline = timeline_storage.open(timeline_filename, 'w')
        # current_timeline.write(gzip.compress(json.dumps(timeline).encode('utf-8')))
        # current_timeline.blob.content_encoding = 'gzip'
        # current_timeline.close()
    else:
        return False
