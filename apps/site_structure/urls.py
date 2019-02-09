from django.urls import path, include
from . import views

app_name = 'site_structure'
urlpatterns = [
    path('home/', views.homepage, name='home'),
    path('premium/', views.premium, name='premium'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
