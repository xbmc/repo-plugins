"""The Widevine service certificate's messages, standard library only.

Laid out as in Widevine's license_protocol.proto: a SignedMessage's field 1 is its type,
field 2 its payload.
"""

# A SignedMessage asking for the service certificate: type SERVICE_CERTIFICATE_REQUEST (4), nothing else.
REQUEST = b"\x08\x04"
# A SignedMessage of type SERVICE_CERTIFICATE (5) with its payload field (2) next.
CERTIFICATE_PREFIX = b"\x08\x05\x12"


def unwrap(msg):
    """Return the SignedDrmCertificate bytes of a SignedMessage{type=SERVICE_CERTIFICATE, msg=cert}; None if not one.

    The licence server sends the whole SignedMessage; Android MediaDrm only accepts
    the bare certificate.
    """
    if not msg.startswith(CERTIFICATE_PREFIX):
        return None
    length, shift, pos = 0, 0, len(CERTIFICATE_PREFIX)
    while pos < len(msg):
        b = msg[pos]
        length |= (b & 0x7F) << shift
        pos += 1
        if not b & 0x80:
            break
        shift += 7
    cert = msg[pos : pos + length]
    return cert if len(cert) == length else None
