from rest_framework.permissions import BasePermission


class IsOptionsPermission(BasePermission):
    """
    Allows preflight requests to complete
    Used for CORS requests in development
    """
    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        else:
            return False


class IsPostPermission(BasePermission):
    """
    Allows preflight requests to complete
    Used for CORS requests in development
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        else:
            return False
