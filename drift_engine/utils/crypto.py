from __future__ import annotations

import hmac
import secrets
from hashlib import sha256

from drift_engine.utils.serialization import canonical_dumps


def secure_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def generate_token(byte_length: int = 32) -> str:
    return secrets.token_urlsafe(byte_length)


def sign_payload(payload: object, secret: str) -> str:
    message = canonical_dumps(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, sha256).hexdigest()


def verify_signature(payload: object, signature: str, secret: str) -> bool:
    expected = sign_payload(payload, secret)
    return secure_compare(expected, signature)
