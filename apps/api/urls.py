from django.urls import path
from .views import (
    ExternalLogout,
    ExternalLogin,
    RaceReplayViewSet,
    BattlenetAccountReplays,
    FetchReplayTimeline,
    RaceStatsViewSet,
    Stats,
    UploadReplays,
    BattlenetAuthorizationUrl,
    SetBattlenetAccount,
    CheckUserInfo,
    AddUserProfile,
    ResendEmail,
)

user_replays = RaceReplayViewSet.as_view({
    'get': 'retrieve',
    'options': 'preflight',
})

user_stats = RaceStatsViewSet.as_view({
    'get': 'retrieve',
    'options': 'preflight',
})

app_name = 'api'
urlpatterns = [
    path('replays/all/', BattlenetAccountReplays.as_view(), name='replay_list'),
    path('replays/<str:race>/', user_replays, name='race_replays'),
    path('replays/timeline/<str:file_hash>/', FetchReplayTimeline.as_view(), name='replay_timeline'),
    path('login/', ExternalLogin.as_view(), name='external_login'),
    path('logout/', ExternalLogout.as_view(), name='external_logout'),
    path('stats/', Stats.as_view(), name='user_stats'),
    path('stats/<str:race>/', user_stats, name='race_stats'),
    path('upload/', UploadReplays.as_view(), name='replay_upload'),
    path('authorize/url/', BattlenetAuthorizationUrl.as_view(), name='battlenet_authorization_url'),
    path('authorize/code/', SetBattlenetAccount.as_view(), name='set_battlenet_account'),
    path('authorize/check/', CheckUserInfo.as_view(), name='ping_battlenet_account'),
    path('profile/', AddUserProfile.as_view(), name='add_user_profile'),
    path('resend/', ResendEmail.as_view(), name='resend_email'),
]
