from __future__ import annotations

import base64
import json
import time
import uuid
from dataclasses import dataclass

from nacl.signing import SigningKey, VerifyKey


def _base58btc_encode(data: bytes) -> str:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    number = int.from_bytes(data, "big")
    encoded = ""

    while number:
        number, remainder = divmod(number, 58)
        encoded = alphabet[remainder] + encoded

    padding = len(data) - len(data.lstrip(b"\x00"))

    return "1" * padding + (encoded or "")


def _did_from_public_key(public_key: bytes) -> str:
    # Ed25519 public-key multicodec prefix: 0xed01
    multicodec_key = b"\xed\x01" + public_key
    return "did:key:z" + _base58btc_encode(multicodec_key)


@dataclass
class AgentIdentity:
    name: str
    signing_key: SigningKey

    @property
    def did(self) -> str:
        return _did_from_public_key(
            bytes(self.signing_key.verify_key)
        )

    def sign(self, room: str, message: str) -> dict:
        nonce = str(uuid.uuid4())

        payload = f"{room}|{nonce}|{message}"

        signature = self.signing_key.sign(
            payload.encode("utf-8")
        ).signature

        return {
            "agent": self.name,
            "did": self.did,
            "room": room,
            "nonce": nonce,
            "message": message,
            "signature": base64.b64encode(signature).decode(),
            "timestamp": time.time(),
        }


def create_identity(name: str) -> AgentIdentity:
    return AgentIdentity(
        name=name,
        signing_key=SigningKey.generate(),
    )


def verify_message(message: dict) -> bool:
    try:
        did = message["did"]

        if not did.startswith("did:key:z"):
            return False

        encoded_key = did[len("did:key:z"):]

        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

        number = 0
        for char in encoded_key:
            number = number * 58 + alphabet.index(char)

        raw = number.to_bytes(
            (number.bit_length() + 7) // 8,
            "big"
        )

        # Remove Ed25519 multicodec prefix
        if raw[:2] != b"\xed\x01":
            return False

        public_key = raw[2:]

        payload = (
            f'{message["room"]}|'
            f'{message["nonce"]}|'
            f'{message["message"]}'
        )

        signature = base64.b64decode(
            message["signature"]
        )

        VerifyKey(public_key).verify(
            payload.encode("utf-8"),
            signature,
        )

        return True

    except Exception:
        return False


def serialize_message(message: dict) -> str:
    return json.dumps(message, indent=2)