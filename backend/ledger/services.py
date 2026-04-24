from django.db import transaction
from .models import LedgerTransaction, TransactionType

class LedgerService:
    @staticmethod
    def create_transaction(merchant, amount_paise, transaction_type, reference_id=None, description=""):
        """
        Creates a ledger transaction. This should always be inside a DB transaction.
        """
        return LedgerTransaction.objects.create(
            merchant=merchant,
            amount_paise=amount_paise,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description
        )

    @staticmethod
    def get_balance(merchant_id):
        return LedgerTransaction.get_balance(merchant_id)
