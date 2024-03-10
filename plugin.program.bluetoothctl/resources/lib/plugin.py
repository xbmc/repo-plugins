import sys
from typing import Any, Callable, Optional, Dict
import urllib.parse
import xbmc  # type: ignore
import xbmcaddon  # type: ignore
import xbmcgui  # type: ignore


class PluginException(Exception):
    """
    Exception for Plugin class.
    """
    pass


# Type signature for action functions
Action = Callable[[Dict[str, str]], None]

# Define log levels
LOGDEBUG = xbmc.LOGDEBUG
LOGINFO = xbmc.LOGINFO
LOGWARNING = xbmc.LOGWARNING
LOGERROR = xbmc.LOGERROR
LOGFATAL = xbmc.LOGFATAL

# Define icons
NOTIFICATION_INFO = xbmcgui.NOTIFICATION_INFO
NOTIFICATION_WARNING = xbmcgui.NOTIFICATION_WARNING
NOTIFICATION_ERROR = xbmcgui.NOTIFICATION_ERROR


class Plugin:
    """
    Provide useful functions for plugin development.
    """
    def __init__(self) -> None:
        """
        Construct a Plugin instance.
        """
        # Extract information from arguments
        self._base_url = sys.argv[0]
        self._handle = int(sys.argv[1])
        self._params = urllib.parse.parse_qs(sys.argv[2][1:])

        # Get Addon instance
        self._addon = xbmcaddon.Addon()

        # Get Dialog instance
        self._dialog = xbmcgui.Dialog()

        # Initialise actions dictionary
        self._actions: Dict[str, Callable[[Dict[str, str]], None]] = {}

    @property
    def handle(self) -> int:
        """
        Return addon handle.
        """
        return self._handle

    @property
    def params(self) -> Dict[str, str]:
        """
        Return query string parameters as a Dict.

        Takes only the first instance if a variable if defined multiple times.
        """
        return {key: value[0] for key, value in self._params.items()}

    @property
    def addon(self) -> xbmcaddon.Addon:
        """
        Return Addon instance.
        """
        return self._addon

    @property
    def dialog(self) -> xbmcgui.Dialog:
        """
        Return Dialog instance
        """
        return self._dialog

    @property
    def name(self) -> str:
        """
        Return addon name.
        """
        name: str = self.addon.getAddonInfo('name')
        return name

    @property
    def icon(self) -> str:
        """
        Return path to addon icon.
        """
        icon: str = self.addon.getAddonInfo('icon')
        return icon

    def get_setting(self, setting_id: str) -> str:
        """
        Get an addon setting.

        setting_id: Name of setting.
        """
        setting: str = self.addon.getSetting(setting_id)
        return setting

    def localise(self, string_id: int) -> str:
        """
        Localise a string.

        string_id: ID of string
        """
        string: str = self.addon.getLocalizedString(string_id)
        return string

    def log(self, level: int, message: str) -> None:
        """
        Send a message to the Kodi log.

        level: log level.
        message: log message.
        """
        assert level in [LOGDEBUG, LOGINFO, LOGWARNING, LOGERROR, LOGFATAL]
        xbmc.log(f'{self.name}: {message}', level)

    def notification(self, message: str,
                     icon: str = NOTIFICATION_INFO) -> None:
        """
        Create a Kodi notification.

        message: Message to display
        icon: Notification icon, one of [NOTIFICATION_INFO,
            NOTIFICATION_WARNING, NOTIFICATION_ERROR]
        """
        self.dialog.notification(heading=self.name, message=message, icon=icon)

    def action(self, name: Optional[str] = None) -> Callable[[Action], Action]:
        """
        Decorator factory to register plugin actions.

        name: Name of the action (to be used as the value for the 'action'
            query string parameter). By default this takes the name of the
            function being decorated.
        """
        def inner(func: Action) -> Action:
            nonlocal name
            if not callable(func):
                raise PluginException(f'{func} is not callable')

            if name is None:
                name = func.__name__
            if name in self._actions.keys():
                raise PluginException(f'action {name} already registered')

            self.log(LOGDEBUG, f'registering action: {name}')
            self._actions[name] = func

            return func

        return inner

    def build_url(self, action: Optional[str] = None, **kwargs: Any) -> str:
        """
        Construct the url to call a plugin action.

        action: Name of the action (as used in the @action decorator).
        kwargs: Arguments to pass.
        """
        # Python > 3.9 only
        # params = urllib.parse.urlencode(
        #     ({'action': action} if action else {}) | kwargs
        # )
        params_dict = {'action': action} if action else {}
        params_dict.update(kwargs)
        params = urllib.parse.urlencode(params_dict)
        url = ''.join([self._base_url, '?', params])
        return url

    def run(self) -> None:
        """
        Plugin entry point. Calls the appropriate action function based on the
            'action' query string parameter.
        """
        self.log(LOGDEBUG, f'entering with parameters {self.params}')
        self.log(LOGDEBUG, f'actions registered: {self._actions.keys()}')
        action = self.params.get('action', 'root')

        self._actions[action](self.params)

    def list_item(self, label: Optional[str] = None,
                  label2: Optional[str] = None,
                  path: Optional[str] = None) -> xbmcgui.ListItem:
        """
        Create a list item.

        label: label to pass to xbmcgui.ListItem.
        label2: label2 to pass to xbmcgui.ListItem.
        path: path to pass to xbmcgui.ListItem.
        """
        list_item = xbmcgui.ListItem(label, label2, path)
        list_item.setArt({'icon': self.icon})

        return list_item
