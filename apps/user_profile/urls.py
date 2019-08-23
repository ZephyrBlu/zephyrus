from django.urls import path
from . import views

app_name = 'user_profile'
urlpatterns = [
    path('authorize/', views.authentication_requests, name='authorize'),
    path('authorization/', views.need_authorization, name='require-authorization'),
]
