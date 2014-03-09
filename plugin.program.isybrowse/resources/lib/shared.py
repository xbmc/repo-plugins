import pyisy
import shared as self
import urls
import xbmc
import xbmcaddon

# addon classes
events = None
browser = None

# connection to ISY controller
isy = None

# runtime parameters
__path__ = ''
__params__ = {}
__id__ = -1

# function shortcuts
translate = None


def events_enabled():
    return events is not None

# common paths
__media__ = ''
__lib__ = ''


def initialize(args):
    '''
    initialize(args)

    DESCRIPTION:
    This function initialize the shared variable library.
    The only input to this function is the program's
    system arguments.  There is no output.
    '''
    # check if events is available
    try:
        self.events = xbmcaddon.Addon('service.script.isyevents')
    except:
        self.events = None

    # get this addon
    self.browser = xbmcaddon.Addon('plugin.program.isybrowse')

    # get plugin information
    self.__path__ = args[0]
    self.__id__ = int(args[1])
    self.__params__ = urls.ParseUrl(args[2])['params']
    self.translate = self.browser.getLocalizedString

    # get common file paths
    self.__media__ = self.browser.getAddonInfo('path') + '/resources/media/'
    self.__lib__ = self.browser.getAddonInfo('path') + '/resources/lib/'

    # connect to isy
    username = self.browser.getSetting('username')
    password = self.browser.getSetting('password')
    host = self.browser.getSetting('host')
    port = int(self.browser.getSetting('port'))
    usehttps = self.browser.getSetting('usehttps') == 'true'
    self.isy = pyisy.open(username, password, host, port, usehttps)

    # verify isy opened correctly
    if self.isy.__dummy__:
        header = self.translate(30501)
        message = self.translate(30502)
        xbmc.executebuiltin('Notification(' + header + ','
                            + message + ', 15000)')
