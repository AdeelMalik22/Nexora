from django.urls import path

from .views import PaymentMethodView

urlpatterns = [path("methods/", PaymentMethodView.as_view(), name="payment-methods")]
