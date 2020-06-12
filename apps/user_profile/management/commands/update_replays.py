import gzip
import json
import traceback
from zephyrus_sc2_parser import parse_replay

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay
from rest_framework.authtoken.models import Token
from storages.backends.gcloud import GoogleCloudStorage
from google.cloud import pubsub_v1
from zephyrus.settings import TIMELINE_STORAGE, GS_PROJECT_ID, UPLOAD_FUNC_TOPIC


class Command(BaseCommand):
    help = 'Updates Replay objects with latest parser output'

    def add_arguments(self, parser):
        parser.add_argument(
            '--local',
            action='store_true',
            help='Decide how to process replays'
        )

        parser.add_argument(
            '--details',
            action='store_true',
            help='Show the details of each replay being processed'
        )

    def handle(self, *args, **options):
        if options['local'] and TIMELINE_STORAGE != 'sc2-timelines-dev':
            return

        replays = list(Replay.objects.all())
        error_list = []

        if options['local']:
            for r in replays:
                user = r.user_account
                if r.battlenet_account:
                    bucket_path = f'{user.email}/{r.battlenet_account.battletag}/{r.file_hash}.SC2Replay'
                else:
                    bucket_path = f'{user.email}/{r.file_hash}.SC2Replay'

                if options['details']:
                    self.stdout.write(f'User: {user.email}')
                    if r.battlenet_account:
                        self.stdout.write(f'Battlenet Account: {r.battlenet_account.battletag}')
                    self.stdout.write(f'File Hash: {r.file_hash}')

                try:
                    current_replay = default_storage.open(bucket_path, 'rb')
                except Exception as error:
                    self.stdout.write(f'No replay exists in the storage bucket at path: {bucket_path}\n')
                    continue

                if options['details']:
                    self.stdout.write('File opened')

                try:
                    players, timeline, engagements, summary_stats, metadata = parse_replay(current_replay)
                except Exception as error:
                    self.stdout.write('\nAn error occurred\n')
                    error_list.append((bucket_path, r.file_hash, error, traceback.format_exc()))
                    continue

                if not summary_stats:
                    raise CommandError(f'There was an error when parsing replay {r.file_hash}')

                if options['details']:
                    self.stdout.write('File parsed')

                current_replay.close()

                r.players = {1: players[1].to_json(), 2: players[2].to_json()}
                r.match_data = summary_stats
                r.save()

                if options['details']:
                    self.stdout.write('Successfully updated database')

                timeline_storage = GoogleCloudStorage(bucket_name=TIMELINE_STORAGE)
                current_timeline = timeline_storage.open(f'{r.file_hash}.json.gz', 'w')

                timeline_data = {'timeline': timeline}
                current_timeline.write(gzip.compress(json.dumps(timeline_data).encode('utf-8')))
                current_timeline.blob.content_encoding = 'gzip'
                current_timeline.close()

                if options['details']:
                    self.stdout.write(f'Success!\n\n')
        else:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(GS_PROJECT_ID, UPLOAD_FUNC_TOPIC)

            for replay in replays:
                user = replay.user_account
                if replay.battlenet_account:
                    replay_path = f'{user.email}/{replay.battlenet_account.battletag}/{replay.file_hash}.SC2Replay'
                else:
                    replay_path = f'{user.email}/{replay.file_hash}.SC2Replay'
                timeline_path = f'{replay.file_hash}.json.gz'

                if options['details']:
                    self.stdout.write(f'User: {user.email}')
                    if replay.battlenet_account:
                        self.stdout.write(f'Battlenet Account: {replay.battlenet_account.battletag}')
                    self.stdout.write(f'File Hash: {replay.file_hash}')

                token = Token.objects.get(user_id=replay.user_account.id)

                # When you publish a message, the client returns a future.
                publisher.publish(
                    topic_path,
                    token=str(token),
                    paths=json.dumps({'replay': replay_path, 'timeline': timeline_path}),
                    data=b''  # data must be a bytestring.
                )

                if options['details']:
                    self.stdout.write('Data sent to Cloud Function\n\n')

        num_replays = len(replays)
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {num_replays} replays'))

        for e in error_list:
            for part in e:
                print(part)
