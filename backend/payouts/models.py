from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class PayoutStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'

class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey('merchants.Merchant', on_delete=models.PROTECT, related_name='payouts')
    amount_paise = models.BigIntegerField()
    bank_account_id = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, 
        choices=PayoutStatus.choices, 
        default=PayoutStatus.PENDING
    )
    idempotency_key = models.UUIDField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout {self.id} - {self.status}"

class IdempotencyKey(models.Model):
    merchant = models.ForeignKey('merchants.Merchant', on_delete=models.CASCADE)
    key = models.UUIDField()
    response_body = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('merchant', 'key')
        indexes = [
            models.Index(fields=['merchant', 'key']),
        ]

    @classmethod
    def is_expired(cls, obj):
        return timezone.now() > obj.created_at + timedelta(hours=24)
