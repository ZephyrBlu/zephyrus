from django.urls import path
from .views import AccountReplays, LatestReplay, CustomAuthToken # verify_replays


app_name = 'api'
urlpatterns = [
    path('all/', AccountReplays.as_view(), name='replay_list'),
    path('recent/', LatestReplay.as_view(), name='replay_latest'),
    path('token/', CustomAuthToken.as_view()),
    # path('verify/', verify_replays, name='verify_replays'),
]
