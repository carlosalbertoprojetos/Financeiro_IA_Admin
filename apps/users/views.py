from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions import TIPPermission, permissions_for_role


class LoginView(APIView):
    """Placeholder login — accepts any credentials and returns demo profile."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username", "demo")
        role = request.data.get("role", "admin")
        perms = permissions_for_role(role)

        return Response(
            {
                "token": "tip-demo-token",
                "user": {
                    "id": "demo-1",
                    "username": username,
                    "display_name": username.title(),
                    "role": role,
                    "permissions": sorted(p.value for p in perms),
                },
            }
        )


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        return Response({"status": "logged_out"})


class CurrentUserView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        role = request.query_params.get("role", "admin")
        username = request.query_params.get("username", "demo")
        perms = permissions_for_role(role)

        return Response(
            {
                "id": "demo-1",
                "username": username,
                "display_name": username.title(),
                "role": role,
                "permissions": sorted(p.value for p in perms),
            }
        )


class PermissionsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "permissions": [p.value for p in TIPPermission],
                "roles": {
                    role: sorted(p.value for p in perms)
                    for role, perms in __import__(
                        "apps.permissions", fromlist=["DEFAULT_ROLE_PERMISSIONS"]
                    ).DEFAULT_ROLE_PERMISSIONS.items()
                },
            }
        )
