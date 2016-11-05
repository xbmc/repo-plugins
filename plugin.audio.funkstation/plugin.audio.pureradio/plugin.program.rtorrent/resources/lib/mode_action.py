# Import
import xbmc
import xbmcgui
import globals as g
# Send action to rTorrent
def main(method, arg1, arg2, arg3):
	allok = 0
	if method.find('erase')!=-1:
		dialog = xbmcgui.Dialog()
		ret = dialog.yesno(g.__lang__(30153), g.__lang__(30154))
		if ret==True:
			allok = 1
	else:
		allok = 1
	if allok==1:
		if arg3:
			#only used at this stage to change priority on files in torrent
			#TODO: Must clean this up and put integer checking in place
			function = 'g.rtc.'+method+'("'+arg1+'",'+arg2+','+arg3+')'
		elif arg2:
			function = 'g.rtc.'+method+'("'+arg1+'","'+arg2+'")'
		else:
			function = 'g.rtc.'+method+'("'+arg1+'")'
		#print function	
		exec function
		xbmc.executebuiltin('Container.Refresh')
