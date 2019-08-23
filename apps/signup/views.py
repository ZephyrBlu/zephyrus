from django.shortcuts import redirect
from allauth.account.views import SignupView
import requests


class MySignupView(SignupView):
    def get_context_data(self, **kwargs):
        context = {}
        context['form'] = super(SignupView, self).get_context_data(**kwargs)['form']
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
        username = form.cleaned_data['email']
        password = form.cleaned_data['password1']
        requests.post("http://127.0.0.1:8000/api/token/", data={"username": username, "password": password})
        return redirect('http://localhost:5000/')
