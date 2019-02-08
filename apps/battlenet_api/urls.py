from django.urls import path
from . import views

app_name = 'battlenet_api'
urlpatterns = [
    path('authorize/', views.authentication_requests, name='authorize'),
]
