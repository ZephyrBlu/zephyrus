from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


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
