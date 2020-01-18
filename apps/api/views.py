import requests
import io
import hashlib
import json
import logging

from django.contrib.auth import authenticate, login, logout
from django.core.files import File
from django.http import (
    HttpResponseNotFound,
    HttpResponseBadRequest,
    HttpResponseServerError,
)

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

from zephyrus.settings import TIMELINE_STORAGE, API_KEY, FRONTEND_URL
from apps.user_profile.models import Replay, BattlenetAccount
from apps.process_replays.views import process_file
from apps.user_profile.secret.master import CLIENT_ID, CLIENT_SECRET

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
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

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


class RaceReplayViewSet(viewsets.ModelViewSet):
    """
    Returns all user replays played with the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    @action(
        detail=False,
        methods=['OPTIONS'],
    )
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
        response = HttpResponseBadRequest("Invalid race")
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class BattlenetAccountReplays(APIView):
    """
    Returns all the replays associated with a user's battlenet account
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        serialized_replays = filter_user_replays(request)

        if serialized_replays is not None:
            response = Response(serialized_replays)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response
        response = HttpResponseBadRequest("Invalid race")
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class FetchReplayTimeline(APIView):
    """
    Fetches the replay timeline related to the file hash param

    Returns the download URL for the timeline file
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

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


class RaceStatsViewSet(viewsets.ModelViewSet):
    """
    Returns the user's stats for the given race param
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    @action(
        detail=False,
        methods=['OPTIONS'],
    )
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


class UploadReplays(APIView):
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
        file_data = request.body

        def sha256sum(f):
            h = hashlib.sha256()
            h.update(f)
            return h.hexdigest()

        file_hash = sha256sum(file_data)
        replay_file = File(io.BufferedReader(io.BytesIO(file_data)))

        replay_file.name = f'{file_hash}.SC2Replay'
        replay_file.seek(0)

        try:
            error = process_file(replay_file, request, file_hash)
        except Exception as e:
            response = HttpResponseServerError(e)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization, content-type'
            return response

        if error == 'error':
            response = HttpResponseServerError()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        else:
            response = Response()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization, content-type'
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
        # profile_data_url = f'https://us.api.blizzard.com/sc2/player/{user_id}?access_token={access_token}'
        # profile_data = requests.get(profile_data_url)
        # profile_data = profile_data.json()

        # regions = {1: 'NA', 2: 'EU', 3: 'KR'}
        # profiles = {}

        # for profile in profile_data:
        #     if int(profile['regionId']) in profiles:
        #         profiles[int(profile['regionId'])]['profile_id'].append(int(profile['profileId']))
        #     else:
        #         profiles[int(profile['regionId'])] = {
        #             'profile_name': profile['name'],
        #             'region_name': regions[profile['regionId']],
        #             'profile_id': [int(profile['profileId'])],
        #             'realm_id': int(profile['realmId'])
        #         }

        authorized_account = BattlenetAccount(
            id=user_id,
            battletag=user_info['battletag'],
            user_account=current_account,
            region_profiles={}
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
