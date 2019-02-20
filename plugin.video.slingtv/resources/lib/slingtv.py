#   Copyright (C) 2018 Lunatixz, eracknaphobia, d21spike
#
#
# This file is part of Sling.TV.
#
# Sling.TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sling.TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sling.TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, pytz, calendar, random, hashlib, xmltodict
import urlparse, urllib, urllib2, socket, json, requests, base64, inputstreamhelper
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
                            
from simplecache import SimpleCache, use_cache
from resources.lib.globals import *
from .login import UserClient

socket.setdefaulttimeout(TIMEOUT)
class SlingTV(object):
    def __init__(self, sysARG):
        log('__init__')
        self.sysARG      = sysARG
        self.cache       = SimpleCache()
        self.endPoints   = self.buildEndpoints()
        self.user        = UserClient()
        self.contentType = 'episodes'
            
            
    def getURL(self, url, header=HEADERS, life=datetime.timedelta(minutes=5), auth=None):
        try:
            log('getURL, url = ' + url + " | Auth= " + str(auth))
            cacheresponse = self.cache.get(ADDON_NAME + '.getURL, url = %s'%url)
            if not cacheresponse:
                if auth is not None:
                    response = requests.get(url, headers=header, auth=auth, verify=VERIFY)
                else:
                    response = requests.get(url, headers=header, verify=VERIFY)
                    if response.status_code == 403:
                        response = requests.get(url, headers=header, auth=self.user.getAuth(), verify=VERIFY)
                if response.status_code == 200:
                    cacheresponse = response.json()
                    if 'message' in cacheresponse: return
                    self.cache.set(ADDON_NAME + '.getURL, url = %s'%url, dumpJSON(cacheresponse), expiration=life)
                if 'message' in response.json():
                    notificationDialog(response.json()['message'])
            if isinstance(cacheresponse, basestring):
                cacheresponse = loadJSON(cacheresponse)
            return cacheresponse
        except Exception as e:
            log("getURL Failed! " + str(e), xbmc.LOGERROR)
            notificationDialog(LANGUAGE(30001))
            return {}
            
            
    def buildMenu(self):
        response = self.getURL(MAIN_URL)
        self.addDir(LANGUAGE(30015), '', 'live')
        self.addDir(LANGUAGE(30017), '', 'vod')
        for item in response:
            # Omit Rentals for the time being
            if item['title'].lower() == 'rentals': continue
            self.addDir(item['title'].title(), (item.get('url') or item['id']), item['id'], False, {'thumb':item.get('thumbnail',{}).get('url',ICON)})

            
    def buildOnNow(self, context):
        success, region = self.user.getRegionInfo()
        if not success:
            notificationDialog(LANGUAGE(30016))
            return

        USER_DMA = region['USER_DMA']
        USER_OFFSET = region['USER_OFFSET']

        if USER_SUBS == '' or USER_DMA == '' or USER_OFFSET == '': return
        dashboardUrl = "https://p-mgcs.movetv.com/rubens-online/rest/v1/dma/{}/offset/{}/domain/1/product/sling/platform/browser/context/{}/ribbons?sub_pack_ids={}"
        dashboardUrl = dashboardUrl.format(USER_DMA, USER_OFFSET, context, USER_SUBS)
        log('buildOnNow, Dashboard URL = ' + dashboardUrl)
        response = self.getURL(dashboardUrl)
        if response:
            ribbons = response['ribbons']
            for ribbon in ribbons:
                ribbonUrl = ribbon['_href']
                response = self.getURL(ribbonUrl)
                if response:
                    tile_count = response['total_tiles']
                    if tile_count > 0:
                        log('buildOnNow, ribbon = ' + str(ribbon['title']))
                        self.addDir(ribbon['title'], ribbonUrl, 'on_now_item')

                    
    def buildOnNowItems(self, name, ribbonUrl):
        ribbonName = urllib.quote(name)
        log('getRibbonChannels, ribbon = ' + name)
        log('getRibbonChannels, ribbonUrl = ' + ribbonUrl)
        response = self.getURL(ribbonUrl)
        if response:
            tiles = response['tiles']
            for tile in tiles:
                log('getRibbonChannels, ribbon = ' + tile['title'].encode("utf-8"))
                infoLabels, infoArt = self.setAssetInfo(tile)
                start_time = stringToDate(tile['start_time'], '%Y-%m-%dT%H:%M:%SZ')
                if start_time < datetime.datetime.utcnow():
                    self.addLink(infoLabels['label'], tile['qvt'], 'play', infoLabels, infoArt)
                else:
                    title = 'Upcoming - ' + utcToLocal(start_time).strftime('%m/%d %H:%M') + ' - ' + infoLabels['label']
                    self.addDir(title, '', 'no_play', infoLabels, infoArt)

                
    def buildMyChannels(self):
        url = '%s/watchlists/v4/watches?product=sling&platform=browser' % (self.endPoints['environments']['production']['cmw_url'])
        myChannels = self.getURL(url, HEADERS, auth=self.user.getAuth())['favorites']
        for fav in myChannels:
            url = '%s/cms/publish3/channel/schedule/24/1810090400/1/%s.json'%(self.endPoints['environments']['production']['cms_url'], fav['guid'])
            schedule = self.getURL(url)
            channel = schedule['schedule']
            meta = channel['metadata']
            label = (meta['channel_name'] or meta['title'] or meta['call_sign'])
            thumb = (channel.get('thumbnail', {}).get('url', '') or ICON)
            logo = (meta.get('thumbnail_cropped', {}).get('url', '') or ICON)
            fanart = (meta.get('default_schedule_image', {}).get('url', '') or FANART)
            infoLabels = {'label': label, 'title': label, 'genre': meta.get('genre', '')}
            infoArt = {'thumb': thumb, 'poster': thumb, 'fanart': fanart, 'logo': logo, 'clearlogo': logo}
            self.addLink(label, channel['qvt_url'], 'play',infoLabels, infoArt)

            
    def buildContinueWatching(self):
        url = '%s/resumes/v4/resumes.json?platform=browser&product=sling' % (self.endPoints['environments']['production']['cmw_url'])
        resumes = self.getURL(url, HEADERS, auth=self.user.getAuth(), life=datetime.timedelta(minutes=1))
        for show in resumes:
            jsonBlock = self.getURL('%s/cms/publish3/asset/info/%s.json' % (self.endPoints['environments']['production']['cms_url'], show['external_id']))
            if jsonBlock is None:
                continue

            qvt_url = None
            if len(jsonBlock['schedules']) > 0:
                qvt_url = jsonBlock['schedules'][0]['playback_info']
            elif len(jsonBlock['entitlements']) > 0:
                qvt_url = jsonBlock['entitlements'][0]['qvt_url']

            if qvt_url is not None:
                infoLabels, infoArt = self.setAssetInfo(jsonBlock)
                properties = {'totaltime': str(show['duration']),
                              'resumetime': str(show['position'])}
                self.addLink(infoLabels['label'], qvt_url, 'play', infoLabels, infoArt, 0, None, properties)

            
    def setAssetInfo(self, jsonBlock, meta=True):
        try:
            channelGuid = jsonBlock['channel']['guid']
        except:
            channelGuid = ''
            
        asset_info = jsonBlock
        metadata   = jsonBlock
        if meta and '_href' in jsonBlock:
            try:
                url = jsonBlock['_href']
                asset_info = self.getURL(url, life=datetime.timedelta(days=7))
                metadata = asset_info['metadata']
            except Exception as e:
                log("setAssetInfo, extra meta Failed! " + str(e), xbmc.LOGERROR)
                
        # -------------------------------
        # Info Labels
        # -------------------------------
        if len(asset_info) == 0: asset_info = jsonBlock
        title = asset_info['title'].encode("utf-8")
        tv_show_title = ''
        if 'episode_title' in metadata:
            tv_show_title = title
            title = metadata['episode_title']

        infoLabels = {'label': title, 'title': title}
        
        # -------------------------------
        # Conditional Info
        # -------------------------------

        if 'id' in asset_info:
            infoLabels['tracknumber'] = asset_info['id']
        
        if 'year' in asset_info:
            infoLabels['year'] = asset_info['release_year']
        
        if 'duration' in asset_info:
            infoLabels['duration'] = asset_info['duration']
            
        if 'celebrities' in asset_info and 'director' in asset_info['celebrities']:
            infoLabels['director'] = asset_info['celebrities']['director'][0]['display_name']
        elif 'director' in metadata:
            infoLabels['director'] = metadata['director'][0]

        if 'genre' in metadata:
            infoLabels['genre'] = metadata['genre']

        if 'description' in metadata:
            infoLabels['plot'] = metadata['description'].encode("utf-8")

        if tv_show_title != '':
            infoLabels['tvshowtitle'] = tv_show_title

        type = (jsonBlock.get('type','') or asset_info.get('type','') or metadata.get('type','video'))                   
        if type == 'movie' or 'Film' in metadata.get('category',''):
            infoLabels['mediatype'] = 'movie'
        elif 'episode_number' in metadata:
            if 'episode_season' in metadata:
                infoLabels['season'] = int(metadata['episode_season'])
            elif 'season_number' in metadata:
                infoLabels['season'] = int(metadata['season_number'])
            infoLabels['episode'] = int(metadata['episode_number'])
            infoLabels['mediatype'] = 'episode'    
        elif 'type' in metadata:
            if metadata['type'] == 'series': infoLabels['mediatype'] = 'tvshow'
        else:
            infoLabels['mediatype'] = 'video'
            
        if 'ratings' in metadata:
            mpaa = metadata['ratings'][0]
            mpaa = mpaa.replace('US_UPR_','')
            mpaa = mpaa.replace('US_MPAA_', '')
            infoLabels['mpaa'] = mpaa

        if 'celebrities' in asset_info and 'cast' in asset_info['celebrities']:
            infoLabels['cast'] = [person['display_name'] for person in asset_info['celebrities']['cast']]

        # -------------------------------
        # Info Art
        # -------------------------------
        thumb = ICON
        if 'program' in asset_info and 'thumbnail' in asset_info['program'] and asset_info['program']['thumbnail'] is not None:
                thumb = asset_info['program']['thumbnail']['url']
        elif 'thumbnail' in asset_info and asset_info['thumbnail'] is not None:
            thumb = asset_info['thumbnail']['url']

        fanart = FANART
        if 'program' in asset_info:
            if 'background_image' in asset_info['program'] and asset_info['program']['background_image'] is not None:
                fanart = asset_info['program']['background_image']['url']
        elif 'thumbnail' in asset_info and asset_info['thumbnail'] is not None:
            fanart = asset_info['thumbnail']['url']

        try:
            channel_logo = jsonBlock['channel']['image']['url']
        except:
            channel_logo = ''

        if channelGuid != '' and channel_logo == '' and 'schedules' in asset_info:
            for logo in asset_info['schedules']:
                if logo['channel_guid'] == channelGuid:
                    channel_logo = logo['channel_image']['url']
                    break

        if channel_logo != '' and thumb == ICON:
            thumb = channel_logo

        if channel_logo != '' and fanart == FANART:
            fanart = channel_logo

        infoArt = {
            'thumb': thumb,
            'poster': thumb,
            'fanart': fanart,
            'logo': channel_logo,
            'clearlogo': channel_logo
        }
        return infoLabels, infoArt


    @use_cache(1)
    def buildEndpoints(self):
        return (self.getURL(WEB_ENDPOINTS))
        
        
    #@use_cache(1)
    def getChannels(self):
        log('getChannels')
        success, region = self.user.getRegionInfo()
        if not success:
            notificationDialog(LANGUAGE(30016))
            return

        USER_DMA = region['USER_DMA']
        USER_OFFSET = region['USER_OFFSET']

        channelURL = '%s/cms/publish3/domain/channels/v4/%s/%s/%s/1.json' % \
                     (self.endPoints['environments']['production']['cms_url'], USER_OFFSET, USER_DMA,
                      base64.b64encode(LEGACY_SUBS.replace('+', ',')))
        subpacks = self.getURL(channelURL)['subscriptionpacks']
        for subpack in subpacks:
            if 'channels' in subpack:
                for channel in subpack['channels']:
                    yield dict(channel)
        
        
    def buildLive(self, channel_type):
        log('buildLive')
        channels = self.getChannels()
        for channel in channels:
            log(str(channel))
            meta   = channel['metadata']
            label  = (meta.get('channel_name','') or meta.get('title','') or meta.get('call_sign',''))
            thumb  = (channel.get('thumbnail',{}).get('url','') or ICON)
            logo   = (meta.get('thumbnail_cropped',{}).get('url','') or ICON)
            fanart = (meta.get('default_schedule_image',{}).get('url','') or FANART)
            infoLabels = {'label': label, 'title': label, 'genre': meta.get('genre', '')}
            infoArt    = {'thumb':thumb,'poster':thumb,'fanart':fanart,'logo':logo,'clearlogo':logo}
            on_demand = False
            on_demand_url = '%s/cms/api/channels/%s/network' % \
                            (self.endPoints['environments']['production']['cms_url'], channel['channel_guid'])
            response = self.getURL(on_demand_url)
            log('CHANNELRESPONSE => ' +str(response))
            if response is not None and len(response):
                for category in response:
                    if len(category['tiles']) > 0:
                        on_demand = True
                        break
            if channel_type == 'vod' and on_demand:
                self.addDir(label, on_demand_url, 'on_demand', infoLabels, infoArt)
            else:
                self.addLink(label, channel['qvt_url'], 'play', infoLabels, infoArt)

        xbmcplugin.addSortMethod(int(self.sysARG[1]), xbmcplugin.SORT_METHOD_LABEL)


    def buildOnDemand(self, url):
        items = (self.getURL(url))
        if 'ribbon=' not in url and items is not None:
            for item in items:
                self.addDir(item['title'], item['_href'], 'on_demand', False, False)
        else:
            tiles = (self.getURL(url))['tiles']
            for item in tiles:
                if item['type'] == 'series':
                    label = item['title']
                    thumb = item['thumbnail']['url']
                    fanart = thumb
                    logo = item['network_thumbnail']['url']
                    infoLabels = {'label': label, 'title': label}
                    infoArt = {'thumb': thumb, 'poster': thumb, 'fanart': fanart, 'logo': logo, 'clearlogo': logo}
                    self.addDir(item['title'], item['_href'], 'tv_show', infoLabels, infoArt)
                else:
                    jsonBlock = self.getURL('%s/cms/publish3/asset/info/%s.json' % (self.endPoints['environments']['production']['cms_url'], item['external_id']))
                    if jsonBlock is None:
                        continue
                    start_time = ''
                    try:
                        for source in jsonBlock['entitlements']:
                            start_time = stringToDate(source['playback_start'], '%Y-%m-%dT%H:%M:%SZ')
                            stop_time = stringToDate(source['playback_stop'], '%Y-%m-%dT%H:%M:%SZ')
                            qvt_url = source['qvt_url']
                            if start_time < datetime.datetime.utcnow() < stop_time:
                                break
                    except:
                        continue

                    infoLabels, infoArt = self.setAssetInfo(jsonBlock)
                    if start_time != '':
                        if start_time < datetime.datetime.utcnow():
                            self.addLink(infoLabels['label'], qvt_url, 'play', infoLabels, infoArt)
                        else:
                            title = 'Upcoming - ' + utcToLocal(start_time).strftime('%m/%d %H:%M') \
                                    + ' - ' + infoLabels['label']
                            self.addDir(title, '', 'no_play', infoLabels, infoArt)

            if '_next' in items.keys():
                self.buildOnDemand(items['_next'])


    def buildMyTV(self, name, item=None):
        log('buildMyTV, name = %s'%(name))
        if item is None:
            items = (self.getURL(MYTV))['ribbons']
            for item in items:
                item['page'] = 0
                if '_href' not in item:
                    self.addDir(item['title'], dumpJSON(item), 'my_tv_item', False, {'thumb':'%s/config/shared/images/mytv-icon.png'%(BASE_WEB)})
                else:
                    url = item['_href'].replace('{{','{').replace('}}','}').replace(' ','%20').replace('my_tv_tvod','my_tv')
                    url = url.format(dma=USER_DMA, timezone_offset=USER_OFFSET, domain='1', product='sling', platform='browser', subscription_pack_ids=USER_SUBS,legacy_subscription_pack_ids=LEGACY_SUBS, page_size='large')
                    # Check if href is empty so we don't display an empty listitem, cache this for a day or two?
                    response = self.getURL(url, life=datetime.timedelta(days=1))
                    if response:
                        if response['total_tiles'] > 0:
                            self.addDir(response['title'], dumpJSON(item), 'my_tv_item', False, {'thumb':'%s/config/shared/images/mytv-icon.png'%(BASE_WEB)})
        else:
            page  = item['page']
            if 'my channels' == item['title'].lower():
                self.buildMyChannels()
            elif 'continue watching' == item['title'].lower():
                self.buildContinueWatching()
            elif '_href' in item:
                url = item['_href'].replace('{{','{').replace('}}','}').replace('page=0','page=%d'%(page)).replace(' ','%20').replace('my_tv_tvod','my_tv')
                url = url.format(dma=USER_DMA, timezone_offset=USER_OFFSET, domain='1', product='sling', platform='browser', subscription_pack_ids=USER_SUBS,legacy_subscription_pack_ids=LEGACY_SUBS, page_size='large')
                log(url)
                items = (self.getURL(url))

                if 'movies' in item['title'].lower():
                    movies = items['tiles']
                    for movie in movies:
                        infoLabels, infoArt = self.setAssetInfo(movie)
                        self.addLink(infoLabels['label'], movie['qvt'], 'play',infoLabels, infoArt)
                if 'shows' in item['title'].lower():
                    shows = items['tiles']
                    for show in shows:
                        infoLabels, infoArt = self.setAssetInfo(show, meta=False) 
                        self.addDir(infoLabels['label'], show['_href'], 'tv_show', infoLabels, infoArt)
                elif items is None:
                    self.addDir(LANGUAGE(30014), '', '')
                elif items and len(items.get('tiles',[])) == 0:
                    self.addDir(LANGUAGE(30014), '', '')
                else:
                    shows = items['tiles']
                    for show in shows:
                        infoLabels, infoArt = self.setAssetInfo(show)
                        self.addLink(infoLabels['label'], show['qvt'], 'play' ,infoLabels, infoArt)
            
                    
    def buildShow(self, name, url=None):
        log('buildShow, name = %s'%(name))
        item = (self.getURL(url, auth=self.user.getAuth()))
        seasons = item.get('seasons',[])

        if seasons:
            self.buildSeasons(seasons)


    def buildSeasons(self, seasons):
        for season in seasons:
            programs = season['programs']
            self.buildPrograms(programs)


    def buildPrograms(self, programs):
        for program in programs:
            try:
                next_airing_time = None
                for airing in program['airings']:
                    start_time = stringToDate(airing['availability'][0]['start'], '%Y-%m-%dT%H:%M:%SZ')
                    stop_time = stringToDate(airing['availability'][0]['stop'], '%Y-%m-%dT%H:%M:%SZ')
                    if start_time < datetime.datetime.utcnow() < stop_time:
                        next_airing_time = None
                        link = airing['availability'][0]['qvt']  # todo add stream select?
                        break
                    elif start_time > datetime.datetime.utcnow():
                        if next_airing_time is None or next_airing_time > start_time:
                            next_airing_time = start_time
            except:
                continue

            if (start_time > datetime.datetime.utcnow() or datetime.datetime.utcnow() > stop_time) and next_airing_time is None:
                continue

            title = program['name']
            infoLabels, infoArt = self.setAssetInfo(airing)
            if next_airing_time is None:
                self.addLink(title, link, 'play',infoLabels, infoArt, len(programs))
            else:
                title = 'Next Airing - ' + utcToLocal(next_airing_time).strftime('%m/%d %H:%M') + ' - ' + title
                self.addDir(title, '', 'no_play',infoLabels, infoArt)


    def search(self, result_url=None):
        if result_url is None:
            keyword = inputDialog('Shows, Movies...')
            if keyword is not None:
                headers = {
                    'Origin': 'https://watch.sling.com',
                    'User-Agent': USER_AGENT,
                    'Accept': '*/*',
                    'Referer': 'https://watch.sling.com/browse/dynamic/on-now',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
                tv_results = self.getURL('%s/cms/api/search/v2/franchises/keyword=%s;subpacks=%s;timezone=%s;dma=%s' %
                                         (self.endPoints['environments']['production']['cms_url'], urllib.quote_plus(keyword),
                                         base64.b64encode(sortGroup(LEGACY_SUBS.replace('+', ','))), USER_OFFSET, USER_DMA),
                                         header=headers)
                for item in tv_results['franchises']:
                    label = item['title']
                    thumb = item['image']['url']
                    fanart = thumb
                    infoLabels = {'label': label, 'title': label}
                    infoArt = {'thumb': thumb, 'poster': thumb, 'fanart': fanart,}
                    self.addDir(item['title'], item['_href'], 'search_result', infoLabels, infoArt)
        else:
            result = self.getURL(result_url)
            if result:
                if 'seasons' in result:
                    self.buildSeasons(result['seasons'])
                elif 'programs' in result:
                    self.buildPrograms(result['programs'])
            else:
                sys.exit()


    def resolverURL(self, url):
        log('resolverURL, url = ' + url)
        video = (self.getURL(url))
        if video is None or 'message' in video: return
        if 'playback_info' not in video: sys.exit()
        mpd_url = video['playback_info']['dash_manifest_url']
        qmx_url = video['playback_info']['clips'][0]['location']
        if 'UNKNOWN_' not in mpd_url:
            qmx = (self.getURL(qmx_url))
            if 'message' in qmx: return
            lic_url = ''
            if 'encryption' in qmx:
                lic_url = qmx['encryption']['providers']['widevine']['proxy_url']
                log('resolverURL, lic_url = ' + lic_url)

            if 'channel_guid' in video:
                channel_id = video['channel_guid']
            if 'playback' in video and 'linear_info' in video['playback_info']:
                channel_id = video['playback_info']['linear_info']['channel_guid']
            elif 'playback' in video and 'asset' in video['playback_info']:
                channel_id = video['playback_info']['asset']['guid']
            elif 'playback_info' in video and 'vod_info' in video['playback_info']:
                try: channel_id = video['playback_info']['vod_info']['svod_channels'][0]
                except: channel_id = ''
            else:
                channel_id = ''

            license_key = ''
            if lic_url != '':
                license_key = '%s||{"env":"production","user_id":"%s","channel_id":"%s","message":[D{SSM}]}|'%(lic_url,self.user.getUserID(), channel_id)

            log('license_key = ' + license_key)
        else:
            if 'vod_info' in video['playback_info']:
                fod_url = video['playback_info']['vod_info'].get('media_url', '')
                response = requests.get(fod_url, headers=HEADERS, verify=VERIFY)
                if response.status_code == 200:
                    mpd_url = response.json()['stream']
                    license_key = ''
                elif 'message' in response.json():
                    notificationDialog(response.json()['message'])
            elif 'linear_info' in video['playback_info'] \
                    and 'disney_stream_service_url' in video['playback_info']['linear_info']:
                log('resolverURL, Inside Disney/ABC')
                utc_datetime = str(time.mktime(datetime.datetime.utcnow().timetuple())).split('.')[0]
                sha1_user_id = hashlib.sha1(SUBSCRIBER_ID).hexdigest()
                rsa_sign_url = '%s/cmw/v1/rsa/sign' % self.endPoints['environments']['production']['cmw_url']
                stream_headers = HEADERS
                stream_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                payload = 'document=%s_%s_' % (sha1_user_id, utc_datetime)
                log('resolverURL, RSA payload => %s' % payload)
                response = requests.post(rsa_sign_url, headers=stream_headers, data=payload, verify=VERIFY)
                if response.status_code == 200 and 'signature' in response.json():
                    signature = response.json()['signature']
                    log('resolverURL, RSA Signature => %s' % signature)
                    disney_info = video['playback_info']['linear_info']
                    if 'abc' in disney_info['disney_network_code']:
                        brand = '003'
                    else:
                        brand = disney_info['disney_brand_code']
                    params = {
                        'ak': 'fveequ3ecb9n7abp66euyc48',
                        'brand': brand,
                        'device': '001_14',
                        'locale': disney_info.get('disney_locale', ''),
                        'token': '%s_%s_%s' % (sha1_user_id, utc_datetime, signature),
                        'token_type': 'offsite_dish_ott',
                        'user_id': sha1_user_id,
                        'video_type': 'live',
                        'zip_code': USER_ZIP
                    }
                    service_url = disney_info['disney_stream_service_url']
                    log('service url %s' % service_url)
                    payload = ''
                    for key in params.keys():
                        payload += '%s=%s&' % (key, params[key])
                    payload = payload[:-1]
                    response = requests.post(service_url, headers=stream_headers, data=payload, verify=VERIFY)
                    if response.status_code == 200:
                        log(str(response.text))
                        session_xml = xmltodict.parse(response.text)
                        service_stream = session_xml['playmanifest']['channel']['assets']['asset']['#text']
                        log('resolverURL, XML Stream: ' + str(service_stream))
                        mpd_url = service_stream
                        license_key = ''

        asset_id = ''
        if 'entitlement' in video and 'asset_id' in video['entitlement']:
            asset_id = video['entitlement']['asset_id']

        return mpd_url, license_key, asset_id

        
    def playVideo(self, name, url, liz=None):
        log('playVideo, url = ' + url)
        try:
            url, license_key, external_id = self.resolverURL(url)
        except:
            license_key = ''
            external_id = ''
        if 'mpd' in url:
            is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
            if not is_helper.check_inputstream():
                sys.exit()
            liz = xbmcgui.ListItem(name, path=url)
            liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+USER_AGENT)
            if license_key != '':
                liz.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                liz.setProperty('inputstream.adaptive.license_key', license_key)
            liz.setMimeType('application/dash+xml')
            liz.setContentLookup(False)
            xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)
        else:
            liz = xbmcgui.ListItem(name, path=url)
            xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)

        # Hack to fix 6 channel audio causing buffering issues
        while not xbmc.Player().isPlayingVideo():
            xbmc.Monitor().waitForAbort(0.25)

        if xbmc.Player().isPlayingVideo() and len(xbmc.Player().getAvailableAudioStreams()) > 1:
            xbmc.Player().setAudioStream(0)

        if external_id != '':
            while xbmc.Player().isPlayingVideo() and not xbmc.Monitor().abortRequested():
                position = int(float(xbmc.Player().getTime()))  # Get timestamp of video from VideoPlayer to save as resume time
                duration = int(float(xbmc.Player().getTotalTime()))  # Get the total time of video playing
                xbmc.Monitor().waitForAbort(3)

            self.setResume(external_id, position, duration)


    def setResume(self, external_id, position, duration):
        # If there's only 2 min left delete the resume point
        if duration - position < 120:
            url = '%s/resumes/v4/resumes/%s' % (self.endPoints['environments']['production']['cmw_url'], str(external_id))
            payload = '{"platform":"browser","product":"sling"}'
            requests.delete(url, headers=HEADERS, data=payload, auth=self.user.getAuth(), verify=VERIFY)
        else:
            url = '%s/resumes/v4/resumes' % (self.endPoints['environments']['production']['cmw_url'])
            payload = '{"external_id":"'+str(external_id)+'","position":'+str(position)+',"duration":'+str(duration)+',"resume_type":"fod","platform":"browser","product":"sling"}'
            requests.put(url, headers=HEADERS, data=payload, auth=self.user.getAuth(), verify=VERIFY)


    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0, contextMenu=None, properties=None):
        try:
            name = name.encode("utf-8")
        except:
            pass
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        if mode == 21: liz.setProperty("IsPlayable","false")
        else: liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else:
            if 'mediatype' in infoList: self.contentType = '%ss'%(infoList['mediatype'])
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        if contextMenu is not None: liz.addContextMenuItems(contextMenu)
        if properties is not None:
            for key, value in properties.iteritems():
                liz.setProperty(key, value)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: 
            if 'mediatype' in infoList: self.contentType = '%ss'%(infoList['mediatype'])
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)

    
    def getLineup(self, days=1):
        return []
    
    
    def uEPG(self):
        log('uEPG')
        #support for uEPG universal epg framework module available from the Kodi repository. https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        channels = self.getChannels()
        lineups  = self.getLineup()
        return poolList(self.buildGuide, [(idx + 1, channel, lineups) for idx, channel in enumerate(channels)])
        
        
    def buildGuide(self, data):
        chnum, channel, listings = data
        meta       = channel['metadata']
        chname     = (meta.get('channel_name','') or meta.get('title','') or meta.get('call_sign',''))
        link       = channel['qvt_url']
        chlogo     = (meta.get('thumbnail_cropped',{}).get('url','') or ICON)
        newChannel = {}
        guidedata  = []
        newChannel['channelname']   = chname
        newChannel['channelnumber'] = chnum
        newChannel['channellogo']   = chlogo
        newChannel['isfavorite']    = random.choice([True, False])
        #dummy info for testing
        starttime  = time.time()
        for listing in range(24):
            label  = chname
            thumb  = (channel.get('thumbnail',{}).get('url','') or chlogo or ICON)
            fanart = (meta.get('default_schedule_image',{}).get('url','') or FANART)
            plot   = 'Plot Placeholder'
            genre  = meta.get('genre','')
            dur    = random.choice([1800,3600,7200])
            starttime = starttime + dur
            tmpdata = {"mediatype":"episode","label":label ,"title":label,"plot":plot,"duration":dur,"genre":genre}
            tmpdata['url'] = self.sysARG[0]+'?mode=play&name=%s&url=%s'%(label,link)
            tmpdata['starttime'] = starttime
            tmpdata['art'] = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
            guidedata.append(tmpdata)
        newChannel['guidedata'] = guidedata
        return newChannel        
    
    
    def getParams(self):
        return dict(urlparse.parse_qsl(self.sysARG[2][1:]))

        
    def run(self):
        global LOGIN_URL, USER_SUBS
        cache  = True
        update = False
        params = self.getParams()

        LOGIN_URL = self.endPoints['environments']['production_noplay']['micro_ums_url'] + '/sling-api/oauth/authenticate-user'
        loggedIn, message = self.user.logIn(LOGIN_URL, USER_EMAIL, USER_PASSWORD)
        log("Sling Class is logIn() ==> Success: " + str(loggedIn) + " | Message: " + message)
        if loggedIn:
            log("self.user Subscriptions URL => " + USER_INFO_URL)
            gotSubs, message = self.user.getUserSubscriptions(USER_INFO_URL)
            if gotSubs:
                USER_SUBS = message
            log("self.user Subscription Attempt, Success => " + str(gotSubs) + "Message => " + message)
        else:
            sys.exit()

        try: url=urllib.unquote(params["url"])
        except: url=None
        try: name=urllib.unquote_plus(params["name"])
        except: name=None
        try:  
            mode=params["mode"]
            if mode.isdigit(): mode=int(mode)
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode is None:  self.buildMenu()
        elif mode == 'live': self.buildLive('live')
        elif mode == 'vod': self.buildLive('vod')
        elif mode == 'my_tv': self.buildMyTV(name)
        elif mode == 'my_tv_item': self.buildMyTV(name, loadJSON(url))
        elif mode == 'search': self.search()
        elif mode == 'search_result': self.search(url)
        elif mode == 'tv_show': self.buildShow(name, url)
        elif mode == 'play': self.playVideo(name, url)
        elif mode == 'no_play': sys.exit()
        elif mode == 'on_demand': self.buildOnDemand(url)
        elif mode == 'on_now' or mode == 'sports': self.buildOnNow(mode)
        elif mode == 'on_now_item': 
            self.buildOnNowItems(name, url)
            cache = False
        elif mode == 'logout': self.user.logOut()
        elif mode == 'settings': 
            REAL_SETTINGS.openSettings(), self.buildMenu()
            update = True
        elif mode == 'guide': 
            cache = False
            xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&skin_path=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(self.uEPG()))),urllib.quote(json.dumps(ADDON_PATH)),urllib.quote(json.dumps(sys.argv[0]+"?mode=20")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("5"))))

        xbmcplugin.setContent(int(self.sysARG[1])    , self.contentType)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), updateListing=update, cacheToDisc=cache)
