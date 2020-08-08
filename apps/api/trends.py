import json

from django.http import (
    HttpResponseNotFound,
    HttpResponseBadRequest,
)

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from allauth.account.models import EmailAddress

from zephyrus.settings import FRONTEND_URL

from apps.user_profile.models import Replay, BattlenetAccount

from .utils.analyze_trends import analyze_trends
from .permissions import IsOptionsPermission


class RaceTrendsViewSet(viewsets.ModelViewSet):
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
            battlenet_account = BattlenetAccount.objects.filter(
                user_account_id=user_id
            ).order_by('-linked_at').first()
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
