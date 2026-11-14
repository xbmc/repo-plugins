"""The plugin's requests to the service over localhost (see quickplay.ask), and the lists served there.

Lists are served from the service so the plugin loads neither the client nor the guide (most of a
list's time on a TV stick).
"""

import json

from resources.lib.data import channellist
from resources.lib.data import menucounts
from resources.lib.net import localserver


class Router:
    """Answer the plugin's requests: a GET with the token to a known path, in JSON; anything else is forbidden.

    :param token: the token each request carries (see quickplay.PROPERTY)
    :param routes: {path: handler(query)}, each returning its JSON answer
    """

    def __init__(self, token, routes):
        self._token = token
        self._routes = routes

    def respond(self, request):
        """Answer a request (a localserver.Request) with its handler's answer, or 403."""
        handler = self._routes.get(request.path)
        if request.method != "GET" or handler is None or request.query.get("token") != self._token:
            status, answer = 403, {"error": "forbidden"}
        else:
            status, answer = 200, handler(request.query)
        return localserver.Response(status, json.dumps(answer).encode(), "application/json")


class Lists:
    """What a channel list and the main menu show, from the client the service's streams share.

    :param shared_client: shared_client() returns that client (see clientfactory.shared_client)
    """

    def __init__(self, shared_client):
        self._shared_client = shared_client

    def list_view(self, scope):
        """Return what a channel list shows (see channellist.view), or {"error": kind, "message"}."""
        try:
            return channellist.view(self._current_client(), scope)
        except Exception as e:  # noqa: BLE001 - the plugin makes the list itself then, and says what failed
            return error_answer(e)

    def menu_counts(self):
        """Return what the main menu says beside its rows (see menucounts.counts), or {"error": kind, "message"}."""
        try:
            return menucounts.counts(self._current_client())
        except Exception as e:  # noqa: BLE001 - the plugin makes them itself then
            return error_answer(e)

    def _current_client(self):
        """Return the shared client with what the plugin changed taken up (a favourite, the order)."""
        client = self._shared_client()
        client.sync()
        return client


def error_answer(e):
    """Return a failure as the plugin's answer: its kind, for quickplay's message (see provider.ApiError), and text."""
    return {"error": getattr(e, "kind", None) or "api", "message": str(e)}
