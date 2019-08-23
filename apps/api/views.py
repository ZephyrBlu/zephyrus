from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission, IsAuthenticated
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from .models import ReplaySerializer
from django.core.files import File
from django.core.files.storage import default_storage
from apps.process_replays.views import parse_replay
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
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
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
                url="http://127.0.0.1:8000/api/token/",
                data=data
            )
            if token_response.status_code != 200:
                return Response(status=token_response.status_code)
            else:
                response = Response(token_response.json())
                response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
                return response
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
            return response


class ExternalLogout(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        logout(request)
        response = Response()
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
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
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)

        if not battle_net_id:
            response = HttpResponseNotFound
            response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
            response['Access-Control-Allow-Headers'] = 'authorization'
            return response

        replay_queryset = Replay.objects.filter(battlenet_account_id=battle_net_id)
        serialized_replays = []
        for replay in list(replay_queryset):
            serializer = ReplaySerializer(replay)
            serialized_replays.append(serializer.data)

        serialized_replays.sort(key=lambda x: x['played_at'], reverse=True)
        response = Response(serialized_replays)
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class Stats(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
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
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class UploadReplays(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
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
        response['Access-Control-Allow-Origin'] = 'http://localhost:5000'
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


def sha256sum(f):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    for n in iter(lambda: f.readinto(mv), 0):
        h.update(mv[:n])
    return h.hexdigest()


def process_file(replay_file, request, file_hash):
    user = request.user

    players, summary_stats, metadata = parse_replay(replay_file)

    if players is None:
        return

    player_summary = {}
    player_summary[1] = vars(players[1])
    player_summary[2] = vars(players[2])

    filename = replay_file.name

    replay_query = Replay.objects.filter(file_hash=file_hash)
    user_account = EmailAddress.objects.get(user=user)
    user_battlenet_accounts = BattlenetAccount.objects.filter(user_account=user_account)

    match_region = players[1].region_id

    duplicate_replay = False
    if replay_query:
        duplicate_replay = True

    if not duplicate_replay:
        profile_ids = [players[1].profile_id, players[2].profile_id]
        kwargs = {f'region_profiles__{match_region}__profile_id__in': profile_ids}
        if user_battlenet_accounts:
            try:
                player_battlenet_account = user_battlenet_accounts.get(**kwargs)
            except ObjectDoesNotExist:
                player_battlenet_account = None
        else:
            player_battlenet_account = None
        if player_battlenet_account:
            bucket_path = f'{user.email}/{player_battlenet_account.battletag}/{filename}'

            player_profile_id = player_battlenet_account.region_profiles[str(match_region)]['profile_id']
            if players[metadata['winner']].profile_id == player_profile_id:
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
            match_data=summary_stats,
            match_length=metadata['game_length'],
            played_at=metadata['time_played_at'],
            map=metadata['map'],
            region_id=match_region,
            win=win
        )
        replay.save()

        file_contents = replay_file.open(mode='rb')
        current_replay = default_storage.open(bucket_path, 'w')
        current_replay.write(file_contents.read())
        current_replay.close()
    else:
        pass
