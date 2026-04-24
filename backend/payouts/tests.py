import threading
import uuid
from django.test import TransactionTestCase
from merchants.models import Merchant
from ledger.models import LedgerTransaction, TransactionType
from payouts.services import PayoutService
from payouts.models import Payout, PayoutStatus
from django.core.exceptions import ValidationError

class PayoutConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Merchant", email="test@test.com")
        # Give them 100 INR (10,000 paise)
        LedgerTransaction.objects.create(
            merchant=self.merchant,
            amount_paise=10000,
            transaction_type=TransactionType.CREDIT
        )

    def test_concurrent_payouts_prevent_overdraw(self):
        """
        Attempt 2 concurrent payouts of 60 INR each when balance is 100 INR.
        Only one should succeed.
        """
        results = []

        def attempt_payout():
            try:
                # Use a unique idempotency key for each thread to avoid idempotency hits
                PayoutService.create_payout(
                    merchant_id=self.merchant.id,
                    amount_paise=6000,
                    bank_account_id="ACC_1",
                    idempotency_key=uuid.uuid4()
                )
                results.append("SUCCESS")
            except ValidationError as e:
                results.append("FAILURE")
            except Exception as e:
                results.append(f"ERROR: {str(e)}")

        t1 = threading.Thread(target=attempt_payout)
        t2 = threading.Thread(target=attempt_payout)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(results.count("SUCCESS"), 1)
        self.assertEqual(results.count("FAILURE"), 1)

    def test_idempotency(self):
        """
        Ensure the same idempotency key results in only one payout.
        """
        key = uuid.uuid4()
        
        # First request
        p1 = PayoutService.create_payout(
            merchant_id=self.merchant.id,
            amount_paise=1000,
            bank_account_id="ACC_1",
            idempotency_key=key
        )
        
        # Second request with same key should fail at DB level (Unique constraint)
        with self.assertRaises(Exception): # IntegrityError
             PayoutService.create_payout(
                merchant_id=self.merchant.id,
                amount_paise=1000,
                bank_account_id="ACC_1",
                idempotency_key=key
            )
        
        self.assertEqual(Payout.objects.count(), 1)
