"""Jellyfin account settings: the server-side preferences kofin already obeys.

Jellyfin resolves each playback's default audio and subtitle track against the
*account* rather than the client, and returns the result on every MediaSource
— which ``service/player.apply_default_tracks`` applies at first frame. The
preferences behind that resolution live only on the server.

This is the Account tab's button for them: read live from ``/Users/Me``, edited
in a ``Dialog.select`` loop, written straight back (:func:`updated`,
:func:`_save`).

Six of the sixteen ``UserConfiguration`` fields are here. The rest are left
alone deliberately: ``EnableNextEpisodeAutoPlay`` duplicates kofin's own
``playNextEnabled``, the display flags (``DisplayMissingEpisodes`` and kin)
change what ``/UserViews`` and ``/Items`` return and so would silently desync
the Kodi database, and the view lists overlap kofin's own library selection.
"""

from typing import Any, NamedTuple, Optional, Union
from collections.abc import Sequence

import xbmcgui

from kofin.core import settings, state, toast
from kofin.core.api import Api
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin.router import Request

LOG = Logger(__name__)

JsonDict = dict[str, Any]

STR_NO_SESSION = 30045
STR_HEADING = 30779
STR_ENABLED = 30786
STR_DISABLED = 30787
STR_ANY = 30788
STR_NOT_HONOURED = 30794
STR_LOAD_FAILED = 30795
STR_SAVE_FAILED = 30796
STR_NO_PERMISSION = 30797

BOOL = "bool"
ENUM = "enum"
LANGUAGE = "language"


class Field(NamedTuple):
    """One row: which configuration key it edits and how it is chosen."""

    key: str
    label: int
    kind: str
    # ENUM only: (server value, label string id), in the order the web client
    # offers them.
    options: tuple[tuple[str, int], ...] = ()


# The rows, in order. Audio, then subtitles, then the two "remember" flags —
# the grouping the web client uses, so someone who set these up there finds
# them where they expect.
FIELDS: tuple[Field, ...] = (
    Field("AudioLanguagePreference", 30780, LANGUAGE),
    Field("PlayDefaultAudioTrack", 30781, BOOL),
    Field("SubtitleLanguagePreference", 30782, LANGUAGE),
    Field(
        "SubtitleMode",
        30783,
        ENUM,
        (
            ("Default", 30789),
            ("Always", 30790),
            ("OnlyForced", 30791),
            ("None", 30792),
            ("Smart", 30793),
        ),
    ),
    Field("RememberAudioSelections", 30784, BOOL),
    Field("RememberSubtitleSelections", 30785, BOOL),
)


# -- pure helpers -------------------------------------------------------------


def language_options(cultures: Sequence[JsonDict]) -> list[tuple[str, str]]:
    """``(code, display name)`` pairs for a language row, "Any" first.

    Server order, which is alphabetical by display name. A culture with no
    three-letter code is dropped: that code *is* the stored value, so a
    language which has none cannot be expressed as a preference.
    """
    options = [("", settings.localized(STR_ANY))]
    for culture in cultures:
        code = str(culture.get("ThreeLetterISOLanguageName") or "")
        if not code:
            continue
        options.append((code, str(culture.get("DisplayName") or code)))
    return options


def language_label(code: str, cultures: Sequence[JsonDict]) -> str:
    """A language code's display name; never blank.

    An unlisted code falls back to itself rather than to "Any": a value some
    other client set against a different culture table is still the account's
    value.
    """
    if not code:
        return settings.localized(STR_ANY)
    for culture in cultures:
        if str(culture.get("ThreeLetterISOLanguageName") or "") == code:
            return str(culture.get("DisplayName") or code)
    return code


def value_label(field: Field, config: JsonDict, cultures: Sequence[JsonDict]) -> str:
    """How ``field``'s current value reads on its row."""
    value = config.get(field.key)
    if field.kind == BOOL:
        return settings.localized(STR_ENABLED if value else STR_DISABLED)
    if field.kind == LANGUAGE:
        return language_label(str(value or ""), cultures)
    for option, label in field.options:
        if option == value:
            return settings.localized(label)
    return str(value or "")


def row_labels(
    config: JsonDict, cultures: Sequence[JsonDict], honoured: bool
) -> list[str]:
    """The menu's rows: one per field, and the caveat when kofin ignores them.

    With ``honourJellyfinDefaultTracks`` off nothing here reaches playback on
    this box, though it stays true of the account and of every other client.
    Saying so beats a dialog that appears to work and does nothing.
    """
    rows = [
        "%s: %s"
        % (settings.localized(field.label), value_label(field, config, cultures))
        for field in FIELDS
    ]
    if not honoured:
        rows.append(settings.localized(STR_NOT_HONOURED))
    return rows


def updated(config: JsonDict, key: str, value: Any) -> JsonDict:
    """``config`` with one key replaced and everything else carried through.

    The copy is the whole point. ``/Users/Configuration`` replaces the
    document, so a write built from only the fields this dialog knows about
    would clear the account's home-screen layout (``OrderedViews``,
    ``GroupedFolders``), its Latest exclusions and its cast receiver — none of
    which anything here has any business touching.
    """
    changed = dict(config)
    changed[key] = value
    return changed


# -- the dialog ---------------------------------------------------------------


def jellyfin_settings(request: Request) -> None:
    """Account-tab button: edit the logged-in user's Jellyfin preferences."""
    creds = Credentials.load()
    if not creds.is_logged_in:
        return
    if not state.is_online():
        toast.show(settings.localized(STR_NO_SESSION), time_ms=4000)
        return

    api = Api.for_plugin(creds)
    try:
        user = api.me()
        cultures = api.cultures()
    except JellyfinError as error:
        LOG.warning("jellyfin settings: load failed: %s", error)
        toast.show(settings.localized(STR_LOAD_FAILED), toast.ERROR, time_ms=4000)
        return

    policy = user.get("Policy") or {}
    if not policy.get("EnableUserPreferenceAccess", True):
        # Refused up front rather than on the first write: the server answers
        # that with a 403, and the transport folds 401 and 403 into the same
        # Unauthorized, so afterwards there is no way to tell "not allowed"
        # from "signed out" and say which.
        toast.show(settings.localized(STR_NO_PERMISSION), toast.WARNING, time_ms=5000)
        return

    _run_menu(api, creds, dict(user.get("Configuration") or {}), cultures)


def _run_menu(
    api: Api, creds: Credentials, config: JsonDict, cultures: Sequence[JsonDict]
) -> None:
    heading = settings.localized(STR_HEADING) % (creds.display_user or "")
    row = 0
    while True:
        # Read the toggle each pass: it lives in the settings dialog this menu
        # is sitting on top of, so it can change underneath.
        honoured = settings.get_bool("honourJellyfinDefaultTracks")
        labels: list[Union[str, xbmcgui.ListItem]] = list(
            row_labels(config, cultures, honoured)
        )
        row = xbmcgui.Dialog().select(heading, labels, preselect=row)
        if row < 0:
            return  # backed out; every change is already saved
        if row >= len(FIELDS):
            continue  # the caveat row is a caption, not a choice

        field = FIELDS[row]
        value = _ask(field, config, cultures)
        if value is None or value == config.get(field.key):
            continue
        config = _save(api, config, field, value)


def _ask(field: Field, config: JsonDict, cultures: Sequence[JsonDict]) -> Optional[Any]:
    """The chosen value for a row, or None when the user backed out.

    A boolean flips on the spot; the others open a list positioned on the
    current value.
    """
    current = config.get(field.key)
    if field.kind == BOOL:
        return not bool(current)

    if field.kind == LANGUAGE:
        # A never-set preference comes back absent rather than empty, and the
        # "Any" option is "" — normalise so it still preselects.
        current = str(current or "")
        options = language_options(cultures)
    else:
        options = [(value, settings.localized(label)) for value, label in field.options]

    preselect = next(
        (index for index, option in enumerate(options) if option[0] == current), -1
    )
    labels: list[Union[str, xbmcgui.ListItem]] = [label for _, label in options]
    chosen = xbmcgui.Dialog().select(
        settings.localized(field.label), labels, preselect=preselect
    )
    if chosen < 0:
        return None
    return options[chosen][0]


def _save(api: Api, config: JsonDict, field: Field, value: Any) -> JsonDict:
    """Post the change; keep the old configuration when the server refuses.

    Returning the unchanged dict on failure is what stops the menu drifting
    away from the server: the next redraw shows what the account actually
    holds, not what was asked for.
    """
    changed = updated(config, field.key, value)
    try:
        api.update_user_configuration(changed)
    except JellyfinError as error:
        LOG.warning("jellyfin settings: saving %s failed: %s", field.key, error)
        toast.show(settings.localized(STR_SAVE_FAILED), toast.ERROR, time_ms=4000)
        return config
    LOG.debug("jellyfin settings: %s -> %r", field.key, value)
    return changed
