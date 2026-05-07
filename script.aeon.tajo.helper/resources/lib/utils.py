#!/usr/bin/python
# coding: utf-8

########################

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import json
import os
import ast
import operator as _op

from resources.lib.helper import *
from resources.lib.json_map import *

########################

''' Safe arithmetic evaluator for skin calc() — replaces unsafe eval()
'''
_ALLOWED_BINOPS = {
    ast.Add: _op.add,
    ast.Sub: _op.sub,
    ast.Mult: _op.mul,
    ast.Div: _op.truediv,
    ast.FloorDiv: _op.floordiv,
    ast.Mod: _op.mod,
    ast.Pow: _op.pow,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: _op.pos,
    ast.USub: _op.neg,
}


def _safe_eval(expr):
    """Evaluate a simple arithmetic expression safely (no name lookups,
    no function calls, no attribute access). Supports +, -, *, /, //,
    %, ** and parentheses on numeric literals only."""
    try:
        node = ast.parse(str(expr), mode='eval').body
    except (SyntaxError, ValueError):
        return 0

    def _eval(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_BINOPS:
            return _ALLOWED_BINOPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_UNARYOPS:
            return _ALLOWED_UNARYOPS[type(n.op)](_eval(n.operand))
        raise ValueError('disallowed expression node: ' + type(n).__name__)

    try:
        return _eval(node)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


########################

''' Functions used by Aeon Tajo skin
'''

def calc(params):
    prop = remove_quotes(params.get('prop', 'CalcResult'))
    formula = remove_quotes(params.get('do'))
    result = _safe_eval(formula)
    winprop(prop, str(result))


def toggleaddons(params):
    addonid = params.get('addonid').split('+')
    enable = get_bool(params.get('enable'))

    for addon in addonid:

        try:
            json_call('Addons.SetAddonEnabled',
                      params={'addonid': '%s' % addon, 'enabled': enable}
                      )
            log('%s - enable: %s' % (addon, enable))
        except Exception:
            pass


def playitem(params):
    clear_playlists()
    execute('Dialog.Close(all,true)')

    dbtype = params.get('type')
    dbid = params.get('dbid')
    resume = params.get('resume', True)
    file = remove_quotes(params.get('item'))

    if dbtype == 'song':
        param = 'songid'

    elif dbtype == 'episode':
        method_details = 'VideoLibrary.GetEpisodeDetails'
        param = 'episodeid'
        key_details = 'episodedetails'

    else:
        method_details = 'VideoLibrary.GetMovieDetails'
        param = 'movieid'
        key_details = 'moviedetails'

    if dbid:
        if dbtype == 'song' or not resume:
            position = 0

        else:
            result = json_call(method_details,
                               properties=['resume', 'runtime'],
                               params={param: int(dbid)}
                               )

            try:
                result = result['result'][key_details]
                position = result['resume'].get('position') / result['resume'].get('total') * 100
                resume_time = result.get('runtime') / 100 * position
                resume_time = str(datetime.timedelta(seconds=resume_time))
            except Exception:
                position = 0
                resume_time = None

            if position > 0:
                resume_string = xbmc.getLocalizedString(12022)[:-5] + resume_time
                contextdialog = DIALOG.contextmenu([resume_string, xbmc.getLocalizedString(12021)])

                if contextdialog == 1:
                    position = 0
                elif contextdialog == -1:
                    return

        json_call('Player.Open',
                  item={param: int(dbid)},
                  options={'resume': position},
                  )

    elif file:
        # playmedia() because otherwise resume points get ignored
        execute('PlayMedia(%s)' % file)


def playall(params):
    clear_playlists()

    container = params.get('id')
    method = params.get('method')

    playlistid = 0 if params.get('type') == 'music' else 1
    shuffled = get_bool(method,'shuffle')

    if shuffled:
        winprop('script.shuffle.bool', True)

    if method == 'fromhere':
        method = 'Container(%s).ListItemNoWrap' % container
    else:
        method = 'Container(%s).ListItemAbsolute' % container

    for i in range(int(xbmc.getInfoLabel('Container(%s).NumItems' % container))):

        if condition('String.IsEqual(%s(%s).DBType,movie)' % (method,i)):
            media_type = 'movie'
        elif condition('String.IsEqual(%s(%s).DBType,episode)' % (method,i)):
            media_type = 'episode'
        elif condition('String.IsEqual(%s(%s).DBType,song)' % (method,i)):
            media_type = 'song'
        else:
            media_type = None

        dbid = xbmc.getInfoLabel('%s(%s).DBID' % (method,i))
        url = xbmc.getInfoLabel('%s(%s).Filenameandpath' % (method,i))

        if media_type and dbid:
            json_call('Playlist.Add',
                      item={'%sid' % media_type: int(dbid)},
                      params={'playlistid': playlistid}
                      )
        elif url:
            json_call('Playlist.Add',
                      item={'file': url},
                      params={'playlistid': playlistid}
                      )

    json_call('Player.Open',
              item={'playlistid': playlistid, 'position': 0},
              options={'shuffled': shuffled}
              )


def txtfile(params):
    prop = params.get('prop')
    path = xbmcvfs.translatePath(remove_quotes(params.get('path')))

    if os.path.isfile(path):
        log('Reading file %s' % path)
        with open(path) as f:
            text = f.read()

        if prop:
            winprop(prop,text)
        else:
            DIALOG.textviewer(remove_quotes(params.get('header')), text)

    else:
        log('Cannot find %s' % path)
        winprop(prop, clear=True)


def multi_scan(params):
    """Manually trigger a scan for extras folders and theme files."""
    from resources.lib.extras_cache import scan_library
    scan_library()


def multi_scan_music(params):
    """Manually trigger a scan for music extras folders."""
    from resources.lib.extras_cache import scan_music_library
    scan_music_library()


def reset_scan(params):
    """Remove all custom art data and perform a full library rescan."""
    if not DIALOG.yesno(ADDON.getLocalizedString(32025), ADDON.getLocalizedString(32040)):
        return

    winprop('reset_scan_running.bool', True)

    from resources.lib.extras_cache import scan_library, scan_music_library
    scan_library(force_reset=True)
    scan_music_library(force_reset=True)

    winprop('reset_scan_running', clear=True)
