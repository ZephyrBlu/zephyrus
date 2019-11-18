# from .utils.mvp import main as parse_replay
from zephyrus_sc2_parser import parse_replay
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
import json
import gzip
from storages.backends.gcloud import GoogleCloudStorage
from zephyrus.settings import TIMELINE_STORAGE
import logging

logger = logging.getLogger(__name__)


def process_file(replay_file, request, file_hash):
    user = request.user

    players, timeline, summary_stats, metadata = parse_replay(replay_file)

    if players is None:
        logger.critical(f'{user.email}, f{file_hash}: Replay was aborted')
        return 'error'

    timeline_storage = GoogleCloudStorage(bucket_name=TIMELINE_STORAGE)
    player_summary = {}
    player_summary[1] = vars(players[1])
    player_summary[2] = vars(players[2])
    user_id = None
    timeline = {'timeline': timeline}

    filename = replay_file.name
    timeline_filename = f'{replay_file.name[:-10]}.json.gz'

    user_account = EmailAddress.objects.get(user=user)
    user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user_account)
    replay_query = Replay.objects.filter(file_hash=file_hash, user_account_id=user_account.email)

    match_region = players[1].region_id

    duplicate_replay = False
    if replay_query:
        duplicate_replay = True

    print(duplicate_replay)

    if not duplicate_replay:
        kwargs = [
            {f'region_profiles__{match_region}__profile_id__contains': players[1].profile_id},
            {f'region_profiles__{match_region}__profile_id__contains': players[2].profile_id}
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
            bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{filename}'

            player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']
            if players[metadata['winner']].profile_id in player_profile_id:
                win = True
            else:
                win = False
        else:
            win = None
            bucket_path = f'{user.email}/{filename}'

        replay = Replay(
            file_hash=file_hash,
            user_account=user_account,
            battlenet_account=player_battlenet_account,
            players=player_summary,
            user_match_id=user_id,
            match_data=summary_stats,
            match_length=metadata['game_length'],
            played_at=metadata['time_played_at'],
            map=metadata['map'],
            region_id=match_region,
            win=win
        )
        replay.save()
        print('replay saved')

        print(bucket_path)
        file_contents = replay_file.open(mode='rb')
        current_replay = default_storage.open(bucket_path, 'w')
        current_replay.write(file_contents.read())
        current_replay.close()

        print(timeline_filename)
        current_timeline = timeline_storage.open(timeline_filename, 'w')
        current_timeline.write(gzip.compress(json.dumps(timeline).encode('utf-8')))
        current_timeline.blob.content_encoding = 'gzip'
        current_timeline.close()
    else:
        pass
