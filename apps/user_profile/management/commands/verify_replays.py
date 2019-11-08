from django.core.management.base import BaseCommand
from zephyrus_sc2_parser import parse_replay
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from storages.backends.gcloud import GoogleCloudStorage
import json
import gzip


class Command(BaseCommand):
    help = 'Updates all user Replays'

    def add_arguments(self, parser):
        # parser.add_argument(
        #     '--details',
        #     action='store_true',
        #     help='Show the details of each replay being processed'
        # )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Reprocesses all replays instead of only those without a battlenet account'
        )

    def process_file(self, user, replay_file, options, battletag=None, *, all_replays=False):
        if replay_file[-10:] != '.SC2Replay':
            return

        file_hash = replay_file[:-10]
        timeline_filename = f'{replay_file[:-10]}.json.gz'

        if battletag:
            file_contents = default_storage.open(f'{user.email}/{battletag}/{replay_file}', 'rb')
        else:
            file_contents = default_storage.open(f'{user.email}/{replay_file}', 'rb')
        players, timeline, summary_stats, metadata = parse_replay(file_contents)

        if players is None:
            self.stdout.write('Error')
            return

        timeline_storage = GoogleCloudStorage(bucket_name='sc2-timelines-dev')
        player_summary = {}
        player_summary[1] = vars(players[1])
        player_summary[2] = vars(players[2])
        user_id = None

        timeline = {'timeline': timeline}

        user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user)

        if options:
            self.stdout.write(f'User: {user.email}')
            self.stdout.write(f'File Hash: {file_hash}')

        replay_query = Replay.objects.filter(file_hash=file_hash)
        duplicate_replay = False
        if replay_query:
            if replay_query[0].battlenet_account:
                duplicate_replay = True

        if not duplicate_replay or all_replays:
            match_region = players[1].region_id

            kwargs = [
                {f'region_profiles__{match_region}__profile_id__contains': players[1].profile_id},
                {f'region_profiles__{match_region}__profile_id__contains': players[2].profile_id}
            ]
            if user_battlenet_accounts:
                for index, k in enumerate(kwargs):
                    try:
                        player_battlenet_account = user_battlenet_accounts.get(**k)
                        user_id = index + 1

                        if options:
                            self.stdout.write(f'Battlenet Account found: {player_battlenet_account.battletag}')

                        break
                    except ObjectDoesNotExist:
                        player_battlenet_account = None
                        user_id = None

                        if options:
                            self.stdout.write(f'Battlenet Account not found\n\n')
            else:
                player_battlenet_account = None

            bucket_path = None
            if player_battlenet_account:
                bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{replay_file}'

                player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']
                if players[metadata['winner']].profile_id in player_profile_id:
                    win = True
                else:
                    win = False
            else:
                return

            replay = Replay(
                file_hash=file_hash,
                user_account=user,
                battlenet_account=player_battlenet_account,
                players=player_summary,
                user_match_id=user_id,
                match_data=summary_stats,
                match_length=metadata['game_length'],
                played_at=metadata['time_played_at'],
                uploaded_at=timezone.now(),
                map=metadata['map'],
                region_id=match_region,
                win=win
            )
            replay.save()

            if options:
                self.stdout.write(f'Replay saved to database')

            current_timeline = timeline_storage.open(timeline_filename, 'w')
            current_timeline.write(gzip.compress(json.dumps(timeline).encode('utf-8')))
            current_timeline.blob.content_encoding = 'gzip'
            current_timeline.close()

            if bucket_path and not all_replays:
                current_replay = default_storage.open(bucket_path, 'w')
                current_replay.write(file_contents.read())
                current_replay.close()

                if options:
                    self.stdout.write(f'Replay saved to bucket\n\n')
            file_contents.close()

        else:
            self.stdout.write('Replay already linked to Battlenet Account\n\n')

    def handle(self, *args, **options):
        users = list(EmailAddress.objects.all())

        if options['all']:
            for u in users:
                user_battlenet_profiles = list(BattlenetAccount.objects.filter(user_account=u))

                for bnet_account in user_battlenet_profiles:
                    dirs, replays = default_storage.listdir(f'{u.email}/{bnet_account.battletag}/')
                    for file in replays:
                        self.process_file(u, file, True, bnet_account.battletag, all_replays=True)
        else:
            for u in users:
                dirs, replays = default_storage.listdir(f'{u.email}')
                for file in replays:
                    self.process_file(u, file, True)
