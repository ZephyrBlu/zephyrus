from django.urls import path
from . import views

app_name = 'user_profile'
urlpatterns = [
    path('', views.overview, name='overview'),
    path('analysis/', views.analysis, name='analysis'),
    path('replays/', views.replays, name='replays'),
    path('authorize/', views.authentication_requests, name='authorize'),
    path('authorization/', views.need_authorization, name='require-authorization'),
    path('new/', views.updated_profile, name='updated-profile'),
]
