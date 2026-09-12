const IDENTITY_DB = "technocore-spark-identity";
const IDENTITY_STORE = "keys";

const MULTICODEC_ED25519 = new Uint8Array([0xed, 0x01]);
const BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

/*
 * Standard Base58BTC implementation.
 * Uses BigInt so there is no ambiguity in byte conversion.
 */

function base58Encode(bytes) {
  let leadingZeros = 0;

  while (
    leadingZeros < bytes.length &&
    bytes[leadingZeros] === 0
  ) {
    leadingZeros++;
  }

  let value = 0n;

  for (const byte of bytes) {
    value = (value << 8n) | BigInt(byte);
  }

  let encoded = "";

  while (value > 0n) {
    const remainder = Number(value % 58n);
    encoded = BASE58[remainder] + encoded;
    value = value / 58n;
  }

  return "1".repeat(leadingZeros) + encoded;
}

function base58Decode(value) {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error("Invalid Base58 value.");
  }

  let number = 0n;

  for (const character of value) {
    const digit = BASE58.indexOf(character);

    if (digit === -1) {
      throw new Error(
        `Invalid base58 character: ${character}`
      );
    }

    number = number * 58n + BigInt(digit);
  }

  let hex = number.toString(16);

  if (hex.length % 2 !== 0) {
    hex = "0" + hex;
  }

  let decodedLength = hex.length / 2;

  let bytes = new Uint8Array(decodedLength);

  for (let i = 0; i < decodedLength; i++) {
    bytes[i] = parseInt(
      hex.slice(i * 2, i * 2 + 2),
      16
    );
  }

  let leadingZeros = 0;

  for (const character of value) {
    if (character !== "1") {
      break;
    }

    leadingZeros++;
  }

  if (leadingZeros > 0) {
    const result = new Uint8Array(
      leadingZeros + bytes.length
    );

    result.set(bytes, leadingZeros);

    return result;
  }

  return bytes;
}

function bytesToBase64Url(bytes) {
  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function base64UrlToBytes(value) {
  const normalized = value
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const padding =
    "=".repeat((4 - (normalized.length % 4)) % 4);

  const binary = atob(normalized + padding);

  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  return bytes;
}

function concatBytes(...arrays) {
  const totalLength = arrays.reduce(
    (sum, array) => sum + array.length,
    0
  );

  const result = new Uint8Array(totalLength);

  let offset = 0;

  for (const array of arrays) {
    result.set(array, offset);
    offset += array.length;
  }

  return result;
}

function openIdentityDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(
      IDENTITY_DB,
      2
    );

    request.onupgradeneeded = () => {
      const database = request.result;

      if (
        !database.objectStoreNames.contains(
          IDENTITY_STORE
        )
      ) {
        database.createObjectStore(
          IDENTITY_STORE
        );
      }
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

async function saveIdentity(
  privateKey,
  publicKey
) {
  const database = await openIdentityDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(
      IDENTITY_STORE,
      "readwrite"
    );

    transaction
      .objectStore(IDENTITY_STORE)
      .put(
        {
          privateKey,
          publicKey
        },
        "participant"
      );

    transaction.oncomplete = () => {
      database.close();
      resolve();
    };

    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };
  });
}

async function loadIdentityRecord() {
  const database = await openIdentityDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(
      IDENTITY_STORE,
      "readonly"
    );

    const request = transaction
      .objectStore(IDENTITY_STORE)
      .get("participant");

    request.onsuccess = () => {
      const result = request.result;

      database.close();

      resolve(result || null);
    };

    request.onerror = () => {
      database.close();
      reject(request.error);
    };
  });
}

async function deleteIdentity() {
  const database = await openIdentityDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction(
      IDENTITY_STORE,
      "readwrite"
    );

    transaction
      .objectStore(IDENTITY_STORE)
      .delete("participant");

    transaction.oncomplete = () => {
      database.close();
      resolve();
    };

    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };
  });
}

async function publicKeyBytes(publicKey) {
  return new Uint8Array(
    await crypto.subtle.exportKey(
      "raw",
      publicKey
    )
  );
}

async function didFromPublicKey(publicKey) {
  const rawPublicKey =
    await publicKeyBytes(publicKey);

  if (rawPublicKey.length !== 32) {
    throw new Error(
      "Ed25519 public key must be exactly 32 bytes."
    );
  }

  const multicodec = concatBytes(
    MULTICODEC_ED25519,
    rawPublicKey
  );

  if (multicodec.length !== 34) {
    throw new Error(
      "Invalid Ed25519 multicodec length."
    );
  }

  const multibase =
    "z" + base58Encode(multicodec);

  if (
    multibase.length !== 48 ||
    !multibase.startsWith("z6Mk")
  ) {
    throw new Error(
      `Generated invalid did:key: ${multibase}`
    );
  }

  return "did:key:" + multibase;
}

async function didFromIdentityRecord(record) {
  if (
    !record ||
    !record.privateKey ||
    !record.publicKey
  ) {
    throw new Error(
      "Browser identity is incomplete. Delete it and create a new identity."
    );
  }

  return didFromPublicKey(
    record.publicKey
  );
}

async function createIdentity() {
  if (!window.crypto?.subtle) {
    throw new Error(
      "Web Crypto is unavailable in this browser."
    );
  }

  const existing =
    await loadIdentityRecord();

  if (existing) {
    throw new Error(
      "A browser identity already exists. Delete it before creating a new one."
    );
  }

  const keyPair =
    await crypto.subtle.generateKey(
      {
        name: "Ed25519"
      },
      false,
      ["sign", "verify"]
    );

  await saveIdentity(
    keyPair.privateKey,
    keyPair.publicKey
  );

  const did =
    await didFromPublicKey(
      keyPair.publicKey
    );

  return {
    did,
    privateKey: keyPair.privateKey,
    publicKey: keyPair.publicKey
  };
}

async function getIdentity() {
  const record =
    await loadIdentityRecord();

  if (!record) {
    return null;
  }

  const did =
    await didFromIdentityRecord(record);

  return {
    did,
    privateKey: record.privateKey,
    publicKey: record.publicKey
  };
}

function validateMessage(text) {
  if (typeof text !== "string") {
    throw new Error(
      "Message must be text."
    );
  }

  const normalized = text
    .replace(
      /[\u0000-\u001F\u007F-\u009F\u2028\u2029]/g,
      " "
    )
    .trim();

  if (!normalized) {
    throw new Error(
      "Message cannot be empty."
    );
  }

  if (normalized.length > 4096) {
    throw new Error(
      "Message is too long."
    );
  }

  return normalized;
}

function validateRoom(room) {
  if (typeof room !== "string") {
    throw new Error(
      "Invalid Technocore room name."
    );
  }

  if (
    !/^[a-z0-9][a-z0-9_-]{0,47}$/.test(room)
  ) {
    throw new Error(
      "Invalid Technocore room name."
    );
  }

  return room;
}

function validateNonce(nonce) {
  if (typeof nonce !== "string") {
    throw new Error(
      "Invalid nonce."
    );
  }

  if (!/^[0-9]{1,19}$/.test(nonce)) {
    throw new Error(
      "Invalid nonce."
    );
  }

  return nonce;
}

function nextNonce() {
  return String(
    Date.now()
  ) + String(
    Math.floor(Math.random() * 1000)
  );
}

async function signMessage(
  privateKey,
  publicKey,
  room,
  text,
  nonce = null
) {
  const validRoom =
    validateRoom(room);

  const validText =
    validateMessage(text);

  const validNonce =
    validateNonce(
      nonce === null
        ? nextNonce()
        : nonce
    );

  const payload =
    new TextEncoder().encode(
      `${validRoom}|${validNonce}|${validText}`
    );

  const signature =
    await crypto.subtle.sign(
      {
        name: "Ed25519"
      },
      privateKey,
      payload
    );

  return {
    room: validRoom,
    did: await didFromPublicKey(
      publicKey
    ),
    sig: bytesToBase64Url(
      new Uint8Array(signature)
    ),
    nonce: validNonce,
    text: validText
  };
}

async function verifyLocalSignature(record) {
  if (
    !record ||
    typeof record.did !== "string" ||
    !record.did.startsWith(
      "did:key:z6Mk"
    )
  ) {
    throw new Error(
      "Invalid did:key."
    );
  }

  if (
    typeof record.room !== "string" ||
    !/^[a-z0-9][a-z0-9_-]{0,47}$/.test(
      record.room
    )
  ) {
    throw new Error(
      "Invalid room."
    );
  }

  const multibase =
    record.did.substring(
      "did:key:".length
    );

  if (
    !multibase.startsWith("z")
  ) {
    throw new Error(
      "Invalid multibase did:key."
    );
  }

  const decoded =
    base58Decode(
      multibase.substring(1)
    );

  if (
    decoded.length !== 34 ||
    decoded[0] !== 0xed ||
    decoded[1] !== 0x01
  ) {
    throw new Error(
      `Invalid Ed25519 did:key encoding. Decoded ${decoded.length} bytes.`
    );
  }

  const rawPublicKey =
    decoded.slice(2);

  const publicKey =
    await crypto.subtle.importKey(
      "raw",
      rawPublicKey,
      {
        name: "Ed25519"
      },
      false,
      ["verify"]
    );

  const payload =
    new TextEncoder().encode(
      `${record.room}|${record.nonce}|${record.text}`
    );

  const signatureBytes =
    base64UrlToBytes(
      record.sig
    );

  return crypto.subtle.verify(
    {
      name: "Ed25519"
    },
    publicKey,
    signatureBytes,
    payload
  );
}

window.SparkIdentity = {
  createIdentity,
  getIdentity,
  deleteIdentity,
  signMessage,
  verifyLocalSignature,
  didFromPublicKey,
  loadIdentityRecord
};
