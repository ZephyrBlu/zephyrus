from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.contrib.auth import get_user_model, logout
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.debug import sensitive_variables

from rest_framework.response import Response
from rest_framework import viewsets

from allauth.account.models import EmailAddress
from allauth.account.adapter import get_adapter
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str, url_str_to_user_pk
from allauth.account import app_settings, signals

from zephyrus.settings import BACKEND_URL, FRONTEND_URL

from .permissions import IsOptionsPermission, IsPostPermission

INTERNAL_RESET_SESSION_KEY = "_password_reset_key"


class PasswordReset(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [IsOptionsPermission | IsPostPermission]

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'content-type'
        return response

    def reset(self, request):
        email = request.data['username']

        if not email:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'content-type'
            return response

        current_site = get_current_site(request)
        try:
            user_account = EmailAddress.objects.get(email=email)
            user = user_account.user
        except ObjectDoesNotExist:
            response = HttpResponseNotFound()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'content-type'
            return response

        # accounts must be verified in order to reset the password
        if not user_account.verified:
            response = HttpResponseForbidden()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'content-type'
            return response

        # send the password reset email
        temp_key = default_token_generator.make_token(user)
        pk_b36 = user_pk_to_url_str(user)
        url = f'{BACKEND_URL}/api/password/reset/key/{pk_b36}-{temp_key}/'
        context = {
            'current_site': current_site,
            'user': user,
            'password_reset_url': url,
            'request': request,
        }
        get_adapter(request).send_mail(
            'account/email/password_reset_key', email, context
        )

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'content-type'
        return response


class PasswordResetFromKey(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []

    def preflight(self, request, uidb36, key):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'content-type'
        return response

    def _get_reset_user(self, uidb36, key):
        User = get_user_model()

        try:
            pk = url_str_to_user_pk(uidb36)
            user = User.objects.get(pk=pk)
        except (ValueError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, key):
            return None
        return user

    @sensitive_variables('password1', 'password2')
    def reset(self, request, uidb36, key):
        # this is second request from frontend containing updated password
        if request.method == 'POST':
            session = SessionStore(session_key=request.data['sessionKey'])
        # this is initial request from reset password email
        else:
            session = request.session

        # if we've already stored the reset key, need to fetch it before continuing
        if key == INTERNAL_RESET_SESSION_KEY:
            password1 = request.data['password1']
            password2 = request.data['password2']

            if not password1 or not password2:
                response = HttpResponseBadRequest()
                response['Access-Control-Allow-Origin'] = FRONTEND_URL
                response['Access-Control-Allow-Headers'] = 'content-type'
                return response

            if password1 != password2:
                response = HttpResponse('401 Unauthorized', status=401)
                response['Access-Control-Allow-Origin'] = FRONTEND_URL
                response['Access-Control-Allow-Headers'] = 'content-type'
                return response

        if key == INTERNAL_RESET_SESSION_KEY:
            key = session.get(INTERNAL_RESET_SESSION_KEY, '')
            user = self._get_reset_user(uidb36, key)
            if user is None:
                response = HttpResponse('401 Unauthorized', status=401)
                response['Access-Control-Allow-Origin'] = FRONTEND_URL
                response['Access-Control-Allow-Headers'] = 'content-type'
                return response

            # In the event someone clicks on a password reset link
            # for one account while logged into another account,
            # logout of the currently logged in account.
            if (
                request.user.is_authenticated
                and request.user.pk != user.pk
            ):
                logout(user)
                session[INTERNAL_RESET_SESSION_KEY] = key

            # set the new password
            adapter = get_adapter()
            adapter.set_password(user, password1)

            # allauth stuff
            # https://github.com/pennersr/django-allauth/blob/master/allauth/account/views.py#L785
            signals.password_reset.send(
                sender=user.__class__,
                request=request,
                user=user,
            )

            response = Response()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'content-type'
            return response
        elif request.method == 'POST' and key != INTERNAL_RESET_SESSION_KEY:
            response = HttpResponse('401 Unauthorized', status=401)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'content-type'
            return response
        else:
            session[INTERNAL_RESET_SESSION_KEY] = key
            return redirect(f'{FRONTEND_URL}/password-reset/{uidb36}-{INTERNAL_RESET_SESSION_KEY}?session={session.session_key}')
