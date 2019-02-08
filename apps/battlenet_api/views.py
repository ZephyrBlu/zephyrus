from django.shortcuts import render, redirect
from apps.user_profile.models import BattlenetAccount
from allauth.account.models import EmailAddress
import requests


api_url = 'https://us.battle.net/'


def authentication_requests(request):
    if request.method == 'GET':
        if 'code' in request.GET:
            token_url = f'{api_url}oauth/token'
            auth_code = request.GET.get('code')
            redirect_uri = 'https://127.0.0.1:8000/authorize'
            client_id = '7868b58312e647819a2785e0ec7eeba1'
            client_secret = 'Ln4sR352JK2rlXUQ8HezmD97DPQ1Cc0C'
            data = {
                    'grant_type': 'authorization_code',
                    'code': auth_code,
                    'redirect_uri': redirect_uri,
                    'client_id': client_id,
                    'client_secret': client_secret
                    }
            info = requests.post(token_url, data=data)
            access_token = info.json()['access_token']

            user_info_url = f'{api_url}oauth/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            json_info = requests.get(user_info_url, headers=headers)
            user_info = json_info.json()
            current_account = EmailAddress.objects.get(email=request.user.email)

            authorized_account = BattlenetAccount(
                id=user_info['id'],
                battletag=user_info['battletag'],
                user_account=current_account
            )
            authorized_account.save()
            return redirect('/profile/')

        else:
            auth_url = f'{api_url}oauth/authorize'
            response_type = 'code'
            client_id = '7868b58312e647819a2785e0ec7eeba1'
            redirect_uri = 'https://127.0.0.1:8000/authorize'
            scope = 'sc2.profile'
            # state = <random string>
            url = f'{auth_url}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}'
            return redirect(url)
