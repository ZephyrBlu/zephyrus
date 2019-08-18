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
import requests
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


# def verify_replays(request):
#     user = request.user
#     user_id = EmailAddress.objects.get(email=user.email)
#
#     authenticated_accounts = BattlenetAccount.objects.filter(user_account_id=user_id)
#     unauthenticated_replays = Replay.object.filter(user_account_id=user_id)
#
#     for account in authenticated_accounts:
#         for replay in unauthenticated_replays:
#             if account.id == replay.player1_battlenet_id:
#                 authenticated_replay = AuthenticatedReplay(
#                     file_hash=replay.file_hash,
#                     battlenet_account=replay.account,
#                     user_in_game_name='NEED TO ADD DATA TO UNAUTHENTICATED REPLAY TABLE',
#                     opponent_in_game_name='NEED TO ADD DATA TO UNAUTHENTICATED REPLAY TABLE',
#                     played_at=replay.played_at,
#                     map=replay.game_map,
#                     )
#                 authenticated_replay.save()
#                 replay.delete()
#
#                 # Add bucket object renaming script in here
