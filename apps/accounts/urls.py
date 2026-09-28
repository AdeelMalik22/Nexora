from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .token_views import NexoraTokenObtainPairView
from .views import (
    DeviceActionView,
    DeviceListView,
    DeviceRegistrationView,
    InvitationCreateView,
    MembershipListView,
    MembershipActionView,
    RoleListView,
    SignupView,
    InvitationAcceptView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", NexoraTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("devices/", DeviceRegistrationView.as_view(), name="device-register"),
    path("devices/list/", DeviceListView.as_view(), name="device-list"),
    path("devices/<uuid:device_id>/<str:action>/", DeviceActionView.as_view(), name="device-action"),
    path("roles/", RoleListView.as_view(), name="role-list"),
    path("memberships/", MembershipListView.as_view(), name="membership-list"),
    path("invitations/", InvitationCreateView.as_view(), name="invitation-create"),
    path("invitations/accept/", InvitationAcceptView.as_view(), name="invitation-accept"),
    path("memberships/<uuid:membership_id>/<str:action>/", MembershipActionView.as_view(), name="membership-action"),
]
