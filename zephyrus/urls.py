"""zephyrus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from allauth.account import views as allauth_views


def to_signup(request):
    return redirect('/signup/')


allauth_patterns = ([
    path('signup/', allauth_views.signup, name="account_signup"),
], 'allauth.account')


urlpatterns = [
    path('', to_signup),
    path('api/', include('apps.api.urls')),
    path('signup/', include('apps.signup.urls', namespace='signup')),
    path('confirm/<str:key>', allauth_views.confirm_email, name="account_confirm_email"),
    path('/', include(allauth_patterns)),
]
