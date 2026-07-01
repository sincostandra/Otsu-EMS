from rest_framework.generics import RetrieveAPIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    """POST email + password -> {access, refresh, user}."""

    serializer_class = CustomTokenObtainPairSerializer


class MeView(RetrieveAPIView):
    """Return the currently authenticated user (so the SPA knows its role)."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
