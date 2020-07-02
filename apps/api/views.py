import requests
import json
import logging
from google.cloud import pubsub_v1, storage

from django.contrib.auth import authenticate, login, logout
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseBadRequest,
    HttpResponseServerError,
)

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

from zephyrus.settings import (
    GS_PROJECT_ID,
    GS_CREDENTIALS,
    REPLAY_STORAGE,
    UPLOAD_FUNC_TOPIC,
    VERIFY_FUNC_TOPIC,
    TIMELINE_STORAGE,
    API_KEY,
    FRONTEND_URL,
)
from apps.user_profile.models import FeatureVote, Replay, BattlenetAccount
from apps.process_replays.views import write_replay
from apps.user_profile.secret.production import CLIENT_ID, CLIENT_SECRET

from .utils.trends import trends as analyze_trends
from .utils.filter_user_replays import filter_user_replays
from .utils.get_user_info import get_user_info
from .utils.parse_profile import parse_profile
from .permissions import IsOptionsPermission, IsPostPermission
from .authentication import IsOptionsAuthentication

logger = logging.getLogger(__name__)


class ExternalLogin(APIView):
    """
    Handles user logins from the /login API endpoint

    If a user does not have a verified email, a verification
    email is sent.

    The user's account information, Token and main race are sent in the response
    """
    authentication_classes = []
    permission_classes = [IsOptionsPermission | IsPostPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
        return response

    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user_info = get_user_info(user)

            if not user_info['user']['verified']:
                send_email_confirmation(request, user)

            response = Response(user_info)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
            return response
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
            return response


class ExternalLogout(APIView):
    """
    Handles user logouts from the /logout API endpoint
    """
    # authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    # permission_classes = [IsAuthenticated | IsOptionsPermission]
    authentication_classes = []
    permission_classes = []

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        logout(request)
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class VerifyReplaysViewset(viewsets.ModelViewSet):
    """
    Returns all user replays played with the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request):
        unlinked_replays = filter_user_replays(request, None, 'verify')

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GS_PROJECT_ID, VERIFY_FUNC_TOPIC)

        for replay in unlinked_replays:
            replay_data = {
                'file_hash': replay.file_hash,
                'user_account': replay.user_account,
            }
            byte_data = json.dumps(replay_data).encode('utf-8')

            # When you publish a message, the client returns a future.
            publisher.publish(
                topic_path, data=byte_data  # data must be a bytestring.
            )

        response = Response({
            'count': len(unlinked_replays),
        })
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def verify(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class ReplaySummaryViewset(viewsets.ModelViewSet):
    """
    Returns all user replays played with the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def retrieve(self, request):
        replay_summary = filter_user_replays(request, None, 'summary')
        response = Response(replay_summary)
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class RaceReplayViewSet(viewsets.ModelViewSet):
    """
    Returns all user replays played with the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request, race):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def retrieve(self, request, race=None):
        serialized_replays = filter_user_replays(request, race)

        if serialized_replays is not None:
            response = Response(serialized_replays)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        response = HttpResponseBadRequest({'response': 'No replays found or invalid race'})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def count(self, request, race=None):
        replay_count = filter_user_replays(request, race, 'count')

        if replay_count is not None:
            response = Response(replay_count)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        elif replay_count is False:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        response = HttpResponseBadRequest({'response': 'No replays found or invalid race'})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class FetchReplayTimeline(APIView):
    """
    Fetches the replay timeline related to the file hash param

    Returns the download URL for the timeline file
    """
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated | IsOptionsPermission]
    authentication_classes = []
    permission_classes = []

    def options(self, request, file_hash):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request, file_hash):
        timeline_url = f'https://www.googleapis.com/storage/v1/b/{TIMELINE_STORAGE}/o/{file_hash}.json.gz?key={API_KEY}'

        response = requests.get(timeline_url, headers={'Accept-Encoding': 'gzip'})
        metadata = response.json()

        response = Response({'timeline_url': metadata['mediaLink']})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class FetchReplayFile(viewsets.ModelViewSet):
    """
    Returns a link to the downloadable replay file
    """
    authentication_classes = []
    permission_classes = [IsAuthenticatedOrReadOnly | IsOptionsPermission]

    def preflight(self, request, file_hash):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def download(self, request, file_hash):
        replay = list(Replay.objects.filter(file_hash=file_hash))[0]

        storage_client = storage.Client(project=GS_PROJECT_ID, credentials=GS_CREDENTIALS)
        replay_storage = storage_client.get_bucket(REPLAY_STORAGE)
        replay_blob_path = f'{replay.user_account_id}/{replay.battlenet_account_id}/{file_hash}.SC2Replay'
        replay_blob = replay_storage.blob(replay_blob_path)
        downloaded_replay = replay_blob.download_as_string(raw_download=True)

        response = HttpResponse(downloaded_replay, content_type='application/octet-stream')
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Content-Disposition'] = f'attachment; filename="{file_hash}.SC2Replay"'
        return response


class RaceStatsViewSet(viewsets.ModelViewSet):
    """
    Returns the user's stats for the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request, race):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def retrieve(self, request, race=None):
        races = ['protoss', 'terran', 'zerg']
        if race not in races:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)

        if BattlenetAccount.objects.filter(user_account_id=user_id).exists():
            battlenet_account = BattlenetAccount.objects.get(user_account_id=user_id)
        else:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        account_replays = Replay.objects.filter(battlenet_account=battlenet_account)

        if len(account_replays) <= 0:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        battlenet_id_list = []
        for region_id, info in battlenet_account.region_profiles.items():
            battlenet_id_list.extend(info['profile_id'])

        trend_data = analyze_trends(account_replays, battlenet_id_list, race)
        if trend_data:
            serialized_data = json.dumps(trend_data)
        else:
            serialized_data = None

        response = Response(serialized_data)
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class Stats(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)

        if BattlenetAccount.objects.filter(user_account_id=user_id).exists():
            battlenet_account = BattlenetAccount.objects.get(
                user_account_id=user_id
            )
        else:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        account_replays = Replay.objects.filter(
            battlenet_account=battlenet_account
        )

        if len(account_replays) <= 0:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        battlenet_id_list = []
        for region_id, info in battlenet_account.region_profiles.items():
            battlenet_id_list.extend(info['profile_id'])

        trend_data = analyze_trends(account_replays, battlenet_id_list)

        response = Response(json.dumps(trend_data))
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class UploadReplay(APIView):
    """
    Handles replay uploads from the /upload API endpoint

    Creates a File wrapper around uploaded replay file data,
    then hashes the file to create a unique ID.

    Then the replay file is processed and stored in a bucket, or if
    processing is unsuccessful an error is returned and the replay is
    stored in an alternate bucket for failed replays.
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        return response

    def post(self, request):
        token = str(request.auth)
        file_data = request.body

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GS_PROJECT_ID, UPLOAD_FUNC_TOPIC)

        # When you publish a message, the client returns a future.
        publisher.publish(
            topic_path, token=token, data=file_data  # data must be a bytestring.
        )

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        return response


class WriteReplaySet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def write(self, request):
        replay_data = json.loads(request.body)
        result = write_replay(replay_data, request)

        if result is None:
            response = HttpResponseServerError()
            response['Access-Control-Allow-Headers'] = 'authorization'
        else:
            response = Response(result)
            response['Access-Control-Allow-Headers'] = 'authorization'
        return response


oauth_api_url = 'https://us.battle.net'


class BattlenetAuthorizationUrl(APIView):
    """
    Handles initial OAuth flow for a user linking their battlenet account

    Returns a redirect URL to begin the OAuth process
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        auth_url = f'{oauth_api_url}/oauth/authorize'

        response_type = 'code'
        client_id = CLIENT_ID
        redirect_uri = FRONTEND_URL
        scope = 'sc2.profile'
        url = f'{auth_url}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}'

        response = Response({'url': url})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class SetBattlenetAccount(APIView):
    """
    Handles OAuth auth code --> token --> user info flow

    Gathers extra user profile information to automatically match replays
    NOTE: This functionality is currently broken due to Blizzard disabling
    the SC2 Community APIs
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def post(self, request):
        auth_code = json.loads(request.body)['authCode']
        token_url = f'{oauth_api_url}/oauth/token'
        redirect_uri = FRONTEND_URL
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        info = requests.post(token_url, data=data)
        access_token = info.json()['access_token']

        user_info_url = f'{oauth_api_url}/oauth/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        json_info = requests.get(user_info_url, headers=headers)

        user_info = json_info.json()

        current_account = EmailAddress.objects.get(email=request.user.email)

        user_id = user_info['id']
        profile_data_url = f'https://us.api.blizzard.com/sc2/player/{user_id}?access_token={access_token}'
        profile_data = requests.get(profile_data_url)
        profiles = {}

        if profile_data.ok:
            profile_data = profile_data.json()

            regions = {1: 'NA', 2: 'EU', 3: 'KR'}

            for profile in profile_data:
                if int(profile['regionId']) in profiles:
                    profiles[int(profile['regionId'])]['profile_id'].append(int(profile['profileId']))
                else:
                    profiles[int(profile['regionId'])] = {
                        'profile_name': profile['name'],
                        'region_name': regions[profile['regionId']],
                        'profile_id': [int(profile['profileId'])],
                        'realm_id': int(profile['realmId'])
                    }

        authorized_account = BattlenetAccount(
            id=user_id,
            battletag=user_info['battletag'],
            user_account=current_account,
            region_profiles=profiles
        )
        authorized_account.save()

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class CheckUserInfo(APIView):
    """
    Handles checking if a user has at least 1 battlenet account linked
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user

        # send_email_confirmation(request, user)

        user_info = get_user_info(user)

        response = Response(user_info)
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class AddUserProfile(APIView):
    """
    Handles validating, parsing and adding game profiles
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def post(self, request):
        user = request.user

        user_profile_url = request.body.decode('utf-8')
        profile_data = parse_profile(user_profile_url)

        if profile_data:
            # save data to user model

            user_battlenet_account = BattlenetAccount.objects.get(
                user_account_id=user.email,
            )

            region_id = list(profile_data.keys())[0]
            new_profile_id = profile_data[region_id]['profile_id'][0]

            if region_id in user_battlenet_account.region_profiles:
                current_profile_id = user_battlenet_account.region_profiles[region_id]['profile_id']
                if new_profile_id not in current_profile_id:
                    current_profile_id.append(new_profile_id)
            else:
                user_battlenet_account.region_profiles.update(profile_data)
            user_battlenet_account.save()

            response = Response()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class ResendEmail(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        send_email_confirmation(request, user)

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class FeatureVoteSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    feature_votes = {
        'f1cab883-f18b-49f8-976a-a62e4b4a82c6': [
            'shareable-replay-pages',
            'winrate-page',
            'game-info',
            'demo-website',
            'focus-goal-tracking',
            'other',
        ],
    }

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def fetch(self, request):
        _uuid = list(self.feature_votes.keys())[0]
        votes = list(FeatureVote.objects.filter(
            vote_id=_uuid,
            user_account_id=request.user.email,
        ))

        response = Response({'votes': list((f.feature, f.comment) for f in votes)})
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def write(self, request):
        data = json.loads(request.body)
        features = data['features']
        votes = data['votes']

        if len(votes) > 2:
            limited_votes = {}
            for count, (f, c) in enumerate(votes.items(), start=1):
                if count >= 2:
                    break
                limited_votes[f] = c
            votes = limited_votes

        for _uuid, f in self.feature_votes.items():
            # if features match, then we save votes
            if f == features:
                existing_votes = list(FeatureVote.objects.filter(
                    vote_id=_uuid,
                    user_account_id=request.user.email,
                ))

                # set for keeping track of new votes
                # that match existing votes
                existing_features = set()

                # saving each vote to database
                for feature_code, comment in votes.items():
                    # if client feature_code isn't in our
                    # feature list, stop doing things
                    # either error or malicious
                    if feature_code not in f:
                        break

                    exists = False
                    for v in existing_votes:
                        if feature_code == v.feature and comment == v.comment:
                            exists = True
                            existing_features.add(feature_code)
                            break

                    # if a vote for this feature doesn't already exist
                    # create a new record for it
                    if not exists:
                        new_vote = FeatureVote(
                            vote_id=_uuid,
                            user_account_id=request.user.email,
                            feature=feature_code,
                            comment=comment[:100],
                        )
                        new_vote.save()

                # remove old votes from the database
                # iterate through all existing votes
                # if the feature already existed, leave it
                # else delete the record
                for vote in existing_votes:
                    # feature in existing_features set means
                    # it already existed in the database
                    if vote.feature not in existing_features:
                        vote.delete()
                break

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response
