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


import re;
import json;
import urlparse;
import time;
import logging;

#from resources.lib.modules import cache
from resources.lib.modules import control;
#from resources.lib.modules import cleandate
from resources.lib.modules import client;
from resources.lib.modules import utils;

#getTrakt('/sync/history', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]})
#mark as watched

#getTrakt('search/tvdb/:72070')

logger = logging.getLogger('funimationnow');


def getTrakt(url, post=None):

    try:

        url = urlparse.urljoin('http://api-v2launch.trakt.tv/', url);

        headers = {
            'Content-Type': 'application/json', 
            'trakt-api-key': '49e7f57ee0c22e6ca39649a9255f6097d10cbdb708a5f1c3dc196e615cce6549', 
            'trakt-api-version': '2'
        };

        if not post == None: 
            post = json.dumps(post);

        if getTraktCredentialsInfo() == False:
            
            result = client.request(url, post=post, headers=headers);

            return result;


        headers.update({'Authorization': 'Bearer %s' % utils.setting('trakt.token')});

        result = client.request(url, post=post, headers=headers, output='response', error=True);

        if not (result[0] == '401' or result[0] == '405'): 
            return result[1];


        oauth = 'http://api-v2launch.trakt.tv/oauth/token';

        opost = {
            'client_id': '49e7f57ee0c22e6ca39649a9255f6097d10cbdb708a5f1c3dc196e615cce6549', 
            'client_secret': '49288059527f042ac3e953419ecfd8c6783438ae966cd0b05982423e7fbb0259', 
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 
            'grant_type': 'refresh_token', 
            'refresh_token': utils.setting('trakt.refresh')
        };

        result = client.request(oauth, post=json.dumps(opost), headers=headers);
        result = json.loads(result);

        token = result['access_token'];
        refresh = result['refresh_token'];

        utils.setting('trakt.token', token);
        urils.setting('trakt.refresh', refresh);

        headers.update({'Authorization': 'Bearer %s' % token});

        result = client.request(url, post=post, headers=headers);

        return result;

    except:
        pass;


def authTrakt():

    try:

        if getTraktCredentialsInfo() == True:

            if control.yesnoDialog(control.lang(32700).encode('utf-8'), control.lang(32701).encode('utf-8'), '', 'Trakt'):

                utils.setting('trakt.user', '');
                utils.setting('trakt.token', '');
                utils.setting('trakt.refresh', '');

            raise Exception();

        result = getTrakt('/oauth/device/code', {'client_id': '49e7f57ee0c22e6ca39649a9255f6097d10cbdb708a5f1c3dc196e615cce6549'});
        result = json.loads(result);

        verification_url = (control.lang(32702) % result['verification_url']).encode('utf-8');
        user_code = (control.lang(32703) % result['user_code']).encode('utf-8');
        expires_in = int(result['expires_in']);
        device_code = result['device_code'];
        interval = result['interval'];

        progressDialog = control.progressDialog;
        progressDialog.create('Trakt', verification_url, user_code);

        for i in range(0, expires_in):

            try:

                if progressDialog.iscanceled(): 
                    break;

                time.sleep(1);

                if not float(i) % interval == 0: 
                    raise Exception();

                r = getTrakt('/oauth/device/token', {'client_id': '49e7f57ee0c22e6ca39649a9255f6097d10cbdb708a5f1c3dc196e615cce6549', 'client_secret': '49288059527f042ac3e953419ecfd8c6783438ae966cd0b05982423e7fbb0259', 'code': device_code});
                r = json.loads(r);

                if 'access_token' in r: 
                    break;
            
            except:
                pass;

        try: 
            progressDialog.close();
        
        except: 
            pass;


        token = r['access_token'];
        refresh = r['refresh_token'];

        headers = {
            'Content-Type': 'application/json', 
            'trakt-api-key': '49e7f57ee0c22e6ca39649a9255f6097d10cbdb708a5f1c3dc196e615cce6549', 
            'trakt-api-version': '2', 
            'Authorization': 'Bearer %s' % token
        };

        result = client.request('http://api-v2launch.trakt.tv/users/me', headers=headers);
        result = json.loads(result);

        user = result['username'];

        utils.setting('trakt.user', user);
        utils.setting('trakt.token', token);
        utils.setting('trakt.refresh', refresh);

        raise Exception();

    except:
        control.openSettings('3.1');


def getTraktCredentialsInfo():

    user = utils.setting('trakt.user').strip();
    token = utils.setting('trakt.token');
    refresh = utils.setting('trakt.refresh');

    if (user == '' or token == '' or refresh == ''): 
        return False;

    return True;


def markEpisodeAsWatched(tvdb, season, episode):
    
    season = int('%01d' % int(season));
    episode = int('%01d' % int(episode));

    return getTrakt('/sync/history', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]});


def markEpisodeAsNotWatched(tvdb, season, episode):
    
    season = int('%01d' % int(season));
    episode = int('%01d' % int(episode));

    return getTrakt('/sync/history/remove', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"tvdb": tvdb}}]});


def startProgress(content, show_id, asset_id, currentTime, totalTime):

    if content.title() == 'Episode':

        try:

            trakt_data = utils.fetchtraktprogressdata(show_id, asset_id);

            if trakt_data is not None:

                (title, season, number) = trakt_data;

                trakt_progress = round(((float(currentTime) / abs(totalTime)) * 100.00), 4);

                getTrakt('/scrobble/start', {"show": {"title": title}, "episode": {"season": season, "number": number}, "progress": trakt_progress, "app_version": "1.0", "app_date": "2016-08-02"});

        except Exception as inst:
            logger.error(inst);
            pass;


def pauseProgress(content, show_id, asset_id, currentTime, totalTime):

    if content.title() == 'Episode':

        try:

            trakt_data = utils.fetchtraktprogressdata(show_id, asset_id);

            if trakt_data is not None:

                (title, season, number) = trakt_data;

                trakt_progress = round(((float(currentTime) / abs(totalTime)) * 100.00), 4);

                getTrakt('/scrobble/pause', {"show": {"title": title}, "episode": {"season": season, "number": number}, "progress": trakt_progress, "app_version": "1.0", "app_date": "2016-08-02"});

        except Exception as inst:
            logger.error(inst);
            pass;


def stopProgress(content, show_id, asset_id, trakt_progress):

    if content.title() == 'Episode':

        try:

            trakt_data = utils.fetchtraktprogressdata(show_id, asset_id);

            if trakt_data is not None:

                (title, season, number) = trakt_data;

                getTrakt('/scrobble/stop', {"show": {"title": title}, "episode": {"season": season, "number": number}, "progress": trakt_progress, "app_version": "1.0", "app_date": "2016-08-02"});

        except Exception as inst:
            logger.error(inst);
            pass;