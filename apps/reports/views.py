from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .services import cash_report, credit_report, daily_report, profit_report, stock_report


class ReportView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "view_reports"


class DailyReportView(ReportView):
    def get(self, request):
        return Response(daily_report(request.shop, request))


class ProfitReportView(ReportView):
    def get(self, request):
        return Response(profit_report(request.shop, request))


class StockReportView(ReportView):
    def get(self, request):
        return Response(stock_report(request.shop, request))


class CreditReportView(ReportView):
    def get(self, request):
        return Response({"customers": credit_report(request.shop)})


class CashReportView(ReportView):
    def get(self, request):
        return Response(cash_report(request.shop, request))
