"""RSA-OAEP encryption (SHA-1, MGF1-SHA-1) with a public key, standard library only.

RSAES-OAEP as in RFC 8017, section 7.1: https://www.rfc-editor.org/rfc/rfc8017#section-7.1

The provider expects the parental lock PIN encrypted this way, as the web player does.
"""

import base64
import hashlib
import os


def _der(data, i):
    """Return (tag, content, next index) of the DER element at i."""
    tag, length = data[i], data[i + 1]
    i += 2
    if length & 0x80:
        size = length & 0x7F
        length = int.from_bytes(data[i : i + size], "big")
        i += size
    return tag, data[i : i + length], i + length


def public_key(spki_b64):
    """Return (modulus, exponent) of a base64 SubjectPublicKeyInfo ("MIGf...")."""
    _, spki, _ = _der(base64.b64decode(spki_b64), 0)
    _, _, i = _der(spki, 0)  # the algorithm identifier
    _, bits, _ = _der(spki, i)
    _, rsa_key, _ = _der(bits, 1)  # after the bit string's unused-bits byte
    _, modulus, i = _der(rsa_key, 0)
    _, exponent, _ = _der(rsa_key, i)
    return int.from_bytes(modulus, "big"), int.from_bytes(exponent, "big")


def _mgf1(seed, length):
    out, counter = b"", 0
    while len(out) < length:
        out += hashlib.sha1(seed + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]


def encrypt(spki_b64, message):
    """Return the base64 RSA-OAEP ciphertext of `message` (bytes), with an empty label."""
    modulus, exponent = public_key(spki_b64)
    size = (modulus.bit_length() + 7) // 8
    label_hash = hashlib.sha1(b"").digest()
    hlen = len(label_hash)
    if len(message) > size - 2 * hlen - 2:
        raise ValueError("message too long")
    block = label_hash + b"\x00" * (size - len(message) - 2 * hlen - 2) + b"\x01" + message
    seed = os.urandom(hlen)
    masked_block = bytes(a ^ b for a, b in zip(block, _mgf1(seed, size - hlen - 1)))
    masked_seed = bytes(a ^ b for a, b in zip(seed, _mgf1(masked_block, hlen)))
    encoded = int.from_bytes(b"\x00" + masked_seed + masked_block, "big")
    return base64.b64encode(pow(encoded, exponent, modulus).to_bytes(size, "big")).decode()
