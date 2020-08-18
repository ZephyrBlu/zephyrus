import requests
import json

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from allauth.account.models import EmailAddress

from zephyrus.settings import FRONTEND_URL

from apps.user_profile.models import BattlenetAccount
from apps.user_profile.secret.production import CLIENT_ID, CLIENT_SECRET

from .permissions import IsOptionsPermission
from .authentication import IsOptionsAuthentication

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
            region_profiles=profiles,
            linked_at=timezone.now(),
        )
        authorized_account.save()

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response
