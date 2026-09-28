from rest_framework_simplejwt.views import TokenObtainPairView

from .tokens import NexoraTokenObtainPairSerializer


class NexoraTokenObtainPairView(TokenObtainPairView):
    serializer_class = NexoraTokenObtainPairSerializer
