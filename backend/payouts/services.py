from django.db import transaction
from django.core.exceptions import ValidationError
from merchants.models import Merchant
from ledger.services import LedgerService
from ledger.models import TransactionType
from .models import Payout, PayoutStatus, IdempotencyKey
import logging

logger = logging.getLogger(__name__)

class PayoutService:
    @staticmethod
    def create_payout(merchant_id, amount_paise, bank_account_id, idempotency_key):
        """
        Orchestrates payout creation with concurrency locking and balance check.
        """
        with transaction.atomic():
            # 1. Concurrency Locking: Lock the merchant record to serialize payouts
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)
            
            # 2. Balance Check
            balance = LedgerService.get_balance(merchant.id)
            if balance < amount_paise:
                raise ValidationError(f"Insufficient balance. Available: {balance}, Requested: {amount_paise}")
            
            # 3. Create Payout record (Pending)
            payout = Payout.objects.create(
                merchant=merchant,
                amount_paise=amount_paise,
                bank_account_id=bank_account_id,
                idempotency_key=idempotency_key,
                status=PayoutStatus.PENDING
            )
            
            # 4. Immediate Debit (Reserve funds)
            # This ensures the balance is updated immediately in the ledger
            LedgerService.create_transaction(
                merchant=merchant,
                amount_paise=amount_paise,
                transaction_type=TransactionType.DEBIT,
                reference_id=payout.id,
                description=f"Payout request: {payout.id}"
            )
            
            return payout

    @staticmethod
    def mark_as_processing(payout_id):
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)
            if payout.status != PayoutStatus.PENDING:
                raise ValidationError(f"Invalid state transition from {payout.status} to PROCESSING")
            
            payout.status = PayoutStatus.PROCESSING
            payout.save()
            return payout

    @staticmethod
    def complete_payout(payout_id):
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)
            if payout.status != PayoutStatus.PROCESSING:
                raise ValidationError(f"Invalid state transition from {payout.status} to COMPLETED")
            
            payout.status = PayoutStatus.COMPLETED
            payout.save()
            return payout

    @staticmethod
    def fail_payout(payout_id, failure_reason=""):
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)
            
            # Allow failure from PENDING or PROCESSING (robustness)
            if payout.status in [PayoutStatus.COMPLETED, PayoutStatus.FAILED]:
                raise ValidationError(f"Cannot fail a payout in {payout.status} state")
            
            payout.status = PayoutStatus.FAILED
            payout.save()
            
            # 5. Atomic Refund: Create a CREDIT transaction in the same DB transaction
            LedgerService.create_transaction(
                merchant=payout.merchant,
                amount_paise=payout.amount_paise,
                transaction_type=TransactionType.CREDIT,
                reference_id=payout.id,
                description=f"Refund for failed payout: {payout.id}. Reason: {failure_reason}"
            )
            
            return payout
