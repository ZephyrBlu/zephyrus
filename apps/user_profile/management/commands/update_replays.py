import gzip
import json
import traceback
import asyncio
from zephyrus_sc2_parser import parse_replay

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from apps.user_profile.models import Replay
from rest_framework.authtoken.models import Token
from storages.backends.gcloud import GoogleCloudStorage
from google.cloud import pubsub_v1
from allauth.account.models import EmailAddress
from zephyrus.settings import (
    TIMELINE_STORAGE,
    GS_PROJECT_ID,
    GS_CREDENTIALS,
    UPLOAD_FUNC_TOPIC,
)

MAX_CONCURRENT_REPLAYS = 25


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

        self.stdout.write('Querying for required data')

        # pre-fetch all users, replays and tokens to minimize database queries
        # call .values() to convert objects -> dict for faster access
        # cast to list to force Django to execute the queries
        user_objects = list(EmailAddress.objects.all().values())
        self.stdout.write('Fetched user accounts')

        replays = list(Replay.objects.all().values())
        self.stdout.write('Fetched replays')

        token_objects = list(Token.objects.all().values())
        self.stdout.write('Fetched auth tokens\n\n')

        # cache user data for later use
        users = {}
        for user in user_objects:
            users[user['email']] = user

        # cache user tokens for later use
        user_tokens = {}
        for token in token_objects:
            user_tokens[token['user_id']] = token['key']

        self.stdout.write(f'{len(replays)} replays found, starting re-processing\n\n')
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
            async def update_replays_async():
                settings = pubsub_v1.types.BatchSettings(
                    max_messages=MAX_CONCURRENT_REPLAYS,
                    max_latency=1,
                )
                client = pubsub_v1.PublisherClient(
                    credentials=GS_CREDENTIALS,
                    publisher_options=pubsub_v1.types.PublisherOptions(
                        flow_control=pubsub_v1.types.PublishFlowControl(
                            message_limit=MAX_CONCURRENT_REPLAYS,
                            limit_exceeded_behavior=pubsub_v1.types.LimitExceededBehavior.BLOCK,
                        ),
                    ),
                    batch_settings=settings,
                )
                topic_path = client.topic_path(GS_PROJECT_ID, UPLOAD_FUNC_TOPIC)

                for count, replay in enumerate(replays):
                    if count % MAX_CONCURRENT_REPLAYS == 0:
                        self.stdout.write('Sleeping for 1s\n\n')
                        await asyncio.sleep(1)

                    if not replay['user_account_id']:
                        continue

                    if replay['battlenet_account_id']:
                        replay_path = f'{replay["user_account_id"]}/{replay["battlenet_account_id"]}/{replay["file_hash"]}.SC2Replay'
                    else:
                        replay_path = f'{replay["user_account_id"]}/{replay["file_hash"]}.SC2Replay'
                    timeline_path = f'{replay["file_hash"]}.json.gz'

                    if options['details']:
                        self.stdout.write(f'User: {replay["user_account_id"]}')
                        if replay['battlenet_account_id']:
                            self.stdout.write(f'Battlenet Account: {replay["battlenet_account_id"]}')
                        self.stdout.write(f'File Hash: {replay["file_hash"]}\n\n')

                    current_user = users[replay['user_account_id']]
                    token = user_tokens[current_user['user_id']]
                    client.publish(
                        topic_path,
                        token=token,
                        paths=json.dumps({'replay': replay_path, 'timeline': timeline_path}),
                        data=b''  # data must be a bytestring.
                    )
            asyncio.run(update_replays_async())

        num_replays = len(replays)
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {num_replays} replays'))

        for e in error_list:
            for part in e:
                print(part)
