from rest_framework.authtoken import views
from django.urls import path
from .views import (
    ExternalLogin,
    BattlenetAccountReplays,
    AccountReplays,
    LatestReplay,
) # verify_replays


app_name = 'api'
urlpatterns = [
    path('all/', BattlenetAccountReplays.as_view(), name='replay_list'),
    path('login/', ExternalLogin.as_view(), name='external_login'),
    # path('recent/', LatestReplay.as_view(), name='replay_latest'),
    path('token/', views.obtain_auth_token),
    # path('verify/', verify_replays, name='verify_replays'),
]
