from django.urls import path
from .views import ReplayList, Replay, LatestReplay

app_name = 'api'
urlpatterns = [
    path('api/all/', ReplayList.as_view(), name='replay_list'),
    path('api/<int:pk>/', Replay.as_view(), name='replay_specific'),
    path('api/recent/', LatestReplay.as_view(), name='replay_latest'),
]
