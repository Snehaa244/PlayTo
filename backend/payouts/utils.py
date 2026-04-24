from functools import wraps
from rest_framework.response import Response
from .models import IdempotencyKey
from django.db import transaction

def idempotent_request(view_func):
    @wraps(view_func)
    def _wrapped_view(view_instance, request, *args, **kwargs):
        key = request.headers.get('Idempotency-Key')
        if not key:
            return view_func(view_instance, request, *args, **kwargs)

        merchant = getattr(request, 'merchant', None) # Assume set by auth
        if not merchant:
            # For this demo, we'll fetch from request data or just use a dummy
            merchant_id = request.data.get('merchant_id')
            from merchants.models import Merchant
            merchant = Merchant.objects.get(id=merchant_id)

        # Check for existing key
        with transaction.atomic():
            idem_key, created = IdempotencyKey.objects.get_or_create(
                merchant=merchant,
                key=key
            )
            
            if not created:
                # Key exists. If it has a response, return it.
                if idem_key.response_body is not None:
                    return Response(idem_key.response_body, status=idem_key.status_code)
                else:
                    # Request is still processing
                    return Response({"error": "Request is already being processed"}, status=409)

        # Proceed to view
        response = view_func(view_instance, request, *args, **kwargs)
        
        # Save response for future hits
        if response.status_code < 500: # Don't cache server errors
            idem_key.response_body = response.data
            idem_key.status_code = response.status_code
            idem_key.save()
            
        return response
    return _wrapped_view
