import xbmc, xbmcgui, sys

total = len(sys.argv)
 
cmdargs = str(sys.argv)

dialog = xbmcgui.Dialog()
dialog.ok(str(sys.argv[2]), "\r\n\r\n"+str(sys.argv[1]))