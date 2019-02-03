from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    path('replay-data/', views.return_replay_data, name='return_replay_data'),
]
