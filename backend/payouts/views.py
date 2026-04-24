from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .services import PayoutService
from .utils import idempotent_request
from .tasks import process_payout_task
import uuid

class PayoutView(APIView):
    @idempotent_request
    def post(self, request):
        amount_paise = request.data.get('amount_paise')
        bank_account_id = request.data.get('bank_account_id')
        merchant_id = request.data.get('merchant_id')
        idempotency_key = request.headers.get('Idempotency-Key')

        if not all([amount_paise, bank_account_id, merchant_id, idempotency_key]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Orchestrate creation (includes locking and balance check)
            payout = PayoutService.create_payout(
                merchant_id=merchant_id,
                amount_paise=int(amount_paise),
                bank_account_id=bank_account_id,
                idempotency_key=uuid.UUID(idempotency_key)
            )

            # 2. Trigger async processing
            process_payout_task.delay(payout.id)

            return Response({
                "id": payout.id,
                "status": payout.status,
                "amount_paise": payout.amount_paise,
                "message": "Payout initiated successfully"
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An internal error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
