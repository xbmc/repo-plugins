import sys
import re
import xbmc

if __name__ == '__main__':
    movie_title = sys.listitem.getLabel()
    movie_title = re.sub('\[.*?]', '', movie_title)
    movie_title = re.sub(' +', '+', movie_title)
    path = "plugin://plugin.video.kermodeandmayo/youtube/search/{0}".format(movie_title)
    xbmc.executebuiltin("Container.Update({0})".format(path))
