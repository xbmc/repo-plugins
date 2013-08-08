"""
This is default file of SynopsiTV service. See addon.xml
<extension point="xbmc.service" library="service.py" start="login|startup">
"""
# xbmc
import xbmc, xbmcgui, xbmcaddon

# python standart lib
import threading
import thread
import sys
import time

# application
from scrobbler import SynopsiPlayerDecor
from library import RPCListenerHandler
from cache import *
from utilities import *
from app_apiclient import AppApiClient
from addonservice import AddonService
import top
import dialog

threading.current_thread().name = 'service.py'

__addon__  = get_current_addon()
__cwd__	= __addon__.getAddonInfo('path')
__addon__.setSetting('ADDON_SERVICE_FIRSTRUN', "false")

DEFAULT_SERVICE_PORT=int(__addon__.getSetting('ADDON_SERVICE_PORT'))

def main():
	log('SYNOPSI SERVICE (%s) START' % VERSION)
	
	top.apiClient = AppApiClient.getDefaultClient()

	# get or generate install-unique ID
	iuid = get_install_id()

	# try to restore cache
	top.stvList = StvList(iuid, top.apiClient)
	top.player = SynopsiPlayerDecor()
	top.player.setStvList(top.stvList)

	# check first run
	check_first_run()
	
	try:
		top.stvList.load()
		thread.start_new_thread(home_screen_fill, (top.apiClient, top.stvList))
	except:
		# first time
		log('CACHE restore failed. If this is your first run, its ok. Rebuilding cache')
		thread.start_new_thread(cache_rebuild_hp_update, ())


	threads = []
	l = RPCListenerHandler(top.stvList)
	threads.append(l)
	aos = AddonService('localhost', DEFAULT_SERVICE_PORT, top.apiClient, top.stvList)
	threads.append(aos)

	for t in threads:
		t.start()

	log('Service loop START')
	while True:
		xbmc.sleep(500)

		if not [t for t in threads if t.isAlive()]:
			log('All threads are dead. Exiting loop')
			break

		if xbmc.abortRequested:
			log('abortRequested')
			log('waiting for: ' + str(','.join([i.name for i in threads if i.isAlive()])))
			aos.stop()

		top.player.update_current_time()


	log('Service loop END')
	top.stvList.save()
	
	dialog.close_all_dialogs()
	log('Service thread END')

if __name__ == "__main__":
	main()
