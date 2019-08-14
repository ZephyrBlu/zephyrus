from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseNotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from rest_framework.authtoken.models import Token
from .models import ReplaySerializer
import requests
import json


class ExternalLogin(APIView):
    authentication_classes = []
    permission_classes = []

    def options(self, request):
        response = Response({'response': 'success'})
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)
        print(user)
        print(user.is_authenticated)

        if user is not None:
            login(request, user)
            print(user.last_login)
            print(vars(request))
            data = {'username': username, 'password': password}
            token = requests.post(
                url="http://127.0.0.1:8000/api/token/",
                data=data
            )
            response = Response(token.json())
            response['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            response = Response({'response': 'Login details invalid'})
            response['Access-Control-Allow-Origin'] = '*'
            return response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def external_logout(request):
    print(request.user)
    logout(request)
    response = Response({'response': 'Successfully logged out'})
    response['Access-Control-Allow-Origin'] = '*'
    return response


# returns particular replay based on pk ID in database
class AccountReplays(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
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
    permission_classes = ([]) #IsAuthenticated,)

    def options(self, request):
        print(vars(request))
        print(request.user)
        print(request.user.is_authenticated)
        response = Response({'response': 'successful preflight'})
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def post(self, request, format=None):
        print(request.body)
        request_token = json.loads(request.body)['auth']
        print(request_token)
        user_token = Token.objects.get(key=request_token)
        print(user_token)
        user = EmailAddress.objects.get(id=user_token.user_id)
        print(vars(user))
        print(user.last_login)

        user_id = user.email
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)

        if not battle_net_id:
            return HttpResponseNotFound

        replay_queryset = Replay.objects.filter(battlenet_account_id=battle_net_id)
        serialized_replays = []
        for replay in list(replay_queryset):
            serializer = ReplaySerializer(replay)
            serialized_replays.append(serializer.data)

        response = Response(serialized_replays)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def get(self, request, format=None):
        print(request.user)
        print(request.user.is_authenticated)
        print(request.auth)
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)

        if not battle_net_id:
            return HttpResponseNotFound

        replay_queryset = Replay.objects.filter(battlenet_account_id=battle_net_id)
        serialized_replays = []
        for replay in list(replay_queryset):
            serializer = ReplaySerializer(replay)
            serialized_replays.append(serializer.data)

        response = Response(serialized_replays)
        response['Access-Control-Allow-Origin'] = '*'
        return response


# returns last uploaded replay
class LatestReplay(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)

        replay = Replay.objects.filter(battlenet_account_id=battle_net_id).latest('uploaded_at')
        serializer = ReplaySerializer(replay)
        return Response(serializer.data)


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
