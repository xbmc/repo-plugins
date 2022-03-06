from collections.abc import Generator
from contextlib import contextmanager
import xbmc  # type: ignore


@contextmanager
def busy_dialog() -> Generator[None, None, None]:
    """
    Display a busy dialog box.
    """
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
