from django.urls import path
from .views import ReplayList, Replay, LatestReplay

app_name = 'api'
urlpatterns = [
    path('replay/all/', ReplayList.as_view(), name='replay_list'),
    path('replay/<int:pk>/', Replay.as_view(), name='replay_specific'),
    path('replay/recent/', LatestReplay.as_view(), name='replay_latest'),
]
