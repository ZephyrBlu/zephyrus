from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission, IsAuthenticated
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from .models import ReplaySerializer
from django.core.files import File
from apps.process_replays.views import process_file
from apps.user_profile.views import battlenet_authorization
from .utils.trends import main as analyze_trends
import requests
import io
import hashlib
import json


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
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
        return response

    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            data = {'username': username, 'password': password}
            token_response = requests.post(
                url="https://zephyrus.gg/api/token/",
                data=data
            )
            if token_response.status_code != 200:
                return Response(status=token_response.status_code)
            else:
                response = Response(token_response.json())
                response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
                return response
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
            return response


class ExternalLogout(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        logout(request)
        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
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
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)

        if not battle_net_id:
            response = HttpResponseNotFound
            response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        replay_queryset = Replay.objects.filter(battlenet_account_id=battle_net_id)
        serialized_replays = []
        for replay in list(replay_queryset):
            serializer = ReplaySerializer(replay)
            serialized_replays.append(serializer.data)

        serialized_replays.sort(key=lambda x: x['played_at'], reverse=True)
        response = Response(serialized_replays)
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class Stats(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battlenet_account = BattlenetAccount.objects.get(user_account_id=user_id)

        account_replays = Replay.objects.filter(battlenet_account=battlenet_account)

        battlenet_id_list = []
        for region_id, info in battlenet_account.region_profiles.items():
            battlenet_id_list.append(info['profile_id'])

        trend_data = analyze_trends(account_replays, battlenet_id_list)

        response = Response(json.dumps(trend_data))
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class UploadReplays(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def post(self, request):
        file_data = request.body
        f = io.BufferedReader(io.BytesIO(file_data))
        replay_file = File(f)

        file_hash = sha256sum(replay_file)

        replay_file.name = f'{file_hash}.SC2Replay'
        replay_file.seek(0)
        process_file(replay_file, request, file_hash)

        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


def sha256sum(f):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: f.readinto(mv), 0):
        h.update(mv[:n])
    return h.hexdigest()


class BattlenetAuthorization(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        battlenet_authorization(request)

        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class CheckBattlenetAccount(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user

        battlenet_accounts = BattlenetAccount.objects.filter(user_account=user.email)

        if battlenet_accounts.exists():
            response = Response()
            response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
            response['Access-Control-Allow-Headers'] = 'authorization'
        else:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = 'https://app.zephyrus.gg'
            response['Access-Control-Allow-Headers'] = 'authorization'
        return response
