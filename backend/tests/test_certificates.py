import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.certificates import canonical_payload, sign_payload, verify_payload_signature
from app.config import settings


def test_ed25519_certificate_signature_round_trip(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    monkeypatch.setattr(settings, "certificate_signing_private_key", private_pem)
    monkeypatch.setattr(settings, "certificate_signing_key_id", "test-key-1")
    payload = {
        "certificate_id": "synthetic-certificate",
        "schema_version": 1,
        "sha256": "a" * 64,
        "status": "ISSUED",
    }

    signature, public_key_pem, key_id = sign_payload(payload)

    assert key_id == "test-key-1"
    assert verify_payload_signature(payload, signature, public_key_pem)
    assert not verify_payload_signature({**payload, "status": "REVOKED"}, signature, public_key_pem)


def test_certificate_payload_serialization_is_deterministic():
    first = {"certificate_id": "synthetic", "schema_version": 1, "status": "ISSUED"}
    reordered = {"status": "ISSUED", "schema_version": 1, "certificate_id": "synthetic"}

    assert canonical_payload(first) == canonical_payload(reordered)
