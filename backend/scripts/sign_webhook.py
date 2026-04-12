#!/usr/bin/env python3
"""
Pomocniczy skrypt: generuje podpis HMAC-SHA256 dla payloadu webhooka HR.

Użycie:
    python scripts/sign_webhook.py '{"event_type": "DOLADOWANIE", "payload": {"hr_employee_id": "EMP001", "amount_pln": 100, "expiry_date": "2026-12-31"}}'
"""
import hashlib
import hmac
import json
import os
import sys


def sign_payload(payload: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python sign_webhook.py '<json_payload>'", file=sys.stderr)
        sys.exit(1)

    raw = sys.argv[1]
    secret = os.environ.get("HMAC_SECRET", "dev-hmac-secret")

    try:
        parsed = json.loads(raw)
        normalized = json.dumps(parsed, ensure_ascii=False)
    except json.JSONDecodeError:
        normalized = raw

    sig = sign_payload(normalized, secret)
    print(f"X-Hub-Signature-256: {sig}")
    print(f"\nPayload:\n{normalized}")
    print(f"\ncURL:\ncurl -X POST http://localhost:8000/api/v1/hr/events \\")
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -H "{sig}" \\')
    print(f"  -d '{normalized}'")
