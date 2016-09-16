# -*- coding: utf-8 -*-

'''
    Funimation|Now Add-on
    Copyright (C) 2016 Funimation|Now

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import sys;
import urlparse;
import logging;

from resources.lib.modules.log_handler import LogHandler;


def setup_logging():
    import xbmcaddon;
    
    addon = xbmcaddon.Addon();

    log_level = (int(addon.getSetting('loglvl')) + 1) * 10;
    logger = logging.getLogger('funimationnow');

    logger.setLevel(log_level);

    formatter = logging.Formatter('[{0}] %(funcName)s : %(message)s'.format(addon.getAddonInfo('id')));
    lh = LogHandler();

    lh.setLevel(log_level);
    lh.setFormatter(formatter);

    logger.addHandler(lh);

    return logger;

logger = setup_logging();
#logger.error('ARGV: %s', sys.argv);

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')));

action = params.get('action');
url = params.get('url');
content = params.get('content');
filtertype = params.get('filtertype');


if action == None:
    from resources.lib.indexers import navigator;

    navigator.navigator().root();

elif action == 'authTrakt':
    from resources.lib.modules import trakt;

    trakt.authTrakt();

elif action == 'featured':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params);    

elif action == 'showsNavigator':
    from resources.lib.indexers import navigator;
    
    navigator.navigator().tvshows();

elif action == 'browseNavigator':
    from resources.lib.indexers import navigator;
    
    navigator.navigator().browse();

elif action == 'alphaNavigator':
    from resources.lib.indexers import navigator;
    
    navigator.navigator().browsealpha();

elif action == 'getAllRatings':
    from resources.lib.indexers import navigator;

    navigator.navigator().ratings(action);

elif action == 'genres':
    from resources.lib.indexers import navigator;

    navigator.navigator().genres(action);

elif action == 'extras':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params, filtertype);

elif action == 'shows':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params);

elif action == 'getVideoHistory':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params);

elif action == 'getQueue':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params);

elif action == 'similarSeries':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params);

elif action == 'videos':
    from resources.lib.indexers import navigator;

    navigator.navigator().filtered(action, filtertype, params);

elif action == 'updatemyqueue':
    from resources.lib.modules import control;
    from resources.lib.modules import utils;

    success = utils.addremovequeueitem(params);
    emessage = 32507;

    if success is not None:

        emessage = success[1];

        if success[0] is True:
            control.refresh();

    utils.sendNotification(emessage, 10000);

elif action == 'updatewatched':
    from resources.lib.modules import control;
    from resources.lib.modules import utils;

    logger.error(params)

    success = utils.markwatchedstatus(params);

    if success is not None:
        control.refresh();


elif action == 'updatefavorites':
    from resources.lib.modules import utils;

    utils.updatefavorites(params);


elif action == 'player':
    from resources.lib.modules import utils;
    
    showinfo = utils.gathermeta(params);

    if showinfo is not None:
        from resources.lib.modules.player import player;

        player().run(showinfo);

    
elif action == 'searchNavigator':
    from resources.lib.modules import control;
    from resources.lib.modules import utils;

    search_text = utils.implementsearch();

    if search_text is not None:

        #url = self.search_link + urllib.quote_plus(q)
        url = '%s?action=search&search=%s' % (sys.argv[0], search_text);
        control.execute('Container.Update(%s)' % url);

elif action == 'search':
    from resources.lib.indexers import navigator;

    navigator.navigator().search(action, params);

elif action == 'loginNavigator':
    from resources.lib.modules import utils;

    utils.promptForLogin();
    utils.checkcookie();

elif action == 'clearCookies':
    import xbmcgui;
    from resources.lib.modules import control;
    from resources.lib.modules import utils;

    if xbmcgui.Dialog().yesno(control.lang(32750).encode('utf-8'), control.lang(32751).encode('utf-8'), control.lang(32752).encode('utf-8')):
        utils.clearcookies();

