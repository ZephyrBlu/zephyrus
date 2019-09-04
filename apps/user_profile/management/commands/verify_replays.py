from django.core.management.base import BaseCommand
from apps.process_replays.utils.mvp import main as parse_replay
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone


class Command(BaseCommand):
    help = 'Updates all user Replays'

    def add_arguments(self, parser):
        parser.add_argument(
            '--details',
            action='store_true',
            help='Show the details of each replay being processed'
        )

    def process_file(self, user, replay_file, options):
        if replay_file[-10:] != '.SC2Replay':
            return

        file_hash = replay_file[:-10]

        file_contents = default_storage.open(f'{user.email}/{replay_file}', 'rb')
        players, summary_stats, metadata = parse_replay(file_contents)

        if players is None:
            self.stdout.write('Error')
            return

        player_summary = {}
        player_summary[1] = vars(players[1])
        player_summary[2] = vars(players[2])

        user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user)

        if options:
            self.stdout.write(f'User: {user.email}')
            self.stdout.write(f'File Hash: {file_hash}')

        replay_query = Replay.objects.filter(file_hash=file_hash)
        duplicate_replay = False
        if replay_query:
            if replay_query[0].battlenet_account:
                duplicate_replay = True

        if not duplicate_replay:
            match_region = players[1].region_id

            kwargs = [
                {f'region_profiles__{match_region}__profile_id__contains': players[1].profile_id},
                {f'region_profiles__{match_region}__profile_id__contains': players[2].profile_id}
            ]
            if user_battlenet_accounts:
                for k in kwargs:
                    try:
                        player_battlenet_account = user_battlenet_accounts.get(**k)

                        if options:
                            self.stdout.write(f'Battlenet Account found: {player_battlenet_account.battletag}')
                        break
                    except ObjectDoesNotExist:
                        player_battlenet_account = None

                        if options:
                            self.stdout.write(f'Battlenet Account not found\n\n')
            else:
                player_battlenet_account = None

            bucket_path = None
            if player_battlenet_account:
                bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{replay_file}'

                player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']
                if players[metadata['winner']].profile_id == player_profile_id:
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

            if bucket_path:
                current_replay = default_storage.open(bucket_path, 'w')
                current_replay.write(file_contents.read())
                file_contents.close()
                current_replay.close()

                if options:
                    self.stdout.write(f'Replay saved to bucket\n\n')
        else:
            self.stdout.write('Replay already linked to Battlenet Account\n\n')

    def handle(self, *args, **options):
        users = list(EmailAddress.objects.all())

        for u in users:
            dirs, replays = default_storage.listdir(f'{u.email}')
            for file in replays:
                self.process_file(u, file, True)
