from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
import uuid

class TransactionType(models.TextChoices):
    CREDIT = 'CREDIT', 'Credit'
    DEBIT = 'DEBIT', 'Debit'

class LedgerTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey('merchants.Merchant', on_delete=models.PROTECT, related_name='ledger_transactions')
    amount_paise = models.BigIntegerField()  # Always positive
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    reference_id = models.UUIDField(null=True, blank=True, help_text="ID of the related Payout or Payment")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['merchant', 'transaction_type']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount_paise} - {self.merchant.name}"

    @classmethod
    def get_balance(cls, merchant_id):
        """
        Calculate balance using database aggregation: Credits - Debits.
        """
        aggregates = cls.objects.filter(merchant_id=merchant_id).aggregate(
            total_credits=Coalesce(Sum('amount_paise', filter=models.Q(transaction_type=TransactionType.CREDIT)), 0, output_field=models.BigIntegerField()),
            total_debits=Coalesce(Sum('amount_paise', filter=models.Q(transaction_type=TransactionType.DEBIT)), 0, output_field=models.BigIntegerField()),
        )
        return aggregates['total_credits'] - aggregates['total_debits']
