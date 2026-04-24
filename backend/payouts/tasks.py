import random
import time
from celery import shared_task
from .services import PayoutService
from .models import Payout, PayoutStatus
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_payout_task(self, payout_id):
    """
    Simulates payout processing with 70% success, 20% failure, 10% stuck.
    """
    try:
        payout = Payout.objects.get(id=payout_id)
        
        # Mark as processing
        PayoutService.mark_as_processing(payout_id)
        
        # Simulate work
        time.sleep(2) 
        
        chance = random.random()
        
        if chance < 0.7:
            # 70% Success
            PayoutService.complete_payout(payout_id)
            logger.info(f"Payout {payout_id} completed successfully.")
            
        elif chance < 0.9:
            # 20% Failure
            PayoutService.fail_payout(payout_id, failure_reason="Bank rejected the transfer")
            logger.warning(f"Payout {payout_id} failed: Bank rejection.")
            
        else:
            # 10% Stuck (Processing)
            # We raise an exception to trigger a retry, 
            # simulating a "stuck" or "timeout" scenario
            logger.info(f"Payout {payout_id} stuck/timeout. Retrying...")
            raise Exception("Timeout connecting to bank API")

    except Exception as exc:
        # Exponential backoff retry
        # retry_backoff=True can be set in decorator for cleaner code, 
        # but showing explicit retry here for clarity.
        countdown = 2 ** self.request.retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Max retries reached, mark as failed and refund
            logger.error(f"Payout {payout_id} reached max retries. Marking as failed.")
            PayoutService.fail_payout(payout_id, failure_reason="Max retries reached after timeout")
