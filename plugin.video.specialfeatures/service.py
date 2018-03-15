from lib.sys_init import *
from lib.iteration import *



if __name__ == '__main__':
    if sys.version_info[0]<3:
        encoding()
    while not monitor.abortRequested():
    	showcon    = addon.getSetting('showcon')
    	home.setProperty('SpecialFeatures.ContextMenu',showcon)
    	if home.getProperty('SpecialFeatures.Query') != 'true':
            listitem = xbmc.getInfoLabel('Container({}).ListItem.label'.format(xbmc.getInfoLabel('System.CurrentControlID')))
            if home.getProperty('SpecialFeatures.Listitem') != listitem:
                home.setProperty('SpecialFeatures.Listitem', listitem)
            	dbEnterExit().initDb('quikchk2')
        if monitor.waitForAbort(1):
            break