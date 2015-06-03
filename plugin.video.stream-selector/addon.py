import xbmc
import xbmcgui
import xbmcplugin

import urlparse
import urllib
import webbrowser
# This addpm display menu to select a stream from given list.
#   - The format of the list is plugin.video.stream-selector/select ? <name> := <link> [ @@ <name> := <link> ]*

class Addon():
    def handle(self):
        path = ''
        if len(sys.argv) >= 1:
            path = sys.argv[0].replace('plugin://plugin.video.stream-selector/','')
        if path == 'select':
            self.select()
            return
        xbmcgui.Dialog().ok('Stream Selector','No action was found')

    def select(self):
        names = []
        links = []
        if len(sys.argv) >= 3:
            qq = urllib.unquote(sys.argv[2][1:])
            for stream in qq.split('@@'):
                ii = stream.find(':=')
                if ii >= 0:
                    names.append(stream[:ii].strip())
                    links.append(stream[ii+2:].strip())
        if len(names) == 0:
            xbmcgui.Dialog().ok('Stream Selector','No streams was found')
        elif len(names) == 1:
            self.play(links[0])
        else:
            index = xbmcgui.Dialog().select('Select stream', names)
            if index != -1:
                self.play(links[index])

    def play(self,link):
        if link.startswith('web://'):
            webbrowser.open(link[len('web://'):])
            return
        xi = xbmcgui.ListItem('item')
        xi.setPath(link)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), succeeded=True, listitem=xi)

Addon().handle()