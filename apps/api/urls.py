from django.urls import path

from .authentication import ExternalLogin, ExternalLogout
from .authorization import BattlenetAuthorizationUrl, SetBattlenetAccount
from .feature_vote import FeatureVoteSet
from .pubsub import UploadReplay, VerifyReplaysViewset
from .replays import (
    ReplaySummaryViewset,
    RaceReplayViewSet,
    FetchReplayTimeline,
    FetchReplayFile,
    WriteReplaySet,
)
from .trends import RaceStatsViewSet, Stats
from .user import CheckUserInfo, AddUserProfile, ResendEmail

replay_download_link = FetchReplayFile.as_view({
    'get': 'download',
    'options': 'preflight',
})

verify_replays = VerifyReplaysViewset.as_view({
    'get': 'verify',
    'options': 'preflight',
})

replay_summary = ReplaySummaryViewset.as_view({
    'get': 'retrieve',
    'options': 'preflight',
})

user_replays = RaceReplayViewSet.as_view({
    'get': 'retrieve',
    'options': 'preflight',
})

user_replays_count = RaceReplayViewSet.as_view({
    'get': 'count',
    'options': 'preflight',
})

user_stats = RaceStatsViewSet.as_view({
    'get': 'retrieve',
    'options': 'preflight',
})

write_replay = WriteReplaySet.as_view({
    'post': 'write',
    'options': 'preflight',
})

feature_vote = FeatureVoteSet.as_view({
    'post': 'write',
    'get': 'fetch',
    'options': 'preflight',
})

app_name = 'api'
urlpatterns = [
    path('replays/verify/', verify_replays, name='verify_replays'),
    path('replays/summary/', replay_summary, name='replay_summary'),
    path('replays/<str:race>/', user_replays, name='race_replays'),
    path('replays/<str:race>/count/', user_replays_count, name='race_replays_count'),
    path('download/<str:file_hash>/', replay_download_link, name='replay_download'),
    path('replays/timeline/<str:file_hash>/', FetchReplayTimeline.as_view(), name='replay_timeline'),
    path('login/', ExternalLogin.as_view(), name='external_login'),
    path('logout/', ExternalLogout.as_view(), name='external_logout'),
    path('stats/', Stats.as_view(), name='user_stats'),
    path('stats/<str:race>/', user_stats, name='race_stats'),
    path('upload/', UploadReplay.as_view(), name='replay_upload'),
    path('upload/data/', write_replay, name='write_replay_data'),
    path('authorize/url/', BattlenetAuthorizationUrl.as_view(), name='battlenet_authorization_url'),
    path('authorize/code/', SetBattlenetAccount.as_view(), name='set_battlenet_account'),
    path('authorize/check/', CheckUserInfo.as_view(), name='ping_battlenet_account'),
    path('profile/', AddUserProfile.as_view(), name='add_user_profile'),
    path('resend/', ResendEmail.as_view(), name='resend_email'),
    path('vote/', feature_vote, name='feature_vote'),
]
