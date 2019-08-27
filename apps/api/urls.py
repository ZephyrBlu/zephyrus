# from rest_framework.authtoken import views
from django.urls import path, include
from .views import (
    ExternalLogout,
    ExternalLogin,
    BattlenetAccountReplays,
    Stats,
    UploadReplays,
    BattlenetAuthorizationUrl,
    SetBattlenetAccount,
    CheckBattlenetAccount,
    # CustomToken,
)


app_name = 'api'
urlpatterns = [
    path('all/', BattlenetAccountReplays.as_view(), name='replay_list'),
    path('login/', ExternalLogin.as_view(), name='external_login'),
    path('logout/', ExternalLogout.as_view(), name='external_logout'),
    # path('token/', CustomToken.as_view()),
    path('stats/', Stats.as_view(), name='user_stats'),
    path('upload/', UploadReplays.as_view(), name='replay_upload'),
    path('authorize/url/', BattlenetAuthorizationUrl.as_view(), name='battlenet_authorization_url'),
    path('authorize/code/', SetBattlenetAccount.as_view(), name='set_battlenet_account'),
    path('authorize/check/', CheckBattlenetAccount.as_view(), name='ping_battlenet_account')
]
