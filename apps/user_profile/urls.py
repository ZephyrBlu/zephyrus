from django.urls import path
from . import views

app_name = 'user_profile'
urlpatterns = [
    path('', views.overview, name='overview'),
    path('analysis/', views.analysis, name='analysis'),
    path('replays/', views.replays, name='replays'),
]