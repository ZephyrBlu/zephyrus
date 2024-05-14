from django.urls import path
from .views import landing_page, replay_page

app_name = 'site_structure'
urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('replay/<str:base64_url>/', replay_page, name='replay_page'),
]
