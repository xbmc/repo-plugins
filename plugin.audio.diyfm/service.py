# import xbmc, xbmcaddon
#
#
# __settings__ = xbmcaddon.Addon(id='plugin.audio.diyfm')
#
#
# class UpdateSettingsMonitor(xbmc.Monitor):
#
#     def onSettingsChanged(self):
#         if __settings__.getSetting('play_news') == 'true':
#             pass
#
# monitor = UpdateSettingsMonitor()
#
# while not xbmc.abortRequested:
#     xbmc.sleep(5000)
