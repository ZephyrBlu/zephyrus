from django.shortcuts import redirect
from allauth.account.models import EmailAddress
from apps.user_profile.models import BattlenetAccount
from .secret import CLIENT_ID, CLIENT_SECRET
import requests


oauth_api_url = 'https://us.battle.net'


def battlenet_authorization(request):
    if 'code' in request.GET:
        token_url = f'{oauth_api_url}/oauth/token'
        auth_code = request.GET.get('code')
        redirect_uri = 'https://zephyrus.gg/api/authorize/'
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
            profiles[int(profile['regionId'])] = {
                'profile_name': profile['name'],
                'region_name': regions[profile['regionId']],
                'profile_id': int(profile['profileId']),
                'realm_id': int(profile['realmId'])
            }

        authorized_account = BattlenetAccount(
            id=user_id,
            battletag=user_info['battletag'],
            user_account=current_account,
            region_profiles=profiles
        )
        authorized_account.save()
    else:
        auth_url = f'{oauth_api_url}/oauth/authorize'
        response_type = 'code'
        client_id = CLIENT_ID
        redirect_uri = 'https://zephyrus.gg/api/authorize/'
        scope = 'sc2.profile'
        url = f'{auth_url}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}'
        return redirect(url)
