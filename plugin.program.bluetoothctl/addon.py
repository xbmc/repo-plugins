from functools import wraps
from subprocess import CompletedProcess
from typing import Any, Callable, Dict
import xbmcplugin  # type: ignore
from resources.lib.plugin import Plugin, Action, LOGDEBUG
from resources.lib.plugin import NOTIFICATION_INFO, NOTIFICATION_ERROR
from resources.lib.bluetoothctl import Bluetoothctl
from resources.lib.busy_dialog import busy_dialog

plugin = Plugin()

bluetoothctl_path = plugin.get_setting('bluetoothctl_path')
plugin.log(LOGDEBUG, f'fetched bluetoothctl path {bluetoothctl_path}')
bluetoothctl_timeout = int(plugin.get_setting('bluetoothctl_timeout'))
plugin.log(LOGDEBUG, f'fetched bluetoothctl timeout {bluetoothctl_timeout}')

bt = Bluetoothctl(executable=bluetoothctl_path,
                  scan_timeout=bluetoothctl_timeout)


@plugin.action()
def root(params: Dict[str, str]) -> None:
    """
    The default (starting) action.

    params: Dictionary of query string parameters passed to the plugin. Uses
        none.
    """
    xbmcplugin.addDirectoryItem(
        handle=plugin.handle,
        url=plugin.build_url(action='paired_devices'),
        listitem=plugin.list_item(plugin.localise(30201)),
        isFolder=True
    )
    xbmcplugin.addDirectoryItem(
        handle=plugin.handle,
        url=plugin.build_url(action='available_devices'),
        listitem=plugin.list_item(plugin.localise(30202)),
        isFolder=True
    )

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.action()
def available_devices(params: Dict[str, str]) -> None:
    """
    Show available, unpaired devices.

    params: Dictionary of query string parameters passed to the plugin. Uses
        none.
    """
    with busy_dialog():
        process = bt.scan()

    log_completed_process(process)

    # Get available devices
    devices = get_available_devices(bt)

    # Remove paired devices from list
    paired_devices = get_paired_devices(bt)
    for device in paired_devices.keys():
        devices.pop(device, None)

    # Create a list of devices
    for device, address in devices.items():
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            url=plugin.build_url(action='device', device=device,
                                 address=address, paired=False),
            listitem=plugin.list_item(device),
            isFolder=True
        )

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.action()
def paired_devices(param: Dict[str, str]) -> None:
    """
    Show paired devices.

    params: Dictionary of query string parameters passed to the plugin. Uses
        none.
    """
    devices = get_paired_devices(bt)

    # Create a list of devices
    for device, address in devices.items():
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            url=plugin.build_url(action='device', device=device,
                                 address=address, paired=True),
            listitem=plugin.list_item(device),
            isFolder=True
        )

    xbmcplugin.endOfDirectory(plugin.handle)


def log_completed_process(process: CompletedProcess[Any]) -> None:
    command = ' '.join(process.args)
    if process.returncode == 0:
        plugin.log(LOGDEBUG, f'{command} successful')
        plugin.log(LOGDEBUG, f'stdout:\n{process.stdout}')
    else:
        plugin.log(LOGDEBUG, f'{command} failed')
        plugin.log(LOGDEBUG,
                   f'return code: {process.returncode}\n'
                   f'stdout:\n{process.stdout}\n'
                   f'stderr:\n{process.stderr}')


def get_available_devices(bt: Bluetoothctl) -> Dict[str, str]:
    """
    Create a dictionary of device name: device address for available devices.
    """
    process = bt.get_devices()

    log_completed_process(process)

    if process.returncode == 0:
        devices = bt.parse_devices_list(process.stdout)
    else:
        devices = {}

    return devices


def get_paired_devices(bt: Bluetoothctl) -> Dict[str, str]:
    """
    Create a dictionary of device name: device address for paired devices.
    """
    process = bt.get_paired_devices()

    log_completed_process(process)

    if process.returncode == 0:
        devices = bt.parse_devices_list(process.stdout)
    else:
        devices = {}

    return devices


@plugin.action()
def device(params: Dict[str, str]) -> None:
    """
    Device view. Presents a list of actions to take which depend on whether the
    device is paired or not.

    params: Dictionary of query string parameters passed to the plugin. Expects
        'device', 'address' and 'paired'.
    """
    # Unpack parameters
    device = params['device']
    address = params['address']
    paired = params['paired']

    if paired == str(True):
        # List actions for paired devices
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30203)),
            url=plugin.build_url(action='connect', device=device,
                                 address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30204)),
            url=plugin.build_url(action='disconnect', device=device,
                                 address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30206)),
            url=plugin.build_url(action='unpair', device=device,
                                 address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30207)),
            url=plugin.build_url(action='trust', device=device,
                                 address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30208)),
            url=plugin.build_url(action='untrust', device=device,
                                 address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30209)),
            url=plugin.build_url(action='info', device=device, address=address)
        )
    elif paired == str(False):
        # List actions for unpaired devices
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30205)),
            url=plugin.build_url(action='pair', device=device, address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30203)),
            url=plugin.build_url(action='connect', device=device,
                                 address=address)
        )
        xbmcplugin.addDirectoryItem(
            handle=plugin.handle,
            listitem=plugin.list_item(plugin.localise(30209)),
            url=plugin.build_url(action='info', device=device, address=address)
        )

    xbmcplugin.endOfDirectory(plugin.handle)


# Type signature for device action functions
DeviceAction = Callable[[Dict[str, str]], CompletedProcess[str]]


def device_action(success: str,
                  failure: str) -> Callable[[DeviceAction], Action]:
    """
    Decorator factory for actions which only call a bluetoothctl function on a
    device.

    success: Notification message upon success
    failure: Notification message upon failure
    """
    def decorator(func: DeviceAction) -> Action:
        nonlocal success
        nonlocal failure

        @wraps(func)
        def wrapper(params: Dict[str, str]) -> None:
            nonlocal success
            nonlocal failure

            process = func(params)

            log_completed_process(process)

            if process.returncode == 0:
                plugin.notification(success, NOTIFICATION_INFO)
            else:
                plugin.notification(failure, NOTIFICATION_ERROR)
        return wrapper
    return decorator


@plugin.action()
@device_action(success=plugin.localise(30310), failure=plugin.localise(30311))
def connect(params: Dict[str, str]) -> CompletedProcess[str]:
    """
    Connect to a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'address'.
    """
    address = params['address']

    with busy_dialog():
        process = bt.connect(address)

    return process


@plugin.action()
@device_action(success=plugin.localise(30320), failure=plugin.localise(30321))
def disconnect(params: Dict[str, str]) -> CompletedProcess[str]:
    """
    Disconnect from a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'address'.
    """
    address = params['address']

    with busy_dialog():
        process = bt.disconnect(address)

    return process


@plugin.action()
@device_action(success=plugin.localise(30330), failure=plugin.localise(30331))
def pair(params: Dict[str, str]) -> CompletedProcess[str]:
    """
    Pair with a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'address'.
    """
    address = params['address']

    with busy_dialog():
        process = bt.pair(address)

    return process


@plugin.action()
@device_action(success=plugin.localise(30340), failure=plugin.localise(30341))
def remove(params: Dict[str, str]) -> CompletedProcess[str]:
    """
    Remove (unpair) a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'address'.
    """
    address = params['address']

    with busy_dialog():
        process = bt.remove(address)

    return process


@plugin.action()
@device_action(success=plugin.localise(30350), failure=plugin.localise(30351))
def trust(params: Dict[str, str]) -> CompletedProcess[str]:
    """
    Trust a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'address'.
    """
    address = params['address']

    with busy_dialog():
        process = bt.trust(address)

    return process


@plugin.action()
@device_action(success=plugin.localise(30360), failure=plugin.localise(30361))
def untrust(params: Dict[str, str]) -> CompletedProcess[str]:
    """
    Revoke trust in a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'address'.
    """
    address = params['address']

    with busy_dialog():
        process = bt.trust(address)

    return process


@plugin.action()
def info(params: Dict[str, str]) -> None:
    """
    Show information about a device.

    params: Dictionary of query string parameters passed to the plugin. Uses
        'device', 'address'.
    """
    device = params['device']
    address = params['address']

    process = bt.info(address)

    log_completed_process(process)

    if process.returncode != 0:
        plugin.notification(plugin.localise(30370), NOTIFICATION_ERROR)
        return

    # Remove tabs from output as they do not render well in the textviewer
    text = process.stdout.replace('\t', '  ')

    plugin.dialog.textviewer(
        heading=device,
        text=text,
        usemono=True
    )


if __name__ == "__main__":
    plugin.run()
