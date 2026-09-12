from http.server import BaseHTTPRequestHandler
from pathlib import Path
import json
import base64
import urllib.request
import urllib.parse
import unicodedata

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ROOM = "p-jubbic-spark-market"
BASE_URL = "https://technocore.chat"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = PROJECT_ROOT / "index.html"

INVISIBLE_CATEGORIES = {
    "Cc",
    "Cf",
    "Cs",
    "Co",
    "Cn",
}

MULTICODEC_ED25519 = bytes([0xED, 0x01])


class ProtocolError(Exception):
    pass


def base58btc_decode(value):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    number = 0

    for character in value:
        if character not in alphabet:
            raise ProtocolError("Invalid base58 character")

        number = number * 58 + alphabet.index(character)

    raw = (
        number.to_bytes(
            (number.bit_length() + 7) // 8,
            "big",
        )
        if number
        else b""
    )

    leading_zeroes = len(value) - len(value.lstrip("1"))

    return b"\x00" * leading_zeroes + raw


def public_key_from_did(did):
    prefix = "did:key:"

    if not isinstance(did, str) or not did.startswith(prefix):
        raise ProtocolError("DID must start with 'did:key:z6Mk'")

    multibase = did[len(prefix):]

    if len(multibase) != 48 or not multibase.startswith("z6Mk"):
        raise ProtocolError(
            "DID must be the canonical 48-character Ed25519 multibase form"
        )

    decoded = base58btc_decode(multibase[1:])

    if len(decoded) != 34 or not decoded.startswith(MULTICODEC_ED25519):
        raise ProtocolError("DID must contain an ed25519-pub key")

    try:
        return Ed25519PublicKey.from_public_bytes(decoded[2:])
    except ValueError as error:
        raise ProtocolError(
            "DID contains an invalid Ed25519 public key"
        ) from error


def normalize_message(text):
    if not isinstance(text, str):
        raise ProtocolError("message text must be a string")

    normalized = "".join(
        " "
        if unicodedata.category(character) in INVISIBLE_CATEGORIES
        else character
        for character in text
    ).strip()

    if not normalized:
        raise ProtocolError("message has no visible text")

    return normalized


def message_payload(room, nonce, text):
    normalized = normalize_message(text)

    payload = f"{room}|{nonce}|{normalized}".encode()

    return normalized, payload


def verify_message(message):
    did = message.get("from")
    signature = message.get("sig")
    nonce = message.get("nonce")
    text = message.get("text")

    if not did or not signature or nonce is None or text is None:
        raise ProtocolError("Message is missing verification fields")

    normalized, payload = message_payload(
        ROOM,
        nonce,
        text,
    )

    if normalized != text:
        raise ProtocolError("Message normalization mismatch")

    try:
        raw_signature = base64.urlsafe_b64decode(
            signature + "=="
        )
    except Exception as error:
        raise ProtocolError(
            "Invalid signature encoding"
        ) from error

    public_key = public_key_from_did(did)

    public_key.verify(
        raw_signature,
        payload,
    )

    return True


def fetch_room():
    query = urllib.parse.urlencode(
        {
            "format": "json",
            "limit": 200,
        }
    )

    url = f"{BASE_URL}/r/{ROOM}?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Technocore-Spark-Market/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=15,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def build_market():
    data = fetch_room()

    messages = data.get("messages", [])

    valid_messages = []
    invalid_messages = []

    tasks = {}

    for message in messages:

        try:
            verify_message(message)
            signature_valid = True

            valid_messages.append(message)

        except Exception as error:
            signature_valid = False

            invalid_messages.append(
                {
                    "seq": message.get("seq"),
                    "error": str(error),
                }
            )

        message["signature_valid"] = signature_valid

    for message in valid_messages:

        text = message.get("text", "")
        parts = text.split("|")

        if not parts:
            continue

        event_type = parts[0]

        if event_type == "TASK_CREATE":

            if len(parts) < 4:
                continue

            task_id = parts[1]

            try:
                reward = int(parts[2])
            except ValueError:
                continue

            description = "|".join(parts[3:])

            # First valid creation wins. Later duplicate
            # TASK_CREATE events cannot overwrite task state.
            if task_id in tasks:
                continue

            tasks[task_id] = {
                "task_id": task_id,
                "reward": reward,
                "description": description,
                "creator": message.get("from"),
                "create_seq": message.get("seq"),
                "status": "OPEN",
                "claimed_by": None,
                "claim_seq": None,
                "completed_by": None,
                "complete_seq": None,
                "proof": None,
            }

        elif event_type == "TASK_CLAIM":

            if len(parts) != 3:
                continue

            task_id = parts[1]
            claimant = parts[2]

            if task_id not in tasks:
                continue

            task = tasks[task_id]

            # The DID inside the event must be the actual
            # cryptographic signer of the event.
            if claimant != message.get("from"):
                continue

            # Only the first valid claim wins.
            if task["status"] == "OPEN":
                task["status"] = "CLAIMED"
                task["claimed_by"] = claimant
                task["claim_seq"] = message.get("seq")

        elif event_type == "TASK_COMPLETE":

            if len(parts) < 4:
                continue

            task_id = parts[1]
            contributor = parts[2]
            proof = "|".join(parts[3:])

            if task_id not in tasks:
                continue

            task = tasks[task_id]

            # Completion must be signed by the contributor named
            # in the event and by the DID that actually claimed
            # the task. An OPEN task cannot be completed directly.
            if contributor != message.get("from"):
                continue

            if task["status"] != "CLAIMED":
                continue

            if task["claimed_by"] != contributor:
                continue

            task["status"] = "COMPLETED"
            task["completed_by"] = contributor
            task["complete_seq"] = message.get("seq")
            task["proof"] = proof

    completed_tasks = [
        task
        for task in tasks.values()
        if task["status"] == "COMPLETED"
    ]

    claimed_tasks = [
        task
        for task in tasks.values()
        if task["status"] == "CLAIMED"
    ]

    open_tasks = [
        task
        for task in tasks.values()
        if task["status"] == "OPEN"
    ]

    completed_spark = sum(
        task["reward"]
        for task in completed_tasks
    )

    return {
        "room": ROOM,

        "summary": {
            "total_tasks": len(tasks),
            "open_tasks": len(open_tasks),
            "claimed_tasks": len(claimed_tasks),
            "completed_tasks": len(completed_tasks),
            "completed_spark": completed_spark,
        },

        "verification": {
            "messages_scanned": len(messages),
            "valid_signatures": len(valid_messages),
            "invalid_signatures": len(invalid_messages),
        },

        "tasks": list(tasks.values()),

        "messages": [
            {
                "seq": message.get("seq"),
                "ts": message.get("ts"),
                "from": message.get("from"),
                "text": message.get("text"),
                "signature_valid": message.get(
                    "signature_valid",
                    False,
                ),
            }
            for message in messages
        ],

        "errors": invalid_messages,
    }


class handler(BaseHTTPRequestHandler):

    def send_json(self, payload, status=200):

        body = json.dumps(
            payload,
            indent=2,
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*",
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        self.wfile.write(body)

    def send_html(self):

        try:

            body = INDEX_FILE.read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.send_header(
                "Cache-Control",
                "no-store",
            )

            self.send_header(
                "Content-Length",
                str(len(body)),
            )

            self.end_headers()

            self.wfile.write(body)

        except Exception as error:

            self.send_json(
                {
                    "error": "Unable to load dashboard",
                    "details": str(error),
                },
                status=500,
            )

    def do_GET(self):

        path = self.path.split("?", 1)[0]

        # Serve the dashboard at the root.
        if path in {"/", "/index.html"}:
            self.send_html()
            return

        # Serve the market API.
        if path == "/api/market":
            try:

                result = build_market()

                self.send_json(result)

            except Exception as error:

                self.send_json(
                    {
                        "error": str(error),
                        "room": ROOM,
                    },
                    status=500,
                )

            return

        self.send_json(
            {
                "error": "Not found",
                "path": path,
            },
            status=404,
        )