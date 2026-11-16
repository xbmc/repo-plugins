"""SyncPlay menu: list/create/join groups, or manage the current one.

Blocks on dialogs; the service runs it on a dedicated worker thread, never on
the notification loop.
"""

from typing import TYPE_CHECKING, Union

import xbmcgui

from kofin.core import settings, toast
from kofin.core.log import Logger

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager


LOG = Logger(__name__)


def show_menu(manager: "SyncPlayManager") -> None:
    if manager.in_group():
        _group_menu(manager)
    else:
        _join_menu(manager)


def _join_menu(manager: "SyncPlayManager") -> None:
    groups = manager.list_groups()

    if groups is None:
        # A failed listing, not an empty one.
        toast.show(
            settings.localized(30574), toast.ERROR, heading="SyncPlay", time_ms=3000
        )
        return

    labels: list[Union[str, xbmcgui.ListItem]] = []

    for group in groups:
        participants = ", ".join(group.get("Participants") or [])
        labels.append(
            "%s  [%s]  %s"
            % (group.get("GroupName") or "?", group.get("State") or "?", participants)
        )

    labels.append(settings.localized(30561))  # New group…

    selection = xbmcgui.Dialog().select(settings.localized(30560), labels)

    if selection < 0:
        return

    if selection < len(groups):
        manager.join_group(groups[selection]["GroupId"])
        return

    name = xbmcgui.Dialog().input(
        settings.localized(30567),
        defaultt=settings.get_str("displayUser") or "Kodi",
    )

    if name:
        manager.new_group(name)


def _group_menu(manager: "SyncPlayManager") -> None:
    manager.refresh_group_info()
    group_name = (manager.group or {}).get("GroupName") or "?"
    members = _describe_members(manager)

    options: list[Union[str, xbmcgui.ListItem]] = [
        settings.localized(30562),  # Leave group
        "%s: %s" % (settings.localized(30572), members or "?"),  # Members
        settings.localized(30573),  # Resync
        (
            settings.localized(30580)
            if not manager.ignore_wait
            else settings.localized(30581)
        ),
    ]

    selection = xbmcgui.Dialog().select(
        "%s: %s" % (settings.localized(30560), group_name), options
    )

    if selection == 0:
        manager.leave_group()
    elif selection == 1:
        xbmcgui.Dialog().ok(
            "%s - %s" % (settings.localized(30560), group_name), members or "?"
        )
    elif selection == 2:
        manager.request_resync()
    elif selection == 3:
        manager.toggle_spectator()


def _describe_members(manager: "SyncPlayManager") -> str:
    parts = []

    for member in manager.members or []:
        if isinstance(member, dict):
            name = member.get("UserName") or "?"
            flags = []

            if member.get("IsBuffering"):
                flags.append(settings.localized(30577))

            if member.get("IsConnected") is False:
                flags.append(settings.localized(30582))

            parts.append("%s%s" % (name, (" (%s)" % ", ".join(flags)) if flags else ""))
        else:
            parts.append("%s" % member)

    return ", ".join(parts)
