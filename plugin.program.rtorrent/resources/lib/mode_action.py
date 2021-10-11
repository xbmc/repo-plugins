'''Application to send "actions" back to rTorrent'''
import xbmc
import xbmcgui
import resources.lib.globals as g

def download_start(download_hash):
    ''' Start download '''
    xbmc.log('Starting download %s' % download_hash)
    g.rtc.call('d.start', download_hash)

def download_stop(download_hash):
    ''' Stop download '''
    xbmc.log('Stopping download %s' % download_hash)
    g.rtc.call('d.stop', download_hash)

def download_erase(download_hash):
    ''' Erase download (with confirmation) '''
    dialog = xbmcgui.Dialog()
    confirm = dialog.yesno(g.__lang__(30153), g.__lang__(30154))
    if confirm is True:
        g.rtc.call('d.erase', download_hash)

def download_priority(download_hash, priority):
    ''' Set download priority '''
    g.rtc.call('d.priority.set', download_hash, priority)

def file_priority(file_hash, priority):
    ''' Set file priority '''
    g.rtc.call('f.priority.set', file_hash, priority)

def main(method, **args):
    ''' Send action to rTorrent '''
    xbmc.log('Performing action %s with these arguments %s' % (method, args))
    if method == "d_start":
        download_start(args['download_hash'])
    elif method == "d_stop":
        download_stop(args['download_hash'])
    elif method == "d_erase":
        download_erase(args['download_hash'])
    elif method == "d_priority":
        download_priority(args['download_hash'], args['priority'])
    elif method == "f_priority":
        file_priority(args['file_hash'], args['priority'])
    else:
        xbmcgui.Dialog().ok(g.__lang__(30900), g.__lang__(30905))
    xbmc.executebuiltin('Container.Refresh')
