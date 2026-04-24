# Playto Payout Engine - Technical Architecture

This document explains the core engineering decisions made to ensure data integrity, atomicity, and correctness in the payout engine.

## 1. Ledger Design: Why BigIntegerField & Aggregation?
We store money in **paise** using `BigIntegerField`. 
- **Avoid Floating Point**: Never use `Float` or `Decimal` for money at scale due to precision loss.
- **Transaction-based**: We do NOT store a `balance` field in the `Merchant` table. A stored balance is a cached value and a source of truth mismatch.
- **Aggregation**: Balance is always `Sum(Credits) - Sum(Debits)`. PostgreSQL is highly optimized for this. With proper indexing on `(merchant_id, transaction_type)`, this scale to millions of transactions.

## 2. Concurrency Control: Preventing Overdraws
To prevent the "Two concurrent payouts of ₹60 with ₹100 balance" race condition, we use **Database-level Pessimistic Locking**:
```python
with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    balance = LedgerService.get_balance(merchant.id)
    if balance < amount_paise:
        raise ValidationError("Insufficient funds")
    # ... create payout and debit ...
```
**How it works**: `select_for_update()` places a row-level lock on the Merchant record. If Request A is checking the balance, Request B must wait at the database level until Request A's transaction commits or rolls back. This ensures serializable access to the balance check.

## 3. Idempotency Logic
The `Idempotency-Key` (UUID) ensures that a request is processed exactly once, even if the client retries due to network failure.
- **Key Storage**: Keys are stored per merchant.
- **Status Caching**: We store the response body and status code.
- **Handling In-Flight**: If a second request arrives while the first is still processing, we return `409 Conflict` to indicate "Request is already being processed".

## 4. State Machine Enforcement
Transitions are strictly controlled in `PayoutService`:
- `pending` -> `processing`
- `processing` -> `completed` OR `failed`
**Rule**: Any attempt to move from `completed` to `failed` or `failed` to `completed` will raise a `ValidationError`. This prevents double-refunds or incorrect accounting.

## 5. Atomicity & "Refunds"
We follow an **Append-Only** philosophy.
- When a payout is initiated, we immediately **Debit** the ledger (funds are reserved).
- If the payout **Fails** (Bank API error or Max Retries), we create a **Credit** (Refund) transaction in the same atomic block.
- **Outcome**: The balance is always accurate, and the ledger provides a perfect audit trail of why money was deducted and added back.

## 6. Senior Engineering Insight: AI Correction Example
**Incorrect AI Pattern**: "Updating a balance field on the Merchant model and then saving it."
**Why it's wrong**: In high-concurrency systems, two processes could read `balance=100`, subtract `60`, and both save `balance=40`. Even with `F()` expressions, you lack a granular audit trail.
**The Fix**: Use a ledger-based approach with `select_for_update()`. It is the only way to guarantee integrity across distributed workers.
