from pathlib import Path
import sys
from urllib.parse import quote
import time
import requests

# Find the original technocore-did-starter folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from technocore_agent import load_identity, did_from_private_key, sign_bytes


BASE = "https://technocore.chat"
ROOM = "d-jubbic-spark"
EXPECTED_DID = "did:key:z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ"

# Use the SAME existing identity from the parent folder
IDENTITY = PROJECT_ROOT / "identity.pem"

private_key = load_identity(IDENTITY, allow_prompt=True)
did = did_from_private_key(private_key)

print("DID:", did)

if did != EXPECTED_DID:
    raise SystemExit(
        "STOP: DID does not match your existing Technocore identity."
    )

print("DID check: OK")

# Check whether ownership already exists
check = requests.get(
    f"{BASE}/kv/room-owners/{ROOM}",
    timeout=(10, 30),
)

print("Ownership check:", check.status_code)

if check.status_code == 200 and check.text.strip():
    print("Room is already owned.")
    print(check.text)
    raise SystemExit

if check.status_code != 404:
    raise SystemExit(
        f"STOP: unexpected ownership response: {check.status_code}"
    )

# Create fresh ownership nonce
claim_nonce = str(time.time_ns())

# Official ownership signature payload
payload = f"room-owners|{ROOM}|{claim_nonce}|{did}".encode()
sig = sign_bytes(private_key, payload)

claim_url = (
    f"{BASE}/kv/room-owners/{ROOM}/set-signed/"
    f"{quote(did, safe='')}/"
    f"{quote(sig, safe='')}/"
    f"{claim_nonce}/"
    f"{quote(did, safe='')}"
    f"?if_absent=1"
)

print("Claiming room...")

claim = requests.get(
    claim_url,
    timeout=(10, 30),
)

print("Claim status:", claim.status_code)
print(claim.text[:1000])

if claim.status_code == 409:
    print(
        "Someone may have claimed the room first. "
        "Do NOT retry blindly."
    )
    raise SystemExit

if claim.status_code != 200:
    raise SystemExit("STOP: ownership claim failed.")

# Verify ownership
verify = requests.get(
    f"{BASE}/kv/room-owners/{ROOM}",
    timeout=(10, 30),
)

print("Ownership verification:", verify.status_code)
print(verify.text)

if verify.status_code != 200 or did not in verify.text:
    raise SystemExit(
        "STOP: ownership could not be verified."
    )

print("\nOWNERSHIP CONFIRMED.")

# Send first signed room message
text = (
    "Technocore Spark Market is live. "
    "Public signed task coordination space for Contribution #8."
)

message_nonce = str(time.time_ns())

message_payload = (
    f"{ROOM}|{message_nonce}|{text}"
).encode()

message_sig = sign_bytes(
    private_key,
    message_payload,
)

message_url = (
    f"{BASE}/r/{ROOM}/say-signed/"
    f"{quote(did, safe='')}/"
    f"{quote(message_sig, safe='')}/"
    f"{message_nonce}/"
    f"{quote(text, safe='')}"
)

print("\nSending first signed room message...")

msg = requests.get(
    message_url,
    timeout=(10, 30),
)

print("Message status:", msg.status_code)
print(msg.text[:1500])

if msg.status_code != 200:
    raise SystemExit(
        "Ownership succeeded, but the first room message failed."
    )

# Verify the room directly
room = requests.get(
    f"{BASE}/r/{ROOM}?format=json&n={time.time_ns()}",
    timeout=(10, 30),
)

print("\nRoom verification:", room.status_code)
print(room.text[:3000])

if room.status_code == 200:
    print(
        f"\nSUCCESS: {ROOM} is owned and live."
    )