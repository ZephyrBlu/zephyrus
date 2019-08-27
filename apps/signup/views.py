from django.shortcuts import redirect
from allauth.account.views import SignupView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


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

        user = authenticate(self.request, username=username, password=password)
        Token.objects.get_or_create(user=user)
        return redirect('https://app.zephyrus.gg/')
