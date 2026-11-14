"""LAN receiver for logging in from a phone.

A human logs in on a phone and sends back the address the login ends on: Kodi's QR code opens
GET /?c=<code>, a page with the login button and a field for the final address, posted to /login.

It runs only while the login dialog is open and requires the code Kodi shows. Its
texts are the add-on's strings (see TEXT_IDS), in Kodi's language.
"""

import html
import secrets
from urllib.parse import parse_qs
from xml.sax.saxutils import quoteattr

from resources.lib.net import localserver

PORT = 47913
# The page's texts by name: the add-on's string ids (the caller gives the texts, see LoginReceiver).
TEXT_IDS = {
    "heading": 30244,
    "button": 30245,
    "button_note": 30246,
    "copy": 30247,
    "copy_how": 30248,
    "send_note": 30249,
    "send": 30250,
    "done": 30251,
    "done_note": 30252,
    "bad_code": 30253,
    "wrong_code": 30254,
    "page_text": 30255,
    "no_login": 30256,
}

_STYLE = (
    "body{font-family:sans-serif;max-width:32em;margin:1.2em auto;padding:0 1em;line-height:1.45;"
    "background:#fff;color:#222}h1{color:#e20074;font-size:1.4em}"
    "a.btn,button{display:block;width:100%;box-sizing:border-box;padding:.9em;margin:.6em 0;border:0;"
    "border-radius:.5em;background:#e20074;color:#fff;font-size:1.1em;text-align:center;text-decoration:none}"
    "textarea{width:100%;box-sizing:border-box;height:7em;font-size:.9em}ol{padding-left:1.2em}"
    "li{margin:.6em 0}.ok{color:#080;font-weight:bold}.err{color:#c00;font-weight:bold}"
)

# Where the provider's login ends: the address the phone sends back starts so.
TOKEN_PAGE = "https://player.telekomtvgo.hu/robots.txt?"

_HEAD = """<!doctype html><html lang=%(lang)s><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%(heading)s</title>
<style>%(style)s</style></head><body><h1>%(heading)s</h1>"""

_PAGE = """%(head)s%(msg)s
<ol>
<li><a class="btn" href=%(login)s target="_blank" rel="noopener">%(button)s</a>
%(button_note)s</li>
<li>%(copy)s <code>%(token_page)s…</code><br>%(copy_how)s</li>
<li>%(send_note)s
<form method="post" action="/login"><input type="hidden" name="code" value=%(code)s>
<textarea name="token" placeholder="%(token_page)s...refresh_token=..."></textarea>
<button type="submit">%(send)s</button></form></li>
</ol></body></html>"""

_DONE = """%(head)s<p class="ok">%(done)s</p><p>%(done_note)s</p></body></html>"""


class LoginReceiver:
    """Serve the phone's login page in a thread until stopped; `token` holds what the phone sent.

    :param login_url: the provider's login address the page's button opens
    :param texts: the page's texts by name (see TEXT_IDS)
    :param lang: their language, as the page declares it ("hu")
    :param port: the port to listen on; if it is taken, any free one (see `port`)
    """

    def __init__(self, login_url, texts, lang="", port=PORT):
        # Only in the QR code, so length costs nothing; a short one could be guessed over the LAN.
        self.code = secrets.token_urlsafe(8)
        self.token = None
        # Escaped once: the texts are plain, the page is HTML.
        self._texts = {name: html.escape(texts[name]) for name in TEXT_IDS}
        self._lang = lang
        self._login_url = login_url
        # A browser's idle or speculative connection must not hold up the real one.
        try:
            self._server = localserver.start(self.respond, "0.0.0.0", port, request_timeout=10)
        except OSError:
            self._server = localserver.start(self.respond, "0.0.0.0", request_timeout=10)
        self.port = localserver.port(self._server)

    def respond(self, request):
        """Answer the phone: the page for GET with the code, the token taken from POST /login."""
        if request.method == "POST":
            return self._take_token(request)
        if not self.accepts(request.query.get("c", "")):
            return _html(403, "<p>%s</p>" % self._texts["bad_code"])
        return _html(200, self._page())

    def _take_token(self, request):
        form = {k: v[0] for k, v in parse_qs(request.body.decode("utf-8", "replace")).items()}
        if request.path != "/login" or not self.accepts(form.get("code") or ""):
            return _html(403, "<p>%s</p>" % self._texts["wrong_code"])
        token = (form.get("token") or "").strip()
        if "refresh_token=" not in token and token.count(".") != 2:
            # The usual slip: the page's text instead of its address.
            slip = "user-agent" in token.lower() or "disallow" in token.lower()
            return _html(400, self._page('<p class="err">%s</p>' % self._texts["page_text" if slip else "no_login"]))
        self.token = token
        return _html(200, _DONE % dict(self._texts, head=self._head()))

    def accepts(self, code):
        """Return whether a request carries the code Kodi shows (compared in constant time)."""
        return secrets.compare_digest(code.encode(), self.code.encode())

    def _head(self):
        return _HEAD % {"lang": quoteattr(self._lang), "heading": self._texts["heading"], "style": _STYLE}

    def _page(self, msg=""):
        values = dict(self._texts, head=self._head(), msg=msg, token_page=html.escape(TOKEN_PAGE))
        return _PAGE % dict(values, login=quoteattr(self._login_url), code=quoteattr(self.code))

    def phone_url(self, host):
        """Return the address the QR code shows, for the phone to open on this host."""
        return "http://%s:%d/?c=%s" % (host, self.port, self.code)

    def stop(self):
        """Stop serving and close the socket."""
        localserver.stop(self._server)


def _html(status, page):
    return localserver.Response(status, page.encode("utf-8"), "text/html; charset=utf-8", [("Cache-Control", "no-store")])
