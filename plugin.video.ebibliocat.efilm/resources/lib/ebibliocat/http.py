"""Bounded service requests. No credentials, response bodies, or URLs are logged."""

import json
import socket
import urllib.error
import urllib.request

from resources.lib.ebibliocat.errors import EfilmError

TIMEOUT = 20
MAX_RESPONSE = 32 * 1024 * 1024


def request(url, method="GET", payload=None, headers=None, as_json=True):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise EfilmError("invalid_response")
        return json.loads(raw.decode("utf-8")) if as_json else raw
    except urllib.error.HTTPError as error:
        # Never display an arbitrary backend body: it can contain account details.
        status = error.code
        loan_limit = False
        if status == 406:
            try:
                rejection = json.loads(error.read(4096).decode("utf-8"))
                loan_limit = isinstance(rejection, dict) and rejection.get("code") == "0010"
            except (ValueError, UnicodeError, OSError):
                pass
        error.close()
        key = {
            401: "session_expired",
            403: "access_denied",
            404: "unavailable",
            409: "loan_conflict",
            429: "rate_limited",
        }.get(status, "service_error")
        if loan_limit:
            key = "loan_limit"
        raise EfilmError(key, status=status, uncertain=method == "POST" and status >= 500) from None
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as error:
        raise EfilmError("network_error", uncertain=method == "POST") from error
    except (ValueError, UnicodeError) as error:
        raise EfilmError("invalid_response", uncertain=method == "POST") from error
