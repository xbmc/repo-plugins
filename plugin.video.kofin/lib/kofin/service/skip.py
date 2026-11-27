"""The kofin overlay: Skip <segment> / Play Next / Close.

Non-modal: ``show()`` returns immediately and the segment tick owns the
lifetime (auto-close past the segment end, autoplay countdown). Button actions
run through the injected callbacks — there is no monitor loop.

Buttons appear when their label property is non-empty; the skin binds
visibility to the properties, so one XML serves every overlay variant.
"""

from typing import Any, Callable, Optional

import xbmcgui

from kofin.core import settings
from kofin.core.log import Logger

LOG = Logger(__name__)

ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

SKIP_BUTTON = 3012
CLOSE_BUTTON = 3013
PLAY_NEXT_BUTTON = 3014

XML_FILENAME = "script-kofin-skip.xml"

Callback = Callable[[], None]


def open_overlay(
    skip_label: str,
    skip_duration: str,
    next_label: str,
    next_info: str,
    on_skip: Optional[Callback],
    on_play_next: Optional[Callback],
) -> "SkipOverlay":
    """Build and show the overlay; empty labels hide their buttons."""
    overlay = SkipOverlay(
        XML_FILENAME,
        settings.addon_path(),
        "default",
        "1080i",
        skip_label=skip_label,
        skip_duration=skip_duration,
        next_label=next_label,
        next_info=next_info,
        on_skip=on_skip,
        on_play_next=on_play_next,
    )
    overlay.show()
    return overlay


class SkipOverlay(xbmcgui.WindowXMLDialog):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._on_skip: Optional[Callback] = kwargs.pop("on_skip", None)
        self._on_play_next: Optional[Callback] = kwargs.pop("on_play_next", None)
        skip_label: str = kwargs.pop("skip_label", "")
        skip_duration: str = kwargs.pop("skip_duration", "")
        next_label: str = kwargs.pop("next_label", "")
        next_info: str = kwargs.pop("next_info", "")
        self.closed = False
        super().__init__(*args)
        self.setProperty("kofin.skip.label", skip_label)
        # The skin appends this in brackets, so an empty value renders nothing.
        self.setProperty("kofin.skip.duration", skip_duration)
        self.setProperty("kofin.next.label", next_label)
        self.setProperty("kofin.next.info", next_info)
        self.setProperty("kofin.close.label", settings.localized(30487))

    def set_countdown(self, seconds: int) -> None:
        """Autoplay countdown shown on the Play Next button; 0 clears it."""
        self.setProperty("kofin.countdown", str(seconds) if seconds > 0 else "")

    def close(self) -> None:
        self.closed = True
        try:
            super().close()
        except Exception:  # window already torn down with the player
            pass

    def onAction(self, action: xbmcgui.Action) -> None:
        action_id = action.getId()
        if action_id in (ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self.close()
        elif action_id == ACTION_SELECT_ITEM:
            # Over fullscreen video the overlay's focus sits on the grouplist,
            # so a button press arrives here as an action rather than firing
            # onClick — route it to the focused button ourselves.
            self.onClick(self.getFocusId())

    def onClick(self, control_id: int) -> None:
        if self.closed:
            return  # idempotent: a select routed via onAction must not re-run
        if control_id == SKIP_BUTTON and self._on_skip is not None:
            self._run(self._on_skip)
        elif control_id == PLAY_NEXT_BUTTON and self._on_play_next is not None:
            self._run(self._on_play_next)
        if control_id in (SKIP_BUTTON, CLOSE_BUTTON, PLAY_NEXT_BUTTON):
            self.close()

    def _run(self, callback: Callback) -> None:
        try:
            callback()
        except Exception:
            LOG.exception("overlay action failed")
