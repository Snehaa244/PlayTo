from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LedgerTransaction
from .services import LedgerService

class BalanceView(APIView):
    def get(self, request, merchant_id):
        balance = LedgerService.get_balance(merchant_id)
        return Response({"merchant_id": merchant_id, "balance_paise": balance})

class TransactionHistoryView(APIView):
    def get(self, request, merchant_id):
        transactions = LedgerTransaction.objects.filter(merchant_id=merchant_id).order_by('-created_at')[:50]
        data = [{
            "id": t.id,
            "amount_paise": t.amount_paise,
            "type": t.transaction_type,
            "description": t.description,
            "created_at": t.created_at
        } for t in transactions]
        return Response(data)
