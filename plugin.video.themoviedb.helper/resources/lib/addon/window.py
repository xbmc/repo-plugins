from xbmc import Monitor
from xbmcgui import Window, getCurrentWindowId
from resources.lib.addon.parser import try_type, try_int
from resources.lib.addon.plugin import executebuiltin, get_condvisibility, get_infolabel


def get_property(name, set_property=None, clear_property=False, window_id=None, prefix=None, is_type=None):
    if prefix != -1:
        prefix = prefix or 'TMDbHelper'
        name = f'{prefix}.{name}'
    if window_id == 'current':
        window_id = getCurrentWindowId()
    window = Window(window_id or 10000)  # Fallback to home window id=10000
    ret_property = set_property or window.getProperty(name)
    if clear_property:
        window.clearProperty(name)
    if set_property is not None:
        window.setProperty(name, f'{set_property}')
    return try_type(ret_property, is_type or str)


def _property_is_value(name, value):
    if not value and not get_property(name):
        return True
    if value and get_property(name) == value:
        return True
    return False


def wait_for_property(name, value=None, set_property=False, poll=1, timeout=10):
    """
    Waits until property matches value. None value waits for property to be cleared.
    Will set property to value if set_property flag is set. None value clears property.
    Returns True when successful.
    """
    xbmc_monitor = Monitor()
    if set_property:
        get_property(name, value) if value else get_property(name, clear_property=True)
    while (
            not xbmc_monitor.abortRequested() and timeout > 0
            and not _property_is_value(name, value)):
        xbmc_monitor.waitForAbort(poll)
        timeout -= poll
    del xbmc_monitor
    if timeout > 0:
        return True


def is_visible(window_id):
    return get_condvisibility(f'Window.IsVisible({window_id})')


def close(window_id):
    return executebuiltin(f'Dialog.Close({window_id})')


def activate(window_id):
    return executebuiltin(f'ActivateWindow({window_id})')


def _is_base_active(window_id):
    if window_id and not is_visible(window_id):
        return False
    return True


def _is_updating(container_id):
    is_updating = get_condvisibility(f"Container({container_id}).IsUpdating")
    is_numitems = try_int(get_infolabel(f"Container({container_id}).NumItems"))
    if is_updating or not is_numitems:
        return True


def _is_inactive(window_id, invert=False):
    if is_visible(window_id):
        return True if invert else False
    return True if not invert else False


def wait_until_active(window_id, instance_id=None, poll=1, timeout=30, invert=False):
    """
    Wait for window ID to open (or to close if invert set to True). Returns window_id if successful.
    Pass instance_id if there is also a base window that needs to be open underneath
    """
    xbmc_monitor = Monitor()
    while (
            not xbmc_monitor.abortRequested() and timeout > 0
            and _is_inactive(window_id, invert)
            and _is_base_active(instance_id)):
        xbmc_monitor.waitForAbort(poll)
        timeout -= poll
    del xbmc_monitor
    if timeout > 0 and _is_base_active(instance_id):
        return window_id


def wait_until_updated(container_id=9999, instance_id=None, poll=1, timeout=60):
    """
    Wait for container to update. Returns container_id if successful
    Pass instance_id if there is also a base window that needs to be open underneath
    """
    xbmc_monitor = Monitor()
    while (
            not xbmc_monitor.abortRequested() and timeout > 0
            and _is_updating(container_id)
            and _is_base_active(instance_id)):
        xbmc_monitor.waitForAbort(poll)
        timeout -= poll
    del xbmc_monitor
    if timeout > 0 and _is_base_active(instance_id):
        return container_id
