"""'Who's watching?' — the service half, and the feature's vocabulary.

The session's primary (logged-in) user owns the session and is permanent:
Jellyfin no-ops any attempt to add it as an additional user and offers no way
to remove it, so it is shown in the dialog title rather than the toggle list.
Everyone else is a checkbox; confirming applies the add/remove deltas.

The Advanced tab's shortlist (``whoIsWatchingShortlist``) narrows that list to
the handful of people who actually watch on this device — a server with fifty
accounts otherwise makes the dialog useless. Its first row is "All", and
selecting nothing at all switches the whole feature off: the root entry goes
away and whoever is on the session is detached (:func:`detach_all`).

The chosen set is also written to the hidden ``whoIsWatching`` setting so the
service can re-attach those users when a new session comes up after a Kodi
restart or websocket reconnect. Jellyfin sessions do not survive either.

The picker runs in the **service**, like SyncPlay's menu; the route handlers
stay in ``plugin/adduser.py`` and call into this module.
"""

from contextlib import AbstractContextManager
from typing import Any, Callable, Optional
from collections.abc import Sequence

import xbmc
import xbmcgui

from kofin.core import settings, state, toast
from kofin.core.api import Api
from kofin.core.http import JellyfinError, Unauthorized
from kofin.core.log import Logger
from kofin.service.ports import no_modal
from kofin.core.settings import Credentials

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# Hidden setting holding the additional-user ids to re-apply on session start.
# Empty means nobody extra (unlike the shortlist, where empty means everyone).
WHO_IS_WATCHING = "whoIsWatching"

# The shortlist, and the three states it has to express: offer everyone, offer
# exactly these ids, or do not offer the feature at all. Two sentinels rather
# than one because a bare id list cannot tell "everyone" and "nobody" apart,
# and they are safe as sentinels because a Jellyfin user id is a 32-character
# hex GUID.
#
# Empty reads as everyone: installs from before the "All" row hold it, and an
# unreadable settings store reads every key empty (settings.get_addon).
SHORTLIST = "whoIsWatchingShortlist"
SHORTLIST_ALL = "all"  # the dialog's first row, and the shipped default
SHORTLIST_NOBODY = "none"  # nothing selected — the feature is off


def shortlist_setting() -> list[str]:
    """The shortlist as stored, one settings read for both readers below."""
    return settings.get_list(SHORTLIST)


def is_enabled(tokens: Optional[Sequence[str]] = None) -> bool:
    """Whether "Who's watching?" is offered at all.

    Off only for the exact value the picker writes when nothing is selected.
    Anything else — an id list, the ALL sentinel, empty, something hand-edited
    — reads as on, because the degrade has to be "the entry is there" rather
    than "the entry is gone and the session was stripped".
    """
    if tokens is None:
        tokens = shortlist_setting()
    return list(tokens) != [SHORTLIST_NOBODY]


def offered_ids(tokens: Sequence[str]) -> list[str]:
    """The ids the toggle dialog narrows to; empty means everyone.

    Only meaningful once :func:`is_enabled` has said yes — the disabled value
    reads as "everyone" here, which is why every caller asks that first.
    """
    if SHORTLIST_ALL in tokens:
        return []
    return [token for token in tokens if token != SHORTLIST_NOBODY]


def offerable(
    users: Sequence[JsonDict],
    primary_id: str,
    shortlist: Sequence[str],
    on_session: set[Optional[str]],
) -> list[JsonDict]:
    """The users the toggle dialog lists.

    The primary user is never offered (it owns the session and cannot be
    added or removed). An empty shortlist means "everyone". A user already on
    the session is always listed even when the shortlist has since dropped
    them — otherwise the only way to take them back off would be to put them
    back on the shortlist first.
    """
    eligible = [user for user in users if user.get("Id") != primary_id]
    if not shortlist:
        return eligible
    allowed = set(shortlist)
    return [
        user
        for user in eligible
        if user.get("Id") in allowed or user.get("Id") in on_session
    ]


def users_to_restore(desired: Sequence[str], on_session: set[str]) -> list[str]:
    """Ids in ``desired`` that are not already on the session.

    Order follows ``desired`` so the setting's left-to-right order is the
    restore order. Empty entries are dropped; the primary user is never in
    this list when the dialog wrote it, but a stale id is harmless (Jellyfin
    no-ops adding the session owner).
    """
    already = set(on_session)
    restored: list[str] = []
    for user_id in desired:
        if not user_id or user_id in already:
            continue
        restored.append(user_id)
        already.add(user_id)  # de-dupe within desired itself
    return restored


def persist_who_is_watching(user_ids: Sequence[Optional[str]]) -> None:
    """Write the full chosen set. Empty clears the setting ("nobody extra")."""
    cleaned = [str(user_id) for user_id in user_ids if user_id]
    settings.set_str(WHO_IS_WATCHING, ",".join(cleaned))


def session_watching_names(session: JsonDict) -> list[str]:
    """The additional-user display names a session dict reports."""
    return [
        str(user.get("UserName"))
        for user in (session.get("AdditionalUsers") or [])
        if user.get("UserName")
    ]


def detach_all(api: Api, device_id: str) -> None:
    """Take every co-watcher off this device's session and forget the saved set.

    What "disabled" means past hiding the root entry. Users left attached to a
    session whose picker is gone would be stranded there — the toggle dialog is
    the only way off one — so switching the feature off detaches them.

    Called both by the disable itself and by the connect-time restore, which is
    how a disable made while the server was unreachable still lands: the next
    session it sees is stripped instead of restored.
    """
    persist_who_is_watching([])
    try:
        sessions = api.device_sessions(device_id)
    except JellyfinError as error:
        LOG.warning("who's-watching detach: session lookup failed: %s", error)
        return
    session = sessions[0] if sessions else {}
    session_id = session.get("Id", "")
    attached = [
        str(user.get("UserId"))
        for user in (session.get("AdditionalUsers") or [])
        if user.get("UserId")
    ]
    if not session_id or not attached:
        state.set_watching_names([])
        return

    for user_id in attached:
        try:
            api.session_remove_user(session_id, user_id)
            LOG.debug("who's-watching detached user %s", user_id)
        except JellyfinError as error:
            LOG.warning("who's-watching detach failed for %s: %s", user_id, error)
    _publish_from_server(api, device_id)


def restore_additional_users(api: Api, device_id: str) -> None:
    """Re-attach saved additional users to the current device session.

    Best-effort and additive only: removals happen through the picker, not
    here. A missing session or a failed add is logged and skipped so a
    websocket connect path is never taken down by this.

    Also the connect-time publisher of ``state.PROP_WHO_NAMES``: the session
    is fetched before the desired-set check (not after) because the root
    listing's label renders from that property alone, and a session that
    already carries co-watchers — say, attached by another client — must show
    them even when this device saved none.
    """
    if not is_enabled():
        detach_all(api, device_id)
        return

    try:
        sessions = api.device_sessions(device_id)
    except JellyfinError as error:
        LOG.warning("who's-watching restore: session lookup failed: %s", error)
        return
    if not sessions:
        LOG.debug("who's-watching restore: no device session yet")
        return

    session = sessions[0]
    session_id = session.get("Id", "")
    if not session_id:
        return

    on_session = {
        str(user.get("UserId"))
        for user in (session.get("AdditionalUsers") or [])
        if user.get("UserId")
    }
    desired = settings.get_list(WHO_IS_WATCHING)
    # Never try to re-add the primary user; Jellyfin no-ops it, but a stale
    # setting from a previous primary should not spam the log either.
    primary = api.user_id or ""
    missing = [
        user_id
        for user_id in users_to_restore(desired, on_session)
        if user_id != primary
    ]
    if not missing:
        state.set_watching_names(session_watching_names(session))
        return

    for user_id in missing:
        try:
            api.session_add_user(session_id, user_id)
            LOG.debug("who's-watching restored user %s", user_id)
        except JellyfinError as error:
            LOG.warning("who's-watching restore failed for %s: %s", user_id, error)
    _publish_from_server(api, device_id)


def _publish_from_server(api: Api, device_id: str) -> None:
    """Re-read the session and publish its co-watcher names — server truth
    after a mutation, since a partial failure leaves any reconstruction
    guessing. Best effort: a failed read keeps the previous property."""
    try:
        sessions = api.device_sessions(device_id)
    except JellyfinError as error:
        LOG.debug("who's-watching publish skipped: %s", error)
        return
    if sessions:
        state.set_watching_names(session_watching_names(sessions[0]))


def show_picker(
    api: Api,
    creds: Credentials,
    modal: Callable[[str], AbstractContextManager[None]] = no_modal,
) -> None:
    """Toggle additional users on this device's session. Blocks on a dialog —
    the service runs it on a dedicated worker thread, and ``modal`` is the
    service's record of the dialog, closed at shutdown."""
    tokens = shortlist_setting()
    if not is_enabled(tokens):
        # Checked before the round trips: the route gates this too, but the IPC
        # can outlive a shortlist emptied while the picker request was in flight.
        LOG.debug("who's-watching picker suppressed: the feature is off")
        return

    try:
        sessions = api.device_sessions(creds.device_id)
    except JellyfinError as error:
        LOG.warning("session lookup failed: %s", error)
        sessions = []
    if not sessions:
        toast.show(settings.localized(30045), time_ms=4000)
        return
    session = sessions[0]
    # Free re-sync of the root label while the data is in hand: the property
    # is normally maintained by the picker's own confirm path and the connect
    # restore, but a set changed elsewhere (another client, the dashboard)
    # would otherwise stay stale until the next reconnect.
    state.set_watching_names(session_watching_names(session))
    current_ids = {u.get("UserId") for u in (session.get("AdditionalUsers") or [])}

    try:
        users = api.users()
    except Unauthorized:
        users = api.public_users()
    except JellyfinError as error:
        LOG.warning("user list unavailable: %s", error)
        return

    eligible = offerable(users, api.user_id, offered_ids(tokens), current_ids)
    if not eligible:
        return
    names = [user.get("Name", "") for user in eligible]
    preselect = [
        index for index, user in enumerate(eligible) if user.get("Id") in current_ids
    ]

    title = settings.localized(30047) % (creds.display_user or "")
    with modal("selectdialog"):
        chosen = xbmcgui.Dialog().multiselect(title, names, preselect=preselect)
    if chosen is None:
        return  # cancelled; the session and the saved set are left as-is

    # Preserve dialog order so the setting is stable across confirms.
    picked_ids = [eligible[index].get("Id") for index in chosen]
    picked_set = {user_id for user_id in picked_ids if user_id}
    # Persist the intended set before the API round trips so a partial failure
    # still re-applies on the next session (service restore retries).
    persist_who_is_watching(picked_ids)

    session_id = session.get("Id", "")
    changed = False
    try:
        for user in eligible:
            user_id = user.get("Id", "")
            was_on = user_id in current_ids
            now_on = user_id in picked_set
            if now_on and not was_on:
                api.session_add_user(session_id, user_id)
                changed = True
            elif was_on and not now_on:
                api.session_remove_user(session_id, user_id)
                changed = True
    except JellyfinError as error:
        LOG.warning("session user change failed: %s", error)

    if changed:
        # Before the refresh below, so the redrawn root reads the new names.
        _publish_from_server(api, creds.device_id)

    if changed and xbmc.getCondVisibility("Window.IsMedia"):
        # Redraw the addon root so the "Who's watching?" entry re-reads the
        # session and shows the updated additional-user names. Only with a
        # media window up; otherwise there is no container to refresh.
        xbmc.executebuiltin("Container.Refresh")
