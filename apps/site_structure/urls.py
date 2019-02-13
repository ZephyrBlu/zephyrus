from django.urls import path, include
from . import views

app_name = 'site_structure'
urlpatterns = [
    path('landing-page/', views.landing_page, name='landingpage'),
    path('home/', views.homepage, name='home'),
    path('premium/', views.premium, name='premium'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
