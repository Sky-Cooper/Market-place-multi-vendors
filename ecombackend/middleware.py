# middleware.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path in ["/api/token/", "/api/token/refresh/"]:
            return self.get_response(request)

        try:
            jwt_auth = JWTAuthentication()
            auth_result = jwt_auth.authenticate(request)

            if auth_result:
                request.user, request.auth = auth_result
        except (InvalidToken, AuthenticationFailed):

            pass

        return self.get_response(request)
