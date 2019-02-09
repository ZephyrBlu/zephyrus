from allauth.account.views import LoginView


class MyLoginView(LoginView):
    template_name = 'login/login.html'

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
