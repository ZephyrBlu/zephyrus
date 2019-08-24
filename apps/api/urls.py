from rest_framework.authtoken import views
from django.urls import path, include
from .views import (
    ExternalLogout,
    ExternalLogin,
    BattlenetAccountReplays,
    Stats,
    UploadReplays,
)
from apps.user_profile.views import battlenet_authorization


app_name = 'api'
urlpatterns = [
    path('all/', BattlenetAccountReplays.as_view(), name='replay_list'),
    path('login/', ExternalLogin.as_view(), name='external_login'),
    path('logout/', ExternalLogout.as_view(), name='external_logout'),
    path('token/', views.obtain_auth_token),
    path('stats/', Stats.as_view(), name='user_stats'),
    path('upload/', UploadReplays.as_view(), name='replay_upload'),
    path('authorize/', battlenet_authorization),
]
