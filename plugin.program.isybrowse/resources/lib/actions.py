import actions as self
import shared
import xbmc
import xbmcaddon
import xbmcgui

# define ISY API actions
__act_names__ = {
    'on': 'NodeOn',
    'off': 'NodeOff',
    'toggle': 'NodeToggle',
    'faston': 'NodeFastOn',
    'fastoff': 'NodeFastOff',
    'bright': 'NodeBright',
    'dim': 'NodeDim',
    'on25': 'NodeOn25',
    'on50': 'NodeOn50',
    'on75': 'NodeOn75',
    'on100': 'NodeOn100',
    'run': 'ProgramRun',
    'then': 'ProgramRunThen',
    'else': 'ProgramRunElse'}
# define local actions
__act_names_local__ = {
    'info': 'ShowNodeInfo',
    'pinfo': 'ShowProgramInfo',
    'config': 'ShowAddonConfig'}


def DoAction(addr, cmd):
    '''
    DoAction(addr, cmd)

    DESCRIPTION:
    This function executes actions on a
    given address. This is the function
    that is called by the menu items.
    '''
    try:
        fun = getattr(shared.isy, __act_names__[cmd])
    except KeyError:
        fun = getattr(self, __act_names_local__[cmd])
    fun(addr)


# local actions
#   these are actions that are performed
#   on the nodes that would not be
#   appropriate in the ISY API
def ShowNodeInfo(addr):
    '''
    ShowNodeInfo(addr)

    DESCRIPTION:
    This action displays node information
    on the screen.
    '''
    data = shared.isy.NodeInfo(addr)
    name = data.keys()[0]
    type = data[name][0]
    status = data[name][2]

    if type == 'node':
        output = name + ' (' + str(int(float(status) / 255.0 * 100.0)) + '%)' \
            + '\n' + shared.translate(30302) + ': ' + str(addr)
    else:
        output = name + '\n' + shared.translate(30302) + ': ' + str(addr)

    dialog = xbmcgui.Dialog()
    dialog.ok(shared.translate(30301), output)


def ShowProgramInfo(addr):
    '''
    ShowProgramInfo(addr)

    DESCRIPTION:
    This action displays program information
    on the screen.
    '''

    output = shared.translate(30302) + ': ' + str(addr)

    dialog = xbmcgui.Dialog()
    dialog.ok(shared.translate(30301), output)


def ShowAddonConfig(addr):
    '''
    ShowAddonConfig(addr)

    DESCRIPTION:
    This action opens the configuration for
    an XBMC addon on the screen.
    '''
    xbmcaddon.Addon(id=addr).openSettings()


def RefreshWindow(*args, **kwargs):
    '''
    RefreshWindow(*)

    DESCRIPTION:
    This function refreshes the active
    window in XBMC. All inputs are ignored
    so that it can be called like the
    other actions that do require input.
    '''
    xbmc.executebuiltin('XBMC.Container.Refresh()')
