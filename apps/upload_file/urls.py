from django.urls import path
from . import views

app_name = 'upload_file'
urlpatterns = [
    path('', views.upload_form, name='upload_form'),
]
