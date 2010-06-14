"""
    TED Talks
    rwparris2
"""
import sys

#plugin constants
__plugin__ = "TED Talks"
__author__ = "rwparris2"
__url__ = "http://code.google.com/p/xbmc-addons/"
__svn_url__ = "http://xbmc-addons.googlecode.com/svn/trunk/plugins/video/TED%20Talks"
__version__ = "2.1.5"

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

if __name__ == "__main__":
    import resources.lib.ted_talks as ted_talks
    if not sys.argv[2]:
        ted_talks.Main()
    elif sys.argv[2].startswith('?addToFavorites'):
        ted_talks.Main(checkMode=False).addToFavorites(sys.argv[2].split('=')[-1])
    elif sys.argv[2].startswith('?removeFromFavorites'):
        ted_talks.Main(checkMode=False).removeFromFavorites(sys.argv[2].split('=')[-1])
    elif sys.argv[2].startswith('?downloadVideo'):
        ted_talks.Main(checkMode=False).downloadVid(sys.argv[2].split('=')[-1])
    else:
        ted_talks.Main()

sys.modules.clear()
