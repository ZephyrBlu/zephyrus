from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, HttpResponseServerError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.authtoken.models import Token
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from .models import ReplaySerializer
from django.core.files import File
from apps.process_replays.views import process_file
from apps.user_profile.secret import CLIENT_ID, CLIENT_SECRET
import requests
from .utils.trends import main as analyze_trends
import io
import hashlib
import json
import copy
import datetime
from math import floor
from zephyrus.settings import API_KEY, FRONTEND_URL


class IsOptionsAuthentication(BaseAuthentication):
    """
    Allows preflight requests to complete
    Used for CORS requests in development
    """
    def authenticate(self, request):
        if request.method == 'OPTIONS':
            return None
        else:
            raise AuthenticationFailed


class IsOptionsPermission(BasePermission):
    """
    Allows preflight requests to complete
    Used for CORS requests in development
    """
    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        else:
            return False


class IsPostPermission(BasePermission):
    """
    Allows preflight requests to complete
    Used for CORS requests in development
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        else:
            return False


class ExternalLogin(APIView):
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
            send_email_confirmation(request, user)
            token = Token.objects.get(user=user)

            response = Response({
                'token': token.key,
                'api_key': API_KEY,
            })
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
            return response
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
            return response


class ExternalLogout(APIView):
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


# returns particular replay based on pk ID in database
class AccountReplays(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def get(self, request):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)

        replay_queryset = Replay.objects.filter(user_account=user_id)
        serialized_replays = []
        for replay in list(replay_queryset):
            serializer = ReplaySerializer(replay)
            serialized_replays.append(serializer.data)

        return HttpResponse(serialized_replays)


# returns particular replay based on pk ID in database
class BattlenetAccountReplays(APIView):
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
            battlenet_account = BattlenetAccount.objects.get(user_account_id=user_id)
        else:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        replay_queryset = Replay.objects.filter(battlenet_account_id=battlenet_account)

        serialized_replays = []
        replay_queryset = list(replay_queryset)
        replay_queryset.sort(key=lambda x: x.played_at, reverse=True)
        limited_queryset = replay_queryset[:100]

        for replay in limited_queryset:
            date = replay.played_at
            days = datetime.timedelta(
                seconds=datetime.datetime.timestamp(datetime.datetime.now()) - datetime.datetime.timestamp(date)
            ).days
            if days != -1:
                weeks = int(round(days / 7, 0))
                months = int(floor(weeks / 4))
            else:
                weeks = 0
                months = 0

            if months > 0:
                if weeks - (months * 4) == 0:
                    date_diff = f'{months}m'
                else:
                    date_diff = f'{months}m'  # *{weeks - (months * 4)}/4*'
            elif weeks > 0:
                date_diff = f'{weeks}w'
            else:
                if days == -1:
                    date_diff = 'Today'
                elif days == 1:
                    date_diff = 'Yesterday'
                else:
                    date_diff = f'{days}d'

            serializer = ReplaySerializer(replay)
            serializer = copy.deepcopy(serializer.data)
            serializer['played_at'] = date_diff

            new_serializer = {}
            for stat, info in serializer.items():
                if stat == 'match_data':
                    new_serializer['match_data'] = {}
                    for name, values in info.items():
                        if type(values) is dict and 'minerals' in values:
                            for resource, value in values.items():
                                new_serializer[stat][f'{name}_{resource}'] = value
                        else:
                            new_serializer[stat][name] = values
                else:
                    new_serializer[stat] = info
            serializer = new_serializer
            serialized_replays.append(serializer)

        response = Response(serialized_replays)
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

        trend_data = analyze_trends(account_replays, battlenet_id_list)

        response = Response(json.dumps(trend_data))
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class UploadReplays(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        return response

    def post(self, request):
        file_data = request.body
        f = io.BufferedReader(io.BytesIO(file_data))
        replay_file = File(f)

        file_hash = sha256sum(replay_file)

        replay_file.name = f'{file_hash}.SC2Replay'
        replay_file.seek(0)
        error = process_file(replay_file, request, file_hash)

        if error == 'error':
            response = HttpResponseServerError()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        else:
            response = Response()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization, content-type'
        return response


def sha256sum(f):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: f.readinto(mv), 0):
        h.update(mv[:n])
    return h.hexdigest()


oauth_api_url = 'https://us.battle.net'


class BattlenetAuthorizationUrl(APIView):
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
        profile_data = profile_data.json()

        regions = {1: 'NA', 2: 'EU', 3: 'KR'}
        profiles = {}

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


class CheckBattlenetAccount(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user

        battlenet_accounts = BattlenetAccount.objects.filter(user_account=user.email)

        if len(battlenet_accounts) > 0:
            response = Response()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
        else:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
        return response
