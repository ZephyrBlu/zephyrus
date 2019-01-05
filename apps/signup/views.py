from django.shortcuts import render
from django import forms
from usermanager.models import CustomUser, CustomManager
from django.contrib.auth import login, authenticate

def email_form(request, context=None):
    form = SignupForm()
    context['form'] = form
    return render(request, 'signup/signup.html', context)

def signedup(request):
    info = 'Thanks for signing up to Zephyrus!'
    heading = 'Zephyrus: Signed Up'
    title = 'Zephyrus | Signed Up'
    context = {'info': info,
               'heading': heading,
               'title': title
               }
    return render(request, 'signup/signup_complete.html', context)
