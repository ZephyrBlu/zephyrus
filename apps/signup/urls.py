from django.urls import path
from . import views

app_name = 'signup'
urlpatterns = [
    path('', views.MySignupView.as_view(), name='signup'),
    # path('complete/', views.signedup, name='signedup'),
]
