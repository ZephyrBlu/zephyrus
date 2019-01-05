from django.shortcuts import render, redirect
from apps.signup.views import email_form, signedup
from apps.upload_file.views import upload_form
from allauth.account.views import SignupView, LoginView

def homepage(request):
    info = 'This is the homepage'
    heading = 'Welcome'
    title = 'Zephyrus | Home'
    active = 'home'
    context = {
            'info':info,
            'heading':heading,
            'title': title,
            'active': active
    }
    return render(request, 'site_structure/index.html', context)

def upload(request):
    info = 'This is the upload page'
    heading = 'Upload'
    title = 'Zephyrus | Upload'
    active = 'upload'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'upload_file/upload_form.html', context)
    #return upload_form(request, context)

def user_profile(request):
    info = 'This is the User Profile page'
    heading = 'Profile'
    title = 'Zephyrus | Profile'
    active = 'profile'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'user_profile/profile.html', context)

def premium(request):
    info = 'This is the premium sign up page'
    heading = 'Premium'
    title = 'Zephyrus | Premium'
    active = 'premium'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'site_structure/index.html', context)

class MySignupView(SignupView):
    def get_context_data(self, **kwargs):
        context = super(MySignupView, self).get_context_data(**kwargs)
        info = 'This is the sign up page'
        heading = 'Sign Up'
        title = 'Zephyrus | Sign Up'
        active = 'signup'
        context['info'] = info
        context['heading'] = heading
        context['title'] = title
        context['active'] = active
        return context

    def form_valid(self, form):
        self.user = form.save(self.request)
        return signedup(self.request)

class MyLoginView(LoginView):
    template_name = "login/login.html"

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        info = 'This is the login page'
        heading = 'Login'
        title = 'Zephyrus | Login'
        active = 'login'
        context['info'] = info
        context['heading'] = heading
        context['title'] = title
        context['active'] = active
        return context

def about(request):
    info = 'This is the about page'
    heading = 'About Us'
    title = 'Zephyrus | About Us'
    active = 'about'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'site_structure/index.html', context)

def contact(request):
    info = 'This is the contact page'
    heading = 'Contact Us'
    title = 'Zephyrus | Contact Us'
    active = 'contact'
    context = {
        'info': info,
        'heading': heading,
        'title': title,
        'active': active
    }
    return render(request, 'site_structure/index.html', context)
