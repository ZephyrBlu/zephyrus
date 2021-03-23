import json

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseBadRequest

from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from allauth.account.utils import send_email_confirmation

from zephyrus.settings import FRONTEND_URL

from .utils.get_user_info import get_user_info
from .permissions import IsOptionsPermission, IsPostPermission


class IsOptionsAuthentication(BaseAuthentication):
    """
    Allows preflight requests to complete
    Used for CORS requests in development
    """
    def authenticate(self, request):
        if request.method == 'OPTIONS':
            return None
        else:
            raise AuthenticationFailed


class ExternalLogin(APIView):
    """
    Handles user logins from the /login API endpoint

    If a user does not have a verified email, a verification
    email is sent.

    The user's account information, Token and main race are sent in the response
    """
    authentication_classes = []
    permission_classes = [IsOptionsPermission | IsPostPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
        return response

    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            token = Token.objects.get(user=user)
            user_info = get_user_info(user, token.key)

            if not user_info['user']['verified']:
                send_email_confirmation(request, user)

            response = Response(user_info)
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
            return response
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'cache-control, content-type'
            return response


class ExternalLogout(APIView):
    """
    Handles user logouts from the /logout API endpoint
    """
    # authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    # permission_classes = [IsAuthenticated | IsOptionsPermission]
    authentication_classes = []
    permission_classes = []

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        logout(request)
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response
