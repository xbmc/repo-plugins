# -*- coding: utf-8 -*-
"""
    Crunchyroll
    Copyright (C) 2012 - 2014 Matthew Beacher
    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""
import os
import re
import sys
import urllib
try:
    import cPickle as pickle
except:
    import pickle

import xbmc
import xbmcgui
import xbmcplugin

import crunchy_json as crj

from crunchy_json import log



class Args(object):
    """Arguments class.

    Hold all arguments passed to the script and also persistent user data and
    reference to the addon. It is intended to hold all data necessary for the
    script.
    """
    def __init__(self, *args, **kwargs):
        """Initialize arguments object.

        Hold also references to the addon which can't be kept at module level.
        """
        self._addon = sys.modules['__main__'].__settings__
        self._lang  = encode(sys.modules['__main__'].__language__)
        self._id    = self._addon.getAddonInfo('id')

        for key, value in kwargs.iteritems():
            if value == 'None':
                kwargs[key] = None
            else:
                kwargs[key] = urllib.unquote_plus(kwargs[key])
        self.__dict__.update(kwargs)



def encode(f):
    """Decorator for encoding strings.

    """
    def lang_encoded(*args):
        return f(*args).encode('utf8')
    return lang_encoded


def endofdirectory(sortMethod='none'):
    """Mark end of directory listing.

    """
    # Set sortmethod to something xbmc can use
    if sortMethod == 'title':
        sortMethod = xbmcplugin.SORT_METHOD_TITLE
    elif sortMethod == 'none':
        sortMethod = xbmcplugin.SORT_METHOD_NONE
    elif sortMethod == 'date':
        sortMethod = xbmcplugin.SORT_METHOD_DATE
    elif sortMethod == 'label':
        sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE

    # Sort methods are required in library mode
    xbmcplugin.addSortMethod(int(sys.argv[1]),
                             sortMethod)

    # Let xbmc know the script is done adding items to the list
    dontAddToHierarchy = False
    xbmcplugin.endOfDirectory(handle        = int(sys.argv[1]),
                              updateListing = dontAddToHierarchy)


def add_item(args,
             info,
             isFolder=True,
             total_items=0,
             queued=False,
             rex=re.compile(r'(?<=mode=)[^&]*')):
    """Add item to directory listing.

    """
    # Defaults in dict. Use 'None' instead of None so it is compatible for
    # quote_plus in parseArgs.
    info.setdefault('url',          'None')
    info.setdefault('thumb',        'None')
    info.setdefault('fanart_image',
                    xbmc.translatePath(args._addon.getAddonInfo('fanart')))
    info.setdefault('mode',         'None')
    info.setdefault('count',        '0')
    info.setdefault('filterx',      'None')
    info.setdefault('id',           'None')
    info.setdefault('series_id',    'None')
    info.setdefault('offset',       '0')
    info.setdefault('season',       '1')
    info.setdefault('series_id',    '0')
    info.setdefault('page_url',     'None')
    info.setdefault('complete',     'True')
    info.setdefault('media_type',   'None')
    info.setdefault('title',        'None')
    info.setdefault('year',         '0')
    info.setdefault('playhead',     '0')
    info.setdefault('duration',     '0')
    info.setdefault('episode',      '0')
    info.setdefault('plot',         'None')

    # Create params for xbmcplugin module
    u = sys.argv[0]    +\
        '?url='        + urllib.quote_plus(info['url'])          +\
        '&mode='       + urllib.quote_plus(info['mode'])         +\
        '&name='       + urllib.quote_plus(info['title'])        +\
        '&id='         + urllib.quote_plus(info['id'])           +\
        '&count='      + urllib.quote_plus(info['count'])        +\
        '&series_id='  + urllib.quote_plus(info['series_id'])    +\
        '&filterx='    + urllib.quote_plus(info['filterx'])      +\
        '&offset='     + urllib.quote_plus(info['offset'])       +\
        '&icon='       + urllib.quote_plus(info['thumb'])        +\
        '&complete='   + urllib.quote_plus(info['complete'])     +\
        '&fanart='     + urllib.quote_plus(info['fanart_image']) +\
        '&season='     + urllib.quote_plus(info['season'])       +\
        '&media_type=' + urllib.quote_plus(info['media_type'])   +\
        '&year='       + urllib.quote_plus(info['year'])         +\
        '&playhead='   + urllib.quote_plus(info['playhead'])     +\
        '&duration='   + urllib.quote_plus(info['duration'])     +\
        '&episode='   + urllib.quote_plus(info['episode'])     +\
        '&plot='       + urllib.quote_plus(info['plot']          +'%20')

    # Create list item
    li = xbmcgui.ListItem(label          = info['title'],
                          thumbnailImage = info['thumb'])
    li.setInfo(type       = "Video",
               infoLabels = {"Title":   info['title'],
                             "Plot":    info['plot'],
                             "Year":    info['year'],
							 "episode": info['episode']})
    li.setProperty("Fanart_Image", info['fanart_image'])

    # Add context menu
    s1  = re.sub(rex, 'add_to_queue',      u)
    s2  = re.sub(rex, 'remove_from_queue', u)
    #s3  = re.sub(rex, 'list_media', u)

    cm = [(args._lang(30505), 'XBMC.Addon.OpenSettings(%s)' % args._id)]

    if (args.mode is not None and
        args.mode not in 'channels|list_categories'):

        cm.insert(0, (args._lang(30504), 'XBMC.Action(Queue)'))

    if not isFolder:
        # Let XBMC know this can be played, unlike a folder
        li.setProperty('IsPlayable', 'true')

        if queued:
            cm.insert(1, (args._lang(30501), 'XBMC.RunPlugin(%s)' % s2))
        else:
            cm.insert(1, (args._lang(30502), 'XBMC.RunPlugin(%s)' % s1))

    else:
        if (args.mode is not None and
            args.mode in 'list_coll|list_series|queue'):

            if queued:
                cm.insert(1, (args._lang(30501), 'XBMC.RunPlugin(%s)' % s2))
            else:
                cm.insert(1, (args._lang(30502), 'XBMC.RunPlugin(%s)' % s1))

    #cm.insert(2, (args._lang(30503), 'XBMC.RunPlugin(%s)' % s3))
    cm.append(('Toggle debug', 'XBMC.ToggleDebug'))

    li.addContextMenuItems(cm, replaceItems=True)

    # Add item to list
    xbmcplugin.addDirectoryItem(handle     = int(sys.argv[1]),
                                url        = u,
                                listitem   = li,
                                isFolder   = isFolder,
                                totalItems = total_items)


def show_main(args):
    """Show main menu.

    """
    change_language = args._addon.getSetting("change_language")

    if change_language != "0":
        crj.change_locale(args)

    anime   = args._lang(30100)
    drama   = args._lang(30104)
    queue   = args._lang(30105)
    history = args._lang(30111)

    add_item(args,
             {'title':      queue,
              'mode':       'queue'})
    add_item(args,
             {'title':      history,
              'mode':       'history'})
    add_item(args,
             {'title':      anime,
              'mode':       'channels',
              'media_type': 'anime'})
    add_item(args,
             {'title':      drama,
              'mode':       'channels',
              'media_type': 'drama'})
    endofdirectory()


def channels(args):
    """Show Crunchyroll channels.

    """
    popular         = args._lang(30103)
    simulcasts      = args._lang(30106)
    recently_added  = args._lang(30102)
    alpha           = args._lang(30112)
    browse_by_genre = args._lang(30107)
    seasons         = args._lang(30110)

    add_item(args,
             {'title':      popular,
              'mode':       'list_series',
              'media_type': args.media_type,
              'filterx':    'popular',
              'offset':     '0'})
    add_item(args,
             {'title':      simulcasts,
              'mode':       'list_series',
              'media_type': args.media_type,
              'filterx':    'simulcast',
              'offset':     '0'})
    add_item(args,
             {'title':      recently_added,
              'mode':       'list_series',
              'media_type': args.media_type,
              'filterx':    'updated',
              'offset':     '0'})
    add_item(args,
             {'title':      alpha,
              'mode':       'list_series',
              'media_type': args.media_type,
              'filterx':    'alpha',
              'offset':     '0'})
    add_item(args,
             {'title':      browse_by_genre,
              'mode':       'list_categories',
              'media_type': args.media_type,
              'filterx':    'genre',
              'offset':     '0'})
    add_item(args,
             {'title':      seasons,
              'mode':       'list_categories',
              'media_type': args.media_type,
              'filterx':    'season',
              'offset':     '0'})
    endofdirectory()


def fail(args):
    """Unrecognized mode found.

    """
    badstuff = args._lang(30207)

    add_item(args,
             {'title': badstuff,
              'mode':  'fail'})

    log("CR: Main: check_mode fall through", xbmc.LOGWARNING)

    endofdirectory()


def parse_args():
    """Decode arguments.

    """
    if (sys.argv[2]):
        return Args(**dict([p.split('=')
                                for p in sys.argv[2][1:].split('&')]))

    else:
        # Args will turn the 'None' into None.
        # Don't simply define it as None because unquote_plus in updateArgs
        # will throw an exception.
        # This is a pretty ugly solution.
        return Args(mode = 'None',
                    url  = 'None',
                    name = 'None')


def check_mode(args):
    """Run mode-specific functions.

    """
    mode = args.mode
    log("CR: Main: argv[0] = %s" % sys.argv[0],     xbmc.LOGDEBUG)
    log("CR: Main: argv[1] = %s" % sys.argv[1],     xbmc.LOGDEBUG)
    log("CR: Main: argv[2] = %s" % sys.argv[2],     xbmc.LOGDEBUG)
    log("CR: Main: args = %s" % str(args.__dict__), xbmc.LOGDEBUG)
    log("CR: Main: mode = %s" % mode,               xbmc.LOGDEBUG)

    if mode is None:
        show_main(args)
    elif mode == 'channels':
        channels(args)
    elif mode == 'list_series':
        crj.list_series(args)
    elif mode == 'list_categories':
        crj.list_categories(args)
    elif mode == 'list_coll':
        crj.list_collections(args)
    elif mode == 'list_media':
        crj.list_media(args)
    elif mode == 'history':
        crj.history(args)
    elif mode == 'queue':
        crj.queue(args)
    elif mode == 'add_to_queue':
        crj.add_to_queue(args)
    elif mode == 'remove_from_queue':
        crj.remove_from_queue(args)
    elif mode == 'videoplay':
        crj.start_playback(args)
    else:
        fail(args)


def main():
    """Main function for the addon.

    """
    args = parse_args()

    if crj.load_pickle(args) is False:
        add_item(args,
                {'title': 'Session failed: Check login'})
        endofdirectory()

    else:
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')

        check_mode(args)

    try:
        base_path = xbmc.translatePath(args._addon.getAddonInfo('profile')).decode('utf-8')
        pickle_path = os.path.join(base_path, "cruchyPickle")
        user_data = pickle.dump(args.user_data, open(pickle_path, 'wb'))

    except:
        log("CR: Unable to dump pickle")
