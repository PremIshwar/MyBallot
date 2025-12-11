import os
import json
import uuid
import base64
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization

# --- Demo in-memory key setup (replace with TPM/HSM in production) ---
_master_secret = os.urandom(32)
hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"idballot-demo")
DEK = hkdf.derive(_master_secret)  # 32 bytes AES-256 key
aesgcm = AESGCM(DEK)

_signing_key = Ed25519PrivateKey.generate()
_verifying_key = _signing_key.public_key()

# In-memory store for encrypted+signed ballots
stored_votes = []


def encrypt_ballot(plaintext_bytes: bytes, aad: bytes = b""):
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad)
    return {
        "nonce_b64": base64.b64encode(nonce).decode(),
        "ciphertext_b64": base64.b64encode(ciphertext).decode(),
        "aad_b64": base64.b64encode(aad).decode(),
    }


def sign_bytes(b: bytes):
    sig = _signing_key.sign(b)
    return base64.b64encode(sig).decode()


def create_encrypted_signed_ballot(voter_info: dict, choice_text: str):
    """
    Create envelope -> encrypt -> sign -> return packet
    """
    envelope = {
        "ballot_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "voter": {
            "name": voter_info.get("name"),
            "id_number": voter_info.get("id_number"),
            "persona_token": voter_info.get("persona_token"),
        },
        "vote": {"choice": choice_text},
    }
    plaintext = json.dumps(envelope, separators=(",", ":"), sort_keys=True).encode()
    aad = envelope["ballot_id"].encode()
    encrypted = encrypt_ballot(plaintext, aad=aad)
    # sign nonce||ciphertext||aad bytes
    sign_target = (
        base64.b64decode(encrypted["nonce_b64"]) +
        base64.b64decode(encrypted["ciphertext_b64"]) +
        base64.b64decode(encrypted["aad_b64"])
    )
    signature_b64 = sign_bytes(sign_target)
    packet = {
        "envelope_meta": {
            "ballot_id": envelope["ballot_id"],
            "timestamp_utc": envelope["timestamp_utc"],
        },
        "encrypted": encrypted,
        "signature_b64": signature_b64,
        "public_key_b64": base64.b64encode(
            _verifying_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        ).decode()
    }
    # store in-memory
    stored_votes.append(packet)
    return packet
