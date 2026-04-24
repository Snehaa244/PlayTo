from django.contrib import admin
from django.urls import path, include
from payouts.views import PayoutView
from ledger.views import BalanceView, TransactionHistoryView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/payouts', PayoutView.as_view(), name='payouts'),
    path('api/v1/merchants/<uuid:merchant_id>/balance', BalanceView.as_view(), name='balance'),
    path('api/v1/merchants/<uuid:merchant_id>/transactions', TransactionHistoryView.as_view(), name='transactions'),
]
