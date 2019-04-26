from django.shortcuts import render, redirect
from allauth.account.models import EmailAddress
from apps.user_profile.models import BattlenetAccount
from django.contrib.auth.decorators import user_passes_test
import requests


api_url = 'https://us.battle.net/'


def updated_profile(request):
    return render(request, 'user_profile/profile-redesign.html', {'active': 'profile'})


def need_authorization(request):
    return render(request, 'user_profile/profile.html', {'active': 'profile'})


def authentication_requests(request):
    if request.method == 'GET':
        if 'code' in request.GET:
            token_url = f'{api_url}oauth/token'
            auth_code = request.GET.get('code')
            redirect_uri = 'https://127.0.0.1:8000/profile/authorize'
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
            return redirect('/upload/')

        else:
            auth_url = f'{api_url}oauth/authorize'
            response_type = 'code'
            client_id = '7868b58312e647819a2785e0ec7eeba1'
            redirect_uri = 'https://127.0.0.1:8000/profile/authorize'
            scope = 'sc2.profile'
            # state = <random string>
            url = f'{auth_url}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}'
            return redirect(url)


def battlenet_authorized(user):
    account = EmailAddress.objects.get(email=user.email)
    battletag_queryset = BattlenetAccount.objects.filter(user_account_id=account.id)
    if battletag_queryset:
        return True
    else:
        return False


# implement class based view for profile sections
@user_passes_test(battlenet_authorized, login_url='/profile/authorization/', redirect_field_name=None)
def overview(request):
    profile_active = 'overview'
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    auth = 'Authorize'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active,
        'profile_active': profile_active,
        'auth': auth
    }
    return render(request, 'user_profile/profile.html', context)


@user_passes_test(battlenet_authorized, login_url='/profile/authorization/', redirect_field_name=None)
def analysis(request):
    profile_active = 'analysis'
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active,
        'profile_active': profile_active
    }
    return render(request, 'user_profile/profile.html', context)


@user_passes_test(battlenet_authorized, login_url='/profile/authorization/', redirect_field_name=None)
def replays(request):
    profile_active = 'replays'
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active,
        'profile_active': profile_active
    }
    return render(request, 'user_profile/profile.html', context)
