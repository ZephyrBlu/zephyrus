from rest_framework.authtoken.models import Token
from allauth.account.models import EmailAddress
from apps.user_profile.models import BattlenetAccount
from .find_main_race import find_main_race


def get_user_info(user):
    user_account = EmailAddress.objects.get(email=user.email)
    user_battlenet = BattlenetAccount.objects.filter(user_account_id=user.email)
    if user_battlenet:
        battlenet_accounts = []
        for account in user_battlenet:
            current_account = {
                'battletag': account.battletag,
                'profiles': account.region_profiles,
            }
            battlenet_accounts.append(current_account)
    else:
        battlenet_accounts = None
    token = Token.objects.get(user=user)
    main_race = find_main_race(user)

    return {
        'user': {
            'email': user.email,
            'verified': user_account.verified,
            'battlenet_accounts': battlenet_accounts,
            'token': token.key,
            'main_race': main_race,
        }
    }
