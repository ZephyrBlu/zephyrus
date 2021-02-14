import json

from django.core.mail import send_mail
from django.http import HttpResponseBadRequest

from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from allauth.account.utils import send_email_confirmation

from zephyrus.settings import FRONTEND_URL

from apps.user_profile.models import BattlenetAccount, Feedback

from .utils.get_user_info import get_user_info
from .utils.parse_profile import parse_profile
from .permissions import IsOptionsPermission
from .authentication import IsOptionsAuthentication


class CheckUserInfo(APIView):
    """
    Handles checking if a user has at least 1 battlenet account linked
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        token = request.auth
        user_info = get_user_info(user, token.key)

        response = Response(user_info)
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class AddUserProfile(APIView):
    """
    Handles validating, parsing and adding game profiles
    """
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def post(self, request):
        user = request.user

        user_profile_url = request.body.decode('utf-8')
        profile_data = parse_profile(user_profile_url)

        if profile_data:
            # save data to user model

            user_battlenet_account = BattlenetAccount.objects.filter(
                user_account_id=user.email,
            ).order_by('-linked_at').first()

            region_id = list(profile_data.keys())[0]
            new_profile_id = profile_data[region_id]['profile_id'][0]

            if region_id in user_battlenet_account.region_profiles:
                current_profile_id = user_battlenet_account.region_profiles[region_id]['profile_id']
                if new_profile_id not in current_profile_id:
                    current_profile_id.append(new_profile_id)
            else:
                user_battlenet_account.region_profiles.update(profile_data)
            user_battlenet_account.save()

            response = Response()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
        else:
            response = HttpResponseBadRequest()
            response['Access-Control-Allow-Origin'] = FRONTEND_URL
            response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class UserFeedback(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def preflight(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def write(self, request):
        feedback = json.loads(request.body)
        feedback_text = feedback['feedback']
        feedback_type = feedback['type']

        if len(feedback_text) >= 10 and feedback_type.upper() in ['ISSUE', 'SUGGESTION']:
            new_feedback = Feedback(
                user_account_id=request.user.email,
                feedback=feedback_text[:300],
                feedback_type=feedback_type[0].upper(),
            )
            new_feedback.save()

            feedback_message = f'''
            Feedback Type: {feedback_type}
            User: {request.user.email}
            Message: {feedback_text}
            '''
            send_mail(
                'New Suggestion/Issue Submitted',
                feedback_message,
                'hello@zephyrus.gg',
                ['hello@zephyrus.gg'],
            )
            response = Response()
        else:
            response = HttpResponseBadRequest()

        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response


class ResendEmail(APIView):
    authentication_classes = [TokenAuthentication, IsOptionsAuthentication]
    permission_classes = [IsAuthenticated | IsOptionsPermission]

    def options(self, request):
        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response

    def get(self, request):
        user = request.user
        send_email_confirmation(request, user)

        response = Response()
        response['Access-Control-Allow-Origin'] = FRONTEND_URL
        response['Access-Control-Allow-Headers'] = 'authorization'
        return response
