from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from apps.user_profile.models import AuthenticatedReplay, UnauthenticatedReplay, BattlenetAccount
from allauth.account.models import EmailAddress
from .models import ReplaySerializer


# returns all replays
class ReplayList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)
        replays = AuthenticatedReplay.objects.filter(battlenet_account_id=battle_net_id)

        serialized_replays = []
        for replay in list(replays):
            serializer = ReplaySerializer(replay)
            serialized_replays.append(serializer.data)

        return Response(serialized_replays)


# returns particular replay based on pk ID in database
class Replay(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    queryset = AuthenticatedReplay.objects.all()
    serializer_class = ReplaySerializer


# returns last uploaded replay
class LatestReplay(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        user_id = EmailAddress.objects.get(email=user.email)
        battle_net_id = BattlenetAccount.objects.get(user_account_id=user_id)

        replay = AuthenticatedReplay.objects.filter(battlenet_account_id=battle_net_id).latest('uploaded_at')
        serializer = ReplaySerializer(replay)
        return Response(serializer.data)


def verify_replays(request):
    user = request.user
    user_id = EmailAddress.objects.get(email=user.email)

    authenticated_accounts = BattlenetAccount.objects.filter(user_account_id=user_id)
    unauthenticated_replays = UnauthenticatedReplay.object.filter(user_account_id=user_id)

    for account in authenticated_accounts:
        for replay in unauthenticated_replays:
            if account.id == replay.player1_battlenet_id:
                authenticated_replay = AuthenticatedReplay(
                    file_hash=replay.file_hash,
                    battlenet_account=replay.account,
                    user_in_game_name='NEED TO ADD DATA TO UNAUTHENTICATED REPLAY TABLE',
                    opponent_in_game_name='NEED TO ADD DATA TO UNAUTHENTICATED REPLAY TABLE',
                    played_at=replay.played_at,
                    game_map=replay.game_map,
                    )
                authenticated_replay.save()
                replay.delete()

                # Add bucket object renaming script in here


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key
        })



