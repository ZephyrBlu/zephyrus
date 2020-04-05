from django.urls import path
from .views import replay_page

app_name = 'site_structure'
urlpatterns = [
    path('replay/<str:base64_url>/', replay_page, name='replay_page'),
]
