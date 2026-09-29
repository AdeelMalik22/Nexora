from django.urls import path

from .views import CashReportView, CreditReportView, DailyReportView, ProfitReportView, StockReportView

urlpatterns = [
    path("daily/", DailyReportView.as_view(), name="report-daily"),
    path("profit/", ProfitReportView.as_view(), name="report-profit"),
    path("stock-valuation/", StockReportView.as_view(), name="report-stock"),
    path("credit/", CreditReportView.as_view(), name="report-credit"),
    path("cash/", CashReportView.as_view(), name="report-cash"),
]
