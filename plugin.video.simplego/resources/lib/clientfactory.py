"""The provider's client the add-on's parts share, and its CA bundle."""

import contextlib
import os
import re
import threading

import xbmc

from resources.lib import kodiutil
from resources.lib import provider

_shared = None
_shared_lock = threading.Lock()
_bundle = None


def make_client():
    """Return a client of its own (it may switch to guest mode, see provider.auth.Auth.guest)."""
    return provider.Client(
        kodiutil.PROFILE,
        # Made at the client's first request (a menu needs none).
        ca_bundle=ca_bundle,
        # The client's measurements (state file, startup page), shown with Kodi's debug logging.
        debug=lambda message: kodiutil.log(message, xbmc.LOGDEBUG),
        # Waiting for the state file's lock, Kodi's exit comes first.
        lock_wait=xbmc.Monitor().waitForAbort,
    )


def has_login():
    """Return whether the add-on is logged in, cheaply (see provider.has_login)."""
    return provider.has_login(kodiutil.PROFILE)


def shared_client():
    """Return one client for the whole process (the service's streams), reusing its connections across switches."""
    global _shared
    with _shared_lock:
        if _shared is None:
            _shared = make_client()
        return _shared


def forget_shared_client():
    """Forget the shared client after a login or logout elsewhere: the next stream starts from the file as it is then."""
    global _shared
    with _shared_lock:
        _shared = None


# Roots of Kodi's certifi (2023.5.7, still what Kodi 21's repository ships) that certifi itself has dropped
# as untrustworthy since: left out of the bundle whatever certifi the device has.
# emSign ECC G3: intermediates with leaked keys (GHSA-6q48-6c7w-9gw2, certifi 2026.10.18); e-Tugra:
# removed after a breach (GHSA-xqr8-7jwr-rhp7, 2023.7.22); GLOBALTRUST 2020 (GHSA-248v-346w-9cwc, 2024.7.4).
DISTRUSTED = (
    "emSign ECC Root CA - G3",
    "E-Tugra Certification Authority",
    "E-Tugra Global Root CA RSA v3",
    "E-Tugra Global Root CA ECC v3",
    "GLOBALTRUST 2020",
)
# Its own name for each way the bundle is made: an older one (without the DISTRUSTED filter) is made anew.
BUNDLE = "ca-bundle-2.pem"
OLD_BUNDLES = ("ca-bundle.pem",)


def ca_bundle():
    """Return the CA bundle's path: certifi's roots but the DISTRUSTED, plus the certificates player.telekomtvgo.hu fails to send.

    The server omits its Sectigo DV E36 intermediate, and Kodi's certifi (2023.5.7)
    predates the Sectigo E46 root, so E46 cross-signed by USERTrust ECC is shipped too.
    Refreshed by scripts/update_certs.py; its weekly run warns a year before expiry.
    """
    global _bundle
    if _bundle:
        return _bundle
    certs_dir = os.path.join(kodiutil.ADDON_PATH, "resources", "certs")
    extras = sorted(os.path.join(certs_dir, f) for f in os.listdir(certs_dir) if f.endswith(".crt"))
    bundle = os.path.join(kodiutil.PROFILE, BUNDLE)
    certifi_file = _certifi_file()
    sources = [certifi_file] + extras
    if not os.path.exists(bundle) or os.path.getmtime(bundle) < max(os.path.getmtime(p) for p in sources):
        os.makedirs(kodiutil.PROFILE, exist_ok=True)
        with open(bundle, "w") as out:
            for p in sources:
                with open(p) as f:
                    out.write((drop_distrusted(f.read()) if p == certifi_file else f.read()) + "\n")
        for old in OLD_BUNDLES:
            with contextlib.suppress(OSError):
                os.remove(os.path.join(kodiutil.PROFILE, old))
    _bundle = bundle
    return bundle


def drop_distrusted(pem):
    """Return certifi's cacert.pem text without the DISTRUSTED roots (each entry starts with its "# Issuer:" lines)."""
    entries = re.split(r"\n(?=# Issuer: )", pem)
    return "\n".join(e for e in entries if not any('# Label: "%s"' % label in e for label in DISTRUSTED))


def _certifi_file():
    """Return certifi's cacert.pem, found without importing certifi (its import pulls in much more)."""
    import importlib.util

    spec = importlib.util.find_spec("certifi")
    path = os.path.join(os.path.dirname(spec.origin), "cacert.pem") if spec and spec.origin else ""
    if os.path.exists(path):
        return path
    import certifi

    return certifi.where()
