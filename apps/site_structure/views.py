from django.shortcuts import render, redirect
from apps.signup.views import email_form
from apps.upload_file.views import upload_form
from allauth.account.views import SignupView

def homepage(request):
    info = 'This is the homepage'
    heading = 'Welcome to Zephyrus'
    title = 'Zephyrus | Home'
    context = {
            'info':info,
            'heading':heading,
            'title': title
    }
    return render(request, 'site_structure/index.html', context)

def upload(request):
    info = 'This is the upload page'
    heading = 'Zephyrus: Upload'
    title = 'Zephyrus | Upload'
    context = {
        'info': info,
        'heading': heading,
        'title': title
    }
    return upload_form(request, context)

def user(request):
    info = 'This is the user overview'
    heading = 'Zephyrus: User Overview'
    title = 'Zephyrus | User Overview'
    context = {
        'info': info,
        'heading': heading,
        'title': title
    }
    return render(request, 'site_structure/index.html', context)

def premium(request):
    info = 'This is the premium sign up page'
    heading = 'Zephyrus: Sign up for Premium'
    title = 'Zephyrus | Premium'
    context = {
        'info': info,
        'heading': heading,
        'title': title
    }
    return render(request, 'site_structure/index.html', context)

class MySignupView(SignupView):
    def get_context_data(self, **kwargs):
        context = super(MySignupView, self).get_context_data(**kwargs)
        info = 'This is the sign up page'
        heading = 'Zephyrus: Sign Up'
        title = 'Zephyrus | Sign Up'
        context['info'] = info
        context['heading'] = heading
        context['title'] = title
        return context

def about(request):
    info = 'This is the about page'
    heading = 'Zephyrus: About Us'
    title = 'Zephyrus | About Us'
    context = {
        'info': info,
        'heading': heading,
        'title': title
    }
    return render(request, 'site_structure/index.html', context)

def contact(request):
    info = 'This is the contact page'
    heading = 'Zephyrus: Contact Us'
    title = 'Zephyrus | Contact Us'
    context = {
        'info': info,
        'heading': heading,
        'title': title
    }
    return render(request, 'site_structure/index.html', context)
