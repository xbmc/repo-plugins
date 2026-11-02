"""The provider's client: its parts, each with its own job, sharing one state and one API."""

import os

from resources.lib.provider import auth
from resources.lib.provider import channels
from resources.lib.provider import core
from resources.lib.provider import guide
from resources.lib.provider import personal
from resources.lib.provider import playback
from resources.lib.provider import statefile


class _Part:
    """A Client attribute that is one of its parts': the method or value of that name there.

    The add-on asks the client, not its parts (they are the client's own business).
    """

    def __init__(self, part, name=None):
        self._part = part
        self._name = name

    def __set_name__(self, owner, name):
        self._name = self._name or name

    def __get__(self, client, owner=None):
        if client is None:
            return self
        return getattr(getattr(client, self._part), self._name)

    def __set__(self, client, value):
        setattr(getattr(client, self._part), self._name, value)


class Client:
    """The provider's client for the add-on.

    Its parts: `auth` the login, the account and its devices; `channels` the channel lists;
    `personal` the account's own lists and settings; `guide` the guide and info pages; `playback`
    stream sessions; `state` what they keep (session.json), shared with every other client of the
    profile. The add-on uses the client's own attributes below, each one of a part's.

    :param profile_dir: where its state (session.json) is kept
    :param ca_bundle: certificates to verify the web player's host with (see core.Api)
    :param debug: debug(message), where the client's measurements go (state file, startup page)
    :param lock_wait: lock_wait(seconds) waits for the state file's lock, True to give up (Kodi exiting)
    """

    # The login and the account.
    authed = _Part("auth")
    guest = _Part("auth")
    device_id = _Part("auth")
    is_logged_in = _Part("auth")
    login_expires = _Part("auth")
    login_url = _Part("auth")
    login_with_refresh_token = _Part("auth")
    logout = _Part("auth")
    valid_account = _Part("auth")
    devices = _Part("auth")
    remove_device = _Part("auth")
    # The channel lists.
    channel_list = _Part("channels", "list")
    channel_of = _Part("channels")
    station_of = _Part("channels")
    subscribed_ids = _Part("channels")
    # The account's own lists and settings.
    parental_lock_enabled = _Part("personal")
    verify_pin = _Part("personal")
    set_favourite_channel = _Part("personal")
    channel_order = _Part("personal")
    set_channel_order = _Part("personal")
    watchlist = _Part("personal")
    set_watchlist = _Part("personal")
    season = _Part("personal")
    airings = _Part("personal")
    offers = _Part("personal")
    bookmarks = _Part("personal")
    set_bookmark = _Part("personal")
    delete_bookmarks = _Part("personal")
    # The guide and the info pages.
    now_and_next = _Part("guide")
    programme_at = _Part("guide")
    epg_blocks = _Part("guide")
    epg_stats = _Part("guide")
    details = _Part("guide")
    # Stream sessions.
    play_live = _Part("playback")
    licence_headers = _Part("playback")
    beacon = _Part("playback")
    close_stale_sessions = _Part("playback")
    get_ready = _Part("playback")
    # What other clients of the profile wrote, taken up (and this one's changes written).
    reload = _Part("state", "save")

    def __init__(self, profile_dir, ca_bundle=None, debug=None, lock_wait=None):
        self.state = statefile.State(os.path.join(profile_dir, core.STATE_FILE), debug=debug, lock_wait=lock_wait)
        self._api = core.Api(self.state, ca_bundle, debug=debug)
        self.auth = auth.Auth(self.state, self._api)
        self.channels = channels.Channels(self.state, self._api, self.auth)
        self.personal = personal.Personal(self.state, self._api, self.auth, self.channels)
        self.guide = guide.Guide(self._api, self.auth)
        self.playback = playback.Playback(self.state, self._api, self.auth, self.channels)

    @property
    def ca_bundle(self):
        """Return the certificates the provider's hosts are verified with (for a stream's own HTTP session)."""
        return self._api.ca_bundle
