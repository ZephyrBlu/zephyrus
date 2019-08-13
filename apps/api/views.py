from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseNotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.user_profile.models import Replay, BattlenetAccount
from allauth.account.models import EmailAddress
from .models import ReplaySerializer
import requests


class ExternalLogin(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            data = {'username': username, 'password': password}
            token = requests.post(
                url="http://127.0.0.1:8000/api/token/",
                data=data
            )
            return Response(token.json())
        else:
            response = Response({'response': 'Login details invalid'})
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
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
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

        return Response(serialized_replays)


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
