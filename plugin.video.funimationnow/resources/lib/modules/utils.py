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



import xbmcaddon;
import logging;
import datetime;
import base64;
import urllib;
import re;


addon = xbmcaddon.Addon();
addonInfo = addon.getAddonInfo;
#dialog = xbmcgui.Dialog();
#execute = xbmc.executebuiltin;
lang = addon.getLocalizedString;
#progressDialog = xbmcgui.DialogProgress();
#progressDialogBG = xbmcgui.DialogProgressBG();
#setting = xbmcaddon.Addon().getSetting;
#setSetting = xbmcaddon.Addon().setSetting;
logger = logging.getLogger('funimationnow');

funimation_url = 'http://www.funimation.com/feeds/ps/getVideoHistory?username=%s&show_id=%s&limit=3000';


def setting(setting_id, setting_value = None):

    if setting_value is None:
        return addon.getSetting(setting_id);

    else:
        return addon.setSetting(setting_id, setting_value);


def decode(fvalue):

    return base64.urlsafe_b64decode(fvalue);


def gathermeta(params):

    import syncdata;


    try:

        season, show_id, asset_id, duration, progress, number = params['barcode'].split('-');
        content = params['video'];
        continueplayback = 1;

        showstatus = syncdata.fetchshowstatus(show_id);

        if showstatus is not None and asset_id in showstatus:

            try:

                status = showstatus[asset_id];
                progress = status['progress'];
                
            except:
                pass;


        if duration is not None and progress is not None:
            progress = calcprogress(progress, duration);         


        if progress > 0:

            if (int(duration) * .92) > progress:

                import xbmcgui;
                import datetime;
                
                progresstext = str(datetime.timedelta(seconds=progress));

                pboptions = ['Resume from %s' % progresstext, 'Start from beginning'];

                dialog = xbmcgui.Dialog();

                try:
                    continueplayback = dialog.contextmenu(pboptions)

                except:
                    continueplayback = dialog.select('Playback Options', pboptions);

        if continueplayback < 0:
            return;
        

        meta = collectdata(season, show_id, asset_id, number, content);

        meta.update({
            'continueplayback': continueplayback,
            'progress': str(progress)
        });

        return meta;


    except Exception as inst:
        logger.error(inst);

        #we need to send some error notification

        return;


def collectdata(season, show_id, asset_id, number, content):

    import json;
    import syncdata;
    
    from resources.lib.modules import cookiecache;
    from resources.lib.modules import client;
    from resources.lib.modules import control;

    checkcookie();

    show = None;

    uid = setting('fn.uid');
    ut = setting('fn.ut') if not None else 'FunimationUser';
    video_quality = int(setting('fn.video_quality')) if not None else 2;
    agent = setting(control.lang(32215).encode('utf-8'));

    content_type = convertValue('content_type');

    funimation_url = 'http://www.funimation.com/feeds/ps/';

    
    if(content == 'Episode' or content == 'Movie'):

        funimation_url += 'videos?';

    else:
        funimation_url += 'extras?';


    if agent is None:
        agent = 'Sony-PS3';

    if uid is not None:
        cookie = cookiecache.fetch(uid.lower(), 1);

    else:
        cookie = None;


    headers = {'User-Agent': agent};
    params = {'show_id':show_id, 'ut':ut, 'filter':'FilterOption%sOnly' % content_type, 'limit':'3000'};

    funimation_url += urllib.urlencode(params);

    try:

        result = client.request(funimation_url, headers=headers, redirect=False, cookie=cookie);
        result = json.loads(result)['videos'];

        for asset in result:

            if(asset['asset_id'] == asset_id):
                show = asset;

                break;


        if show is not None:

            year = None;
            tvdb = None;
            imdb = None;
            poster = None;
            network = None;
            premaired = None;

            plot = show['description'] if 'description' in show else None;
            genre = " / ".join(sorted(list(set(show.get('genre', '').split(',')))));


            siteRatingCount = 0;
            siteRating = 10.0;

            plot = show['description'] if 'description' in show else None;

            try:
                
                aired = show['releaseDate'] if 'releaseDate' in show else None;

                if aired is None:
                    aired = show['pubDate'] if 'pubDate' in show else None;

            except:
                aired = None;

                pass;

            if content == 'Episode':
                
                tvdbmeta = syncdata.fetchepisodes([show_id], [asset_id]);
                name = '%s S%02dE%02d' % (show['title'], int(season), int(number));


                if tvdbmeta is not None:

                    try:

                        tmeta = tvdbmeta[show['asset_id'].encode('utf-8')];

                        if tmeta is not None:

                            aired = tmeta['firstAired'];
                            overview = tmeta['overview'];
                            tvdb = tmeta['tvdbeid'];
                            genre = tmeta['genre'];
                            network = tmeta['network'];
                            siteRatingCount = tmeta['siteRatingCount'];
                            siteRating = tmeta['siteRating'];

                            overview = tmeta['overview'];

                            if overview is not None:
                                if re.sub(r'[^a-zA-Z0-9]+', '', overview).lower() != 'na':
                                    plot = overview;


                    except Exception as inst:
                        logger.error(inst);
                        
                        pass;


            else:

                name = show['title'];

                if name == 'The Movie':
                        
                    try:
                        name = re.sub('(?i)[ ]+\((Sub|Dub)\)', '', show['extended_title']);

                    except:
                        name = show['extended_title'];


                name = '%s (%s)' % (name, year);


            if aired is not None:
            
                from datetime import datetime;
                from dateutil import parser;
                
                try:

                    aired = parser.parse(aired, dayfirst=False);

                    year = aired.strftime('%Y');
                    premaired = aired.strftime('%d/%m/%Y');
                    aired = aired.strftime('%d/%m/%Y');


                except Exception as inst:
                    logger.error(inst);
                
                    pass;



            season = '%01d' % int(season) if content != 'Movie' else None;
            episode = '%01d' % int(number) if content != 'Movie' else None;
            content = 'movie' if content == 'Movie' else 'episode';

            tvdb = tvdb if not tvdb == None else '0';
            imdb = imdb if not imdb == None else '0';
            
            ids = {'imdb': imdb, 'tvdb': tvdb};
            ids = dict((k,v) for k, v in ids.iteritems() if not v == '0');

            try:

                #rawurl = show['hd_video_url'] if 'hd_video_url' in show else show['video_url'];
                rawurl = show['hd_video_url'] if ('hd_video_url' in show and show['hd_video_url'] is not None and len(show['hd_video_url']) > 0) else (show['xbox_one_video_url'] if ('xbox_one_video_url' in show and show['xbox_one_video_url'] is not None and len(show['xbox_one_video_url']) > 0) else show['video_url']);

                videoInfo = {
                    'duration': show['duration'], 
                    'codec': 'h264',
                };
                
                infos = formurl(rawurl, videoInfo, video_quality);

                url = infos[0];
                videoInfo = infos[1];

            except Exception as inst:
                
                logger.error(inst);

                return None;

                pass;


            icon = show['thumbnail_url'];
            thumb = show['thumbnail_url'];

            artwork = getartwork(show_id);

            if artwork:
                
                try:
                    from random import randint

                    artwork = json.loads(artwork)['data'];

                    posters = [d for d in artwork if d['keyType'].lower() == 'poster'.encode('utf-8')];

                    if posters and len(posters) > 0:
                        poster = 'http://thetvdb.com/banners/%s' % posters[randint(0, (len(posters) - 1))]['fileName'];

                except Exception as inst:
                    logger.error(inst);
                
                    pass;


            poster = poster if not None else thumb;
            #string - "video", "movie", "tvshow", "season", "episode" or "musicvideo"

            infoLabels = {
                'rating': siteRating,
                'year': year,
                'duration': show['duration'],
                'plot': plot,
                'votes': siteRatingCount,
                'thumb': thumb,
                'title': show['title'],
                'tvdb': tvdb,
                'mpaa': show['rating'],
                'label': show['title'],
                'poster': poster,
                #'status': ,
                'season': season,
                'tvshowtitle': show['show_name'],
                'mediatype': content,
                'studio': network,
                'genre': genre,
                #'banner': ,
                'episode': episode,
                'premiered': premaired,
                #'fanart': ,
            }


            showinfo = {
                'year': year,
                'name': name,
                'season': season,
                'episode': episode,
                'show_id': show_id,
                'asset_id': asset_id,
                'ids': ids,
                'url': url,
                'content': content,
                'art': {'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster},
                'infoLabels': infoLabels
            };

            return showinfo;


        else:

            sendNotification(32505, 10000);

    except Exception as inst:

        try:
            
            emesage = re.search(r'<h2[^>]*>(?P<message>.*)</h2>', result, re.I);
            emesage = emesage.group('message');
            emesage = re.sub('<[^>]*>', '', emesage);

        except:
            emesage = 32502;
            pass;

        sendNotification(emesage, 15000);

        logger.error(inst);

        pass;


    return None;


def calcprogress(progress, duration):

    cprogress = 0;

    try:
        cprogress = int(progress);

    except:

        try:
            cprogress = float(progress);

            if cprogress > 0:
                cprogress = int(round((int(duration) * (cprogress * .01))));

        except Exception as inst:
            logger.error(inst);
            cprogress = 0;


    return cprogress;


def formurl(url, info, video_quality):
    from urlparse import urlparse;

    url = urlparse(url);

    segments = url.path.split(',');

    rates = sorted([int(r) for r in segments if r.isdigit()], reverse=True);
    rsize = len(rates);

    qdict = {
        0:1500, 
        1:2500, 
        2:4000
    };

    hedict = {
        750:[640, 480],
        #1500:[768, 576], # aert by year
        1500:[960, 540],
        2000:[1280, 720],
        2500:[1280, 720],
        4000:[1920, 1080],
    };

    for r in rates:

        if r <= qdict[video_quality]:

            rate = r;

            break;


    path = '%s%s%s' % (segments[0], str(rate), segments[-1]);

    if rate not in hedict:
        rate = min(hedict, key=lambda x:abs(x - rate));

    finalurl = '%s://%s%s?%s' % (url.scheme, url.netloc, path, url.query);

    w = hedict[rate][0];
    h = hedict[rate][1];

    info['width'] = w;
    info['height'] = h;
    info['aspect'] = (w / float(h));

    return (finalurl, info);


def convertValue(prop):

    if prop == 'content_type':
        return 'Subbed' if (int(setting('fn.%s' % prop)) if not None else 0) == 0 else 'Dubbed';

    if prop == 'result_count':
        result_count = int(setting('fn.%s' % prop)) if not None else 0;

        return 3000 if (result_count == 0) else result_count;

    if prop == 'user_role':
        return bool(re.compile(r'(All-Access|Sub)Pass').match(setting('fn.%s' % prop)));


    return;


def markwatchedstatus(params):

    overlay = '7' if int(params['watched']) > 0 else '6';

    return syncdbprogress(params['show_id'], params['asset_id'], params['content'], params['progress'], params['duration'], True, overlay, False);


def syncdbprogress(show_id, asset_id, content, currentTime, totalTime, webupdate, overlay, supress=True):
    import syncdata;

    watched = 1 if overlay == '7' else 0;
    trakt_progress = 0.0;

    try:

        trakt_progress = round(((float(currentTime) / abs(totalTime)) * 100.00), 4);

    except:
        trakt_progress = 0.0;

    meta = [{
        'show_id': show_id,
        'asset_id': asset_id,
        'video_type': content.title(),
        'fn_progress': int(currentTime),
        'fn_watched': watched,
        'trakt_progress': trakt_progress,
        'trakt_watched': watched
    }];


    syncdata.insertfnepisodes(meta, 'player');


    if webupdate:

        settraktstatus(show_id, asset_id, trakt_progress, content, watched);

        return setfnstatus(show_id, asset_id, int(currentTime), watched, supress);

    else:
        return None;


def settraktstatus(show_id, asset_id, progress, content, watched):

    import syncdata;
    from resources.lib.modules import trakt;

    try:

        if trakt.getTraktCredentialsInfo():

            tvdb_info = syncdata.fetchtraktupdateinfo(show_id, asset_id);

            if tvdb_info is not None and len(tvdb_info) == 3:

                (tvdb, season, episode) = tvdb_info;

                if watched == 1:
                    trakt.markEpisodeAsWatched(tvdb, season, episode);

                else:
                    trakt.markEpisodeAsNotWatched(tvdb, season, episode);

            trakt.stopProgress(content, show_id, asset_id, progress);

    except Exception as inst:
        logger.error(inst);
        pass;


def setfnstatus(show_id, asset_id, progress, watched, supress):

    import json;
    import syncdata;

    from resources.lib.modules import client;
    from resources.lib.modules import control;
    from resources.lib.modules import cookiecache;


    try:

        uid = setting('fn.uid');

        if uid is not None:

            agent = setting(control.lang(32215).encode('utf-8'));

            if agent is None:
                agent = 'Sony-PS3';

            headers = {'User-Agent': agent, 'Content-Type': 'application/json'};
            payload = {'username': uid, 'video_id': asset_id, 'show_id': show_id, 'checkpoint': str(progress if watched > 0 else '0'), 'watched': str(watched)};

            url = 'http://www.funimation.com/feeds/ps/saveVideoHistory';

            payload = json.dumps(payload);

            result = client.request(url, post=payload, headers=headers);
            result = json.loads(result)['success'];

            if result == False:

                if not supress:

                    if watched > 0:
                        sendNotification(32503, 5000);

                    else: 
                        sendNotification(32504, 5000);

                return None;

            else:
                return True;

    except Exception as inst:
        logger.error(inst);

        if not supress:

            if watched > 0:
                    sendNotification(32503, 5000);

            else: 
                sendNotification(32504, 5000);

        return None;
        

def fetchtraktprogressdata(show_id, asset_id):

    import syncdata;
    from resources.lib.modules import trakt;

    try:

        if trakt.getTraktCredentialsInfo():

            trakt_info = syncdata.fetchtraktprogressinfo(show_id, asset_id);

            if trakt_info is not None and len(trakt_info) == 3:

                return trakt_info;

            else:
                return None;

    except Exception as inst:
        logger.error(inst);
        
        return None;


def checkcookie():

    uid = setting('fn.uid');
    pwd = setting('fn.pwd');
    
    if uid and pwd:

        refreshcookie = True;

        cookie_experation = setting('fn.cookie_experation');

        if cookie_experation:
            import cookiecache;
            from dateutil import parser;

            cookieexists = cookiecache.fetch(uid.lower(), 2);

            if cookieexists is not None:

                try:
                    from datetime import datetime;

                    updatesettings(cookieexists);

                    #cookie_experation = datetime.strptime(str(cookie_experation), '%Y-%m-%d %H:%M:%S'); #bug where it would give NoneType called error after initial working call.
                    cookie_experation = parser.parse(cookie_experation, dayfirst=False);

                    present = datetime.now();

                    if present >= cookie_experation:
                        newcookie = True;

                    else:
                        refreshcookie = False;

                except Exception as inst:

                    refreshcookie = True;

                    logger.error(inst);

                    pass;

            else:
                refreshcookie = True;


        if refreshcookie is None or refreshcookie is True:

            import json;

            from resources.lib.modules import client;
            from resources.lib.modules import control;

            agent = setting(control.lang(32215).encode('utf-8'));

            if agent is None:
                agent = 'Sony-PS3';

            headers = {'User-Agent': agent, 'Content-Type': 'application/json'};
            payload = {'username': uid, 'password': pwd, 'playstation_id': ''};

            try:

                payload = json.dumps(payload);

                url = 'https://www.funimation.com/feeds/ps/login.json?v=2';

                result = client.request(url, post=payload, headers=headers, output='extended');

                if result is not None:

                    if len(result) == 2:

                        result = json.loads(result[1]);

                        if 'success' in result:
                            sendNotification(result['message'], 15000);

                            promptForLogin(True);
                            #{"success":false,"message":"Authentication Failed. Please ensure that you are entering your username and not your email address. Your username and password are case-sensitive."}

                        else:
                            resetsettings();

                    else:

                        cookie = result[3];

                        if cookie is not None:
                            import cookiecache;

                            entry = cookiecache.insert(uid.lower(), cookie, result[0]);

                        if entry is True:

                            updatesettings(result[0]);

                            maxage = result[2];

                            if maxage:
                                import re;

                                try:

                                    maxage = re.search(r'bb_lastactivity.*Max-Age=(?P<maxage>\d+)', maxage['set-cookie'], re.I);
                                    maxagev = long(maxage.group('maxage'));

                                    if maxagev:
                                        import decimal;
                                        import datetime;

                                        from dateutil.relativedelta import relativedelta;

                                        expmonths = int((((decimal.Decimal(maxagev) / 31536000) * 12) - 1));

                                        cookie_experation = datetime.date.today() + relativedelta(months =+ expmonths);
                                        cookie_experation = (str(cookie_experation) + ' 00:00:00');

                                        setting('fn.cookie_experation', cookie_experation);

                                except Exception as inst:
                                    logger.error(inst);

                                    pass;

                        else:
                            resetsettings();

            except Exception as inst:
                logger.error(inst);
                
                resetsettings();

                pass;

    else:
        resetsettings();


def clearcookies():
    import cookiecache;

    if cookiecache.clearcookies():
        sendNotification(32753, 5000);

    else:
        sendNotification(32754, 5000);


def gettvdbToken(apikey, url):

    try:

        import json;
        import tokens;

        from resources.lib.modules import client;
        from dateutil.relativedelta import relativedelta;

        tokenexpired = False;
        tokenrefresh = False;

        token = tokens.fetchtvdbtoken();
        apikey = decode(base64.urlsafe_b64decode(apikey));


        if token is not None:

            edate = expireddate(token[1]);
            rdate = expireddate(token[2]);
            token = token[0].encode('utf-8');
            
            if edate:
                tokenexpired = True;

            elif rdate:
                tokenrefresh = True;


        if tokenrefresh and not tokenexpired:
            
            headers = {'Accept': 'application/json', 'Authorization' : 'Bearer %s' % token.encode('utf-8')};

            try:

                rurl = url % 'refresh_token';

                result = client.request(rurl, headers=headers, redirect=False);

                if result is not None:

                    token = json.loads(result)['token'];

                    if token:

                        edate = datetime.datetime.now() + relativedelta(hours =+ 23);
                        rdate = datetime.datetime.now() + relativedelta(hours =+ 22);

                        tokens.inserttvdbtoken(token, edate, rdate);

            except Exception as inst:
                logger.error(inst);

                pass;


        if tokenexpired or token is None:

            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'};
            payload = {'apikey': apikey};

            try:

                rurl = url % 'login';
                payload = json.dumps(payload);

                result = client.request(rurl, post=payload, headers=headers, redirect=False);

                if result is not None:

                    token = json.loads(result)['token'];

                    if token:

                        edate = datetime.datetime.now() + relativedelta(hours =+ 23);
                        rdate = datetime.datetime.now() + relativedelta(hours =+ 22);

                        tokens.inserttvdbtoken(token, edate, rdate);

            except Exception as inst:
                logger.error(inst);

                pass;

        return token;

    except Exception as inst:
        logger.error(inst);

        return;


def checktvdbMeta(apikey, token, url, view, criteria, funshows, skipchecks=False):

    try:

        import json;
        import syncdata;

        from resources.lib.modules import client;
        from resources.lib.modules import trakt;
        #TODO Add Movie Support


        episodes = [d for d in funshows if d['video_type'].lower() == 'episode'.encode('utf-8')];
        movies = [d for d in funshows if d['video_type'].lower() == 'movie'.encode('utf-8')];

        assets = set([d['asset_id'] for d in episodes if 'asset_id' in d]);
        shows = set([d['show_id'] for d in episodes if 'show_id' in d]);

        if len(episodes) < 1:
            collected = syncdata.fetchepisodes(shows, assets);

        else:

            metarefresh = False;

            showid = episodes[0]['show_id'];
            showname = stripped(episodes[0]['show_name']);

            expired = syncdata.fetchfnmetacheck(showid);
            expired = expireddate(expired);

            if expired is False:

                collected = syncdata.fetchepisodes(shows, assets);
                synchistory(funshows, showid);

                if collected and len(collected) >= len(episodes):
                    return collected;

                else:
                    return None;


            else:
                from dateutil.relativedelta import relativedelta;
                
                rdate = datetime.datetime.now() + relativedelta(hours =+ 24);
                syncdata.insertfnmetacheck(showid, rdate);
            

            apikey = decode(base64.urlsafe_b64decode(apikey));
            token = token.encode('utf-8');

            headers = {'Accept': 'application/json', 'Authorization' : 'Bearer %s' % token};

            if not skipchecks:

                lastupdated = syncdata.fetchupdated(showid);

                if lastupdated:

                    for lut in lastupdated:
                        
                        try:

                            rurl = url % 'series/%s' % lut[0];

                            result = client.request(rurl, headers=headers, redirect=False);
                            lu_result = json.loads(result)['data']['lastUpdated'];

                            if int(lu_result) > int(lut[1]):
                                metarefresh = True;


                        except Exception as inst:
                            metarefresh = True;

                            logger.error(inst);

                            pass;

                else:
                    metarefresh = True;


            if metarefresh is False:

                collected = syncdata.fetchepisodes(shows, assets);

                if collected and len(collected) >= len(episodes):
                    synchistory(funshows, showid);

                    return collected;

                else:
                    metarefresh = True;


            if metarefresh and not skipchecks:

                if view == 'series':

                    try:

                        rurl = url % 'search/series?name=%s' % urllib.quote(criteria);

                        result = client.request(rurl, headers=headers, redirect=False);

                        if result is not None:

                            from dateutil import parser;


                            idx = 0;
                            rsize = 0;
                            absolute = 0;

                            ft_result = json.loads(result)['data'];

                            ft_result = [d for d in ft_result if stripped(d['seriesName']).startswith(showname)];


                            for series in ft_result:

                                rurl = url % 'series/%d' % series['id'];

                                result = client.request(rurl, headers=headers, redirect=False);

                                st_result = json.loads(result)['data'];

                                if st_result['seriesName'] != '** 403: Series Not Permitted **':
                                
                                    try:

                                        rurl = url % 'series/%d/episodes' % series['id'];

                                        result = client.request(rurl, headers=headers, redirect=False);
                                        tt_result = json.loads(result)['data'];
                                        pages = json.loads(result)['links']['last'];


                                        if pages > 1:

                                            for num in range(2, (int(pages) + 1)):
                                                
                                                rurl = url % 'series/%d/episodes/query?page=%d' % (series['id'], num);

                                                result = client.request(rurl, headers=headers, redirect=False);
                                                page_result = json.loads(result)['data'];

                                                tt_result += page_result;


                                        rurl = url % 'series/%d/images/query?subKey=graphical' % series['id'];

                                        artwork = client.request(rurl, headers=headers, redirect=False);
                                        artwork = json.loads(artwork);

                                        rurl = url % 'series/%d/images/query?keyType=poster' % series['id'];

                                        ar2work2 = client.request(rurl, headers=headers, redirect=False);
                                        ar2work2 = json.loads(ar2work2)['data'];

                                        for art in ar2work2:
                                            artwork['data'].append(art);

                                        artwork = json.dumps(artwork);

                                        firstEpisode = (idx + rsize) if idx > 0 else 1;
                                        genre = " / ".join(sorted(list(set(st_result.get('genre', '') + episodes[0].get('genre', '').split(',')))));

                                        airdate = parser.parse(st_result['firstAired'], dayfirst=False);
                                        airdate = airdate.strftime('%m-%d-%Y');

                                        series_dict = {
                                            'show_id':episodes[0]['show_id'],
                                            'tvdbid':st_result['id'],
                                            'imdbid':st_result['imdbId'],
                                            'seriesid':st_result['seriesId'],
                                            'traktid': None,
                                            'lastUpdated':st_result['lastUpdated'],
                                            'seriesName':st_result['seriesName'],
                                            'status':st_result['status'],
                                            'firstAired':airdate,
                                            'firstEpisode':firstEpisode,
                                            'network':st_result['network'],
                                            'genre':genre,
                                            'siteRating':st_result.get('siteRating', 10),
                                            'siteRatingCount':st_result.get('siteRatingCount', 0),
                                            'images':artwork
                                        };

                                        syncdata.inserttvdbseries(series_dict);

                                        idx += 1;
                                        rsize += len(tt_result);

                                        episode_dict = [];
                                        byepisode = build_dict(tt_result, key='absoluteNumber');


                                        for ep in episodes:
                                            try:
                                                
                                                epnumber = int(ep['number']);
                                                videotype = ep.get('video_type', 'Episode').encode('utf-8');

                                                if epnumber <= rsize and videotype.lower() == 'episode':

                                                    #if epnumber >= 104:

                                                    tvdb = byepisode[(epnumber - absolute)];

                                                    airdate = parser.parse(tvdb['firstAired'], dayfirst=False);
                                                    airdate = airdate.strftime('%m-%d-%Y');

                                                    episode_dict.append({
                                                        'show_id':ep['show_id'],
                                                        'episode_id': ep['asset_id'],
                                                        'tvdbid':st_result['id'],
                                                        'tvdbeid': tvdb['id'],
                                                        'overview': tvdb['overview'],
                                                        'description': ep['description'],
                                                        'absoluteNumber': int(tvdb['absoluteNumber']) + absolute,
                                                        'airedSeason': tvdb['airedSeason'],
                                                        'airedEpisodeNumber': tvdb['airedEpisodeNumber'],
                                                        'firstAired': airdate,
                                                        'episodeName': tvdb['episodeName'],
                                                        'sorttitle': ep['extended_title'],
                                                        'url': ep['url'],
                                                        'videotype': ep.get('video_type', 'Episode'),
                                                        'watched': 0,
                                                        'progress': 0,
                                                    });
                                                        

                                            except Exception as inst:
                                                #logger.error(inst);
                                                
                                                pass;

                                        
                                        absolute = rsize;
                                        
                                        if len(episode_dict) > 0:
                                            syncdata.inserttvdbepisodes(episode_dict);


                                    except Exception as inst:
                                        logger.error(inst);

                                        pass;

                                if syncdata.fetchepisodecount(showid) >= len(episodes):
                                    break;


                    except Exception as inst:
                        #logger.error(inst);

                        pass;
                    

                collected = syncdata.fetchepisodes(shows, assets);
                synchistory(funshows, showid);

                if collected and len(collected) >= len(episodes):
                    return collected;

                else:
                    return None;


    except Exception as inst:
        logger.error(inst);

        return None;


def syncqueue(funshows, queuestate=0):

    if len(funshows) > 0:
        import syncdata;

        try:

            syncdata.updatefnqueue(funshows, queuestate);

        except Exception as inst:
            logger.error(inst);
            pass;


def getqueuestatus(showid):
    import syncdata;

    try:

        return syncdata.fetchqueuestate(showid);

    except Exception as inst:
        logger.error(inst);
        
        return;


def addremovequeueitem(meta):
    import json;
    import syncdata;

    from resources.lib.modules import client;
    from resources.lib.modules import cookiecache;
    from resources.lib.modules import control;
    
    try:

        uid = setting('fn.uid');

        if uid is not None:

            agent = setting(control.lang(32215).encode('utf-8'));

            if agent is None:
                agent = 'Sony-PS3';

            headers = {'User-Agent': agent, 'Content-Type': 'application/json'};
            payload = {'username': uid, 'show_id': meta['asset_id']};

            url = 'http://www.funimation.com/feeds/ps/';

            if int(meta['state']) > 0:
                url = str('%saddToQueue' % url);
                #{"success":true,"message":"Show added to queue successfully."}

            else:
                url = str('%sremoveFromQueue' % url);
                #{"success":true,"message":"Show removed from queue successfully."}


            payload = json.dumps(payload);

            result = client.request(url, post=payload, headers=headers);
            result = json.loads(result)['success'];

            if result == True:
                return syncdata.addremovefnqueue(meta);

            else:

                if int(meta['state']) > 0:
                    return (False, "There was an error adding %s to your anime queue." % meta['series_name']);

                else:
                    return (False, "There was an error removing %s from your anime queue." % meta['series_name']);

    except Exception as inst:
        logger.error(inst);
        
        if int(meta['state']) > 0:
            return (False, "There was an error adding %s to your anime queue." % meta['series_name']);

        else:
            return (False, "There was an error removing %s from your anime queue." % meta['series_name']);


def synchistory(funshows, showid):

    if len(funshows) > 0:
        import json;
        import syncdata;

        from resources.lib.modules import client;
        from resources.lib.modules import cookiecache;
        from resources.lib.modules import control;
        from resources.lib.modules import trakt;
        from dateutil.relativedelta import relativedelta;


        try:

            expired = syncdata.fetchfnhistorycheck(showid);
            expired = expireddate(expired);

            if expired:
                
                rdate = datetime.datetime.now() + relativedelta(hours =+ 24);
                syncdata.insertfnhistorycheck(showid, rdate);

                syncdata.insertfnepisodes(funshows, 'series');

                uid = setting('fn.uid');

                if uid is not None:

                    cookie = cookiecache.fetch(uid.lower(), 1);
                    agent = setting(control.lang(32215).encode('utf-8'));

                    if agent is None:
                        agent = 'Sony-PS3';

                    headers = {'User-Agent': agent};

                    historyset = client.request(funimation_url % (uid, showid), headers=headers, redirect=False, cookie=cookie);
                    historyset = json.loads(historyset);

                    if 'videos' not in historyset:
                        syncdata.insertfnepisodes(historyset, 'history');


        except Exception as inst:
            logger.error(inst);
            pass;


        if trakt.getTraktCredentialsInfo():

            try:

                expired = syncdata.fetchtraktprogresslastupdated();
                expired = expireddate(expired);

                if expired:
                    traktprogress = trakt.getTrakt('sync/playback/episodes?type=episodes');
                    traktprogress = json.loads(traktprogress);

                    rdate = datetime.datetime.now() + relativedelta(hours =+ 24);

                    syncdata.synctraktprogress(traktprogress, rdate);

            except Exception as inst:
                logger.error(inst);
                pass;

            try:

                expired = syncdata.fetchtraktwatchedcheck(showid);
                expired = expireddate(expired);

                if expired:
                    
                    rdate = datetime.datetime.now() + relativedelta(hours =+ 24);
                    syncdata.inserttraktwatchedcheck(showid, rdate);

                    tvdbids = syncdata.fetchupdated(showid);

                    for tvdbid in tvdbids:
                        
                        traktids = trakt.getTrakt('search/tvdb/%s?id_type=tvdb&id=%s&type=show' % (tvdbid[0], tvdbid[0]));

                        try:

                            traktids = json.loads(traktids)[0]['show']['ids'];

                            watched = trakt.getTrakt('shows/%s/progress/watched?hidden=false&specials=false&count_specials=false' % traktids['slug']);
                            seasons = json.loads(watched)['seasons'];

                            for season in seasons:

                                for ep in season['episodes']:
                                    
                                    ep.update({
                                        'show_id': showid,
                                        'season_number': season['number'],
                                        'trakt_series_id': traktids['trakt'],
                                        'trakt_slug': traktids['slug'],
                                        'tvdbid': tvdbid[0],
                                        'completed': (1 if ep['completed'] is True else 'NULL')
                                    });

                                syncdata.insertfnepisodes(season['episodes'], 'trakt');


                        except Exception as inst:
                            logger.error(inst);
                            pass;


            except Exception as inst:
                logger.error(inst);
                pass;


def getshowname(showid):
    import syncdata;

    try:

        return syncdata.fetchshowname(showid);

    except Exception as inst:
        logger.error(inst);
        
        return;


def getartwork(showid):
    import json;
    import syncdata;

    try:

        return syncdata.fetchartwork(showid);

    except Exception as inst:
        logger.error(inst);
        
        return;


def getshowstatus(showid):
    import json;
    import syncdata;

    try:

        return syncdata.fetchshowstatus(showid);

    except Exception as inst:
        logger.error(inst);
        
        return;


def favorites():
    import json;
    from resources.lib.modules import control;
    
    try:

        favs = control.jsonrpc('{"jsonrpc": "2.0", "method": "Favourites.GetFavourites", "params": { "properties": ["path", "windowparameter"] }, "id": "1"}');
        favs = json.loads(favs);
        
        favs = list(set([item for sublist in [[d.get('windowparameter', None), d.get('path', None)] for d in favs['result']['favourites']] for item in sublist if item is not None]));

        return favs;

    except Exception as inst:
        logger.error(inst);

        return [];


def updatefavorites(params):
    import json;

    from resources.lib.modules import control;

    url = None;
    title = None;
    thumbnail = None;
    isFolder = None;

    try:


        if 'action' in params:
            params.pop('action');

        if 'url' in params:
            url = re.sub('/action', '/?action', params['url']);
            params.pop('url');

        if 'name' in params:
            title = params['name'];
            params.pop('name');

        if 'posterart' in params:
            thumbnail = params['posterart'];
            params.pop('posterart');

        if 'isFolder' in params:
            isFolder = params['isFolder'];
            params.pop('isFolder');

        if url:

            import json;
            import xbmcgui;
            from resources.lib.modules import control;

            params = urllib.urlencode(params);
            url += ('&' + params);

            if isFolder == 'True':

                wid = xbmcgui.getCurrentWindowId();

                favs = control.jsonrpc('{"jsonrpc": "2.0", "method": "Favourites.AddFavourite", "params": {"title": "%s", "type": "window", "windowparameter": "%s", "thumbnail": "%s", "window": "%s"}, "id": 1}' % (title, url, thumbnail, 10025));

            else:
                favs = control.jsonrpc('{"jsonrpc": "2.0", "method": "Favourites.AddFavourite", "params": {"title": "%s", "type": "media", "path": "%s", "thumbnail": "%s"}, "id": 1}' % (title, url, thumbnail));

            favs = json.loads(favs);

            if 'result' in favs and favs['result'] != 'OK':
                sendNotification(32506, 5000);

            else:
                control.refresh();


    except Exception as inst:
        logger.error(inst);
        sendNotification(32506, 5000);

        pass;


def stripped(name):

    name = name.strip();
    name = name.lower();
    name = re.sub('[^a-z0-9]', '', name);
    name.encode('utf-8');

    return name;


def build_dict(seq, key):

    return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq));


def expireddate(date):
    from dateutil import parser;

    if date is not None:

        try:

            present = datetime.datetime.now();
            edate = parser.parse(date.encode('utf-8'));
                
            if present >= edate:
                return True;

            else:
                return False;

        except Exception as inst:
            logger.error(inst);
            pass;

        return True;

    else:
        return True;


def resetsettings():
    from resources.lib.modules import control;

    for key in ['cookie_experation', 'user_age', 'user_birthday', 'user_id', 'user_type']:

        try:
            setting(str('fn.' + key), '');

        except Exception as inst:
            logger.error(inst);
            
            pass;


    try:

        setting('fn.ut', control.lang(32600).encode('utf-8'));
        setting('fn.subscriber_status', control.lang(32601).encode('utf-8'));
        setting('fn.user_role', control.lang(32602).encode('utf-8'));
        setting('fn.user_agent', control.lang(32603).encode('utf-8'));

    except Exception as inst:
        logger.error(inst);

        pass;


def updatesettings(settings):
    import json;

    try:

        settings = json.loads(settings);

        for key in settings:

            setid = ('fn.' + key);
            setval = settings[key];

            setting('fn.' + key, str(setval));

    except Exception as inst:
        logger.error(inst);

        resetsettings();


def implementsearch():
    from resources.lib.modules import control;

    try:

        control.idle();

        title = control.lang(32726).encode('utf-8');
        kb = control.keyboard('', title); 
        
        kb.doModal();
        
        text = kb.getText() if kb.isConfirmed() else None;

        if (text == None or text == ''): 
            return None;

        else:
            return text;

    except Exception as inst:
        logger.error(inst);

        return None;


def promptForLogin(prompt=None):
    import xbmcgui;
    from resources.lib.modules import control;

    __settings__ = xbmcaddon.Addon(control.addonInfo('id'))

    if prompt:
        if xbmcgui.Dialog().yesno(control.lang(32755).encode('utf-8'), control.lang(32756).encode('utf-8'), control.lang(32757).encode('utf-8')):
            __settings__.openSettings();

    else:
        __settings__.openSettings();

    #else: # if user chose no then end the script
       # sys.exit();


def sendNotification(msg, time):
    import xbmc;
    from resources.lib.modules import control;

    addonname = addon.getAddonInfo('name');
    icon = addon.getAddonInfo('icon');
     
    if not isinstance(msg, basestring):
        msg = control.lang(msg).encode('utf-8');
     
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(addonname, msg, time, icon));