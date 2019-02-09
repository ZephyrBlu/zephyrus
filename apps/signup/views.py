from django.shortcuts import render, redirect
from allauth.account.views import SignupView


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
        return redirect('login/')


def signedup(request):
    info = 'Thanks for signing up to Zephyrus!'
    heading = 'Zephyrus: Signed Up'
    title = 'Zephyrus | Signed Up'
    context = {'info': info,
               'heading': heading,
               'title': title
               }
    return render(request, 'signup/signup_complete.html', context)


# def email_form(request, context=None):
#     form = SignupForm()
#     context['form'] = form
#     return render(request, 'signup/signup.html', context)
#
#

