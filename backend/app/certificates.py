import base64
import json
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.config import settings


def canonical_payload(payload: dict[str, Any]) -> bytes:
    """Serialize the signed payload deterministically for independent verification."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _load_private_key() -> Ed25519PrivateKey:
    configured = settings.certificate_signing_private_key.strip()
    if not configured:
        raise RuntimeError("Certificate signing key is not configured")
    pem = configured.replace("\\n", "\n").encode("utf-8")
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise RuntimeError("Certificate signing key must be an Ed25519 private key")
    return key


def sign_payload(payload: dict[str, Any]) -> tuple[str, str, str]:
    private_key = _load_private_key()
    signature = private_key.sign(canonical_payload(payload))
    signature_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return signature_b64, public_pem, settings.certificate_signing_key_id


def verify_payload_signature(
    payload: dict[str, Any],
    signature_b64: str,
    public_key_pem: str,
) -> bool:
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(public_key, Ed25519PublicKey):
            return False
        padded = signature_b64 + ("=" * (-len(signature_b64) % 4))
        signature = base64.urlsafe_b64decode(padded.encode("ascii"))
        public_key.verify(signature, canonical_payload(payload))
        return True
    except (ValueError, TypeError, InvalidSignature):
        return False
