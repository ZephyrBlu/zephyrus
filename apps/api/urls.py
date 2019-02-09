from django.urls import path
from .views import ReplayList, Replay, LatestReplay

app_name = 'api'
urlpatterns = [
    path('all/', ReplayList.as_view(), name='replay_list'),
    path('<int:pk>/', Replay.as_view(), name='replay_specific'),
    path('recent/', LatestReplay.as_view(), name='replay_latest'),
]
