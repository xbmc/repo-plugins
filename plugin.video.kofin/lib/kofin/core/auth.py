"""Server resolution and authentication flows (dialog-free, unit-testable).

The UI around these calls (keyboards, Quick Connect code dialog) lives in
kofin.plugin.account; this module only talks to the server.
"""

from typing import Any
from urllib.parse import quote, urlsplit

from kofin.core.http import Http, HttpError
from kofin.core.log import Logger

LOG = Logger(__name__)

DEFAULT_HTTP_PORT = 8096


class AuthResult:
    def __init__(
        self, token: str, user_id: str, user_name: str, server_id: str
    ) -> None:
        self.token = token
        self.user_id = user_id
        self.user_name = user_name
        self.server_id = server_id

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "AuthResult":
        user = data.get("User") or {}
        return cls(
            token=data.get("AccessToken", ""),
            user_id=user.get("Id", ""),
            user_name=user.get("Name", ""),
            server_id=data.get("ServerId", ""),
        )


def normalize_address(text: str) -> str:
    """'host', 'host:port' or a full URL -> canonical base URL, no trailing /.

    A bare host gets http on port 8096; explicit schemes and ports pass
    through (https without a port stays portless, i.e. 443). A user name and
    password are dropped: the Authorization header is the only credential a
    request carries, and the address is logged and stored.
    """
    address = text.strip().rstrip("/")
    if not address:
        return ""
    if "://" not in address:
        address = "http://" + address
    parts = urlsplit(address)
    # The last "@", as urlsplit takes it: a password may hold one.
    netloc = parts.netloc.rpartition("@")[2]
    # ``parts.port`` rather than a ":" test: an IPv6 literal is full of
    # colons.
    if parts.port is None and parts.scheme == "http" and not netloc.endswith(":"):
        netloc = "%s:%d" % (netloc, DEFAULT_HTTP_PORT)
    base = "%s://%s" % (parts.scheme, netloc)
    if parts.path:
        base += parts.path.rstrip("/")
    return base


def build_auth_header(
    device_name: str, device_id: str, version: str, token: str = ""
) -> str:
    fields = [
        'MediaBrowser Client="Kofin"',
        # Jellyfin URL-decodes every value of this header, and http.client
        # sends header values as Latin-1. Encoded as encodeURIComponent
        # encodes it, a name in any script and with any punctuation reaches
        # the server as typed.
        'Device="%s"' % quote(device_name, safe="!~*'()"),
        'DeviceId="%s"' % device_id,
        'Version="%s"' % version,
    ]
    if token:
        fields.append('Token="%s"' % token)
    return ", ".join(fields)


def public_info(http: Http, address: str) -> dict[str, Any]:
    """The server's public info. Whatever else answers at the address (a web
    page, a captive portal) sends a body that is not a JSON object, which is
    an HttpError like any other bad answer."""
    url = address + "/System/Info/Public"
    response = http.request("GET", url, retries=1)
    try:
        info = response.json()
    except ValueError:
        info = None
    if not isinstance(info, dict):
        raise HttpError(
            response.status_code,
            "GET %s -> %d with a body that is not a JSON object"
            % (url, response.status_code),
        )
    return info


# The reachability check behind LAN discovery (kofin.core.discovery). The
# connect leg is api.PROBE_TIMEOUT's: 3.05 s covers one TCP SYN retransmit.
# The read leg is five seconds, since the server has just answered a
# broadcast and every failure that matters is in the connect leg.
DISCOVERY_PROBE_TIMEOUT = (3.05, 5.0)


def probe_public_info(http: Http, address: str) -> dict[str, Any]:
    """/System/Info/Public on the discovery budget -- one attempt, no ladder.

    ``retries=0`` because the scan window is already the retry policy: a
    second HTTP attempt per address doubles the worst case for a server the
    broadcast has proved is there.
    """
    response = http.request(
        "GET",
        address + "/System/Info/Public",
        timeout=DISCOVERY_PROBE_TIMEOUT,
        retries=0,
    )
    info: dict[str, Any] = response.json()
    return info


def quick_connect_enabled(http: Http, address: str, header: str) -> bool:
    response = http.request(
        "GET",
        address + "/QuickConnect/Enabled",
        headers={"Authorization": header},
        retries=1,
    )
    return bool(response.json())


def quick_connect_initiate(http: Http, address: str, header: str) -> dict[str, Any]:
    response = http.request(
        "POST",
        address + "/QuickConnect/Initiate",
        headers={"Authorization": header},
        retries=1,
    )
    state: dict[str, Any] = response.json()
    return state


def quick_connect_poll(http: Http, address: str, header: str, secret: str) -> bool:
    response = http.request(
        "GET",
        address + "/QuickConnect/Connect",
        headers={"Authorization": header},
        params={"secret": secret},
        retries=1,
    )
    state = response.json()
    return bool(state.get("Authenticated"))


def authenticate_quick_connect(
    http: Http, address: str, header: str, secret: str
) -> AuthResult:
    response = http.request(
        "POST",
        address + "/Users/AuthenticateWithQuickConnect",
        headers={"Authorization": header},
        json_body={"Secret": secret},
        retries=1,
    )
    return AuthResult.from_response(response.json())


def authenticate_password(
    http: Http, address: str, header: str, username: str, password: str
) -> AuthResult:
    response = http.request(
        "POST",
        address + "/Users/AuthenticateByName",
        headers={"Authorization": header},
        json_body={"Username": username, "Pw": password},
        retries=1,
    )
    return AuthResult.from_response(response.json())


def logout(http: Http, address: str, header: str) -> None:
    try:
        http.request(
            "POST",
            address + "/Sessions/Logout",
            headers={"Authorization": header},
            retries=0,
        )
    except Exception as error:
        # Best effort: local credentials are cleared regardless.
        LOG.warning("server-side logout failed: %s", error)
