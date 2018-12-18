from django.urls import path, include
from . import views

app_name = 'site_structure'
urlpatterns = [
    path('home/', views.homepage, name='home'),
    path('upload/', views.upload, name='upload'),
    path('user/', views.user, name='user'),
    path('premium/', views.premium, name='premium'),
    path('signup/', views.MySignupView.as_view(), name='signup'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]