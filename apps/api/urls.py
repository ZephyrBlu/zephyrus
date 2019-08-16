from rest_framework.authtoken import views
from django.urls import path
from .views import (
    ExternalLogout,
    ExternalLogin,
    BattlenetAccountReplays,
)  # verify_replays


app_name = 'api'
urlpatterns = [
    path('all/', BattlenetAccountReplays.as_view(), name='replay_list'),
    path('login/', ExternalLogin.as_view(), name='external_login'),
    path('logout/', ExternalLogout.as_view(), name='external_logout'),
    path('token/', views.obtain_auth_token),
    # path('verify/', verify_replays, name='verify_replays'),
]
