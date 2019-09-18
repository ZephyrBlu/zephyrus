from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay
from apps.process_replays.views import parse_replay


class Command(BaseCommand):
    help = 'Updates Replay objects with latest parser output'

    def add_arguments(self, parser):
        parser.add_argument(
            '--details',
            action='store_true',
            help='Show the details of each replay being processed'
        )

    def handle(self, *args, **options):
        replays = list(Replay.objects.all())

        for r in replays:
            user = r.user_account
            if r.battlenet_account:
                bucket_path = f'{user.email}/{r.battlenet_account.battletag}/{r.file_hash}.SC2Replay'
            else:
                bucket_path = f'{user.email}/{r.file_hash}.SC2Replay'

            if options['details']:
                self.stdout.write(f'User: {user.email}')
                self.stdout.write(f'Battlenet Account: {r.battlenet_account.battletag}')
                self.stdout.write(f'File Hash: {r.file_hash}')
            try:
                current_replay = default_storage.open(bucket_path, 'rb')
            except Exception as error:
                raise CommandError(f'No replay exists in the storage bucket at path: {bucket_path}')

            if options['details']:
                self.stdout.write(f'File opened')

            players, summary_stats, metadata = parse_replay(current_replay)

            if not summary_stats:
                raise CommandError(f'There was an error when parsing replay {r.file_hash}')

            if options['details']:
                self.stdout.write(f'File parsed')

            current_replay.close()

            r.match_data = summary_stats
            r.save()
            if options['details']:
                self.stdout.write(f'Success!\n\n')

        num_replays = len(replays)
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {num_replays} replays'))
