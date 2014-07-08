# -*- coding: utf-8 -*-
"""
    CrunchyRoll;xbmc
    Copyright (C) 2012 - 2014 Matthew Beacher
    This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""
import sys
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcgui
import xbmcplugin
import time
import shelve
import random, re, string
import json
import gzip
import StringIO
import dateutil.tz, dateutil.relativedelta, dateutil.parser 
import crunchy_main
__settings__ = sys.modules[ "__main__" ].__settings__
lineupRegion = __settings__.getSetting("lineupRegion")
__version__ = sys.modules[ "__main__" ].__version__
__XBMCBUILD__ = xbmc.getInfoLabel( "System.BuildVersion" ) +" "+ sys.platform



class _Info:
	
	def __init__( self, *args, **kwargs ):
		self.__dict__.update( kwargs )

class CrunchyJSON:

        def __init__(self, checkMode = True):
                self.loadShelf()

        def loadShelf(self):
                try:
                        self.base_path = xbmc.translatePath(__settings__.getAddonInfo('profile')).decode('utf-8')
                        self.base_cache_path = os.path.join(self.base_path, "cache")
                        if not os.path.exists(self.base_cache_path):
                                os.makedirs(self.base_cache_path)
                        shelf_path = os.path.join(self.base_path, "cruchyXBMC")
                        #Load Persistan Vars
                        userData = shelve.open(shelf_path,writeback=True)
                        local_string = __settings__.getLocalizedString
                        notice_msg = local_string(30200).encode("utf8")
                        setup_msg = local_string(30203).encode("utf8")
                        change_language = __settings__.getSetting("change_language")
                        if change_language == "0":
                                userData.setdefault('API_LOCALE',"enUS")
                        elif change_language == "1":
                                userData['API_LOCALE']  = "enUS"
                        elif change_language == "2":
                                userData['API_LOCALE']  = "enGB"
                        elif change_language == "3":
                                userData['API_LOCALE']  = "jaJP"
                        elif change_language == "4":
                                userData['API_LOCALE']  = "frFR"
                        elif change_language == "5":
                                userData['API_LOCALE']  = "deDE"
                        elif change_language == "6":
                                userData['API_LOCALE']  = "ptBR"
                        elif change_language == "7":
                                userData['API_LOCALE']  = "ptPT"
                        elif change_language == "8":
                                userData['API_LOCALE']  = "esLA"
                        elif change_language == "9":
                                userData['API_LOCALE']  = "esES"
                        userData['username'] = __settings__.getSetting("crunchy_username")
                        userData['password'] = __settings__.getSetting("crunchy_password")
                        if not userData.has_key('device_id'):
                                char_set = string.ascii_letters + string.digits
                                device_id = ''.join(random.sample(char_set,32))
                                userData["device_id"] = device_id
                                print "Crunchyroll;xbmc ----> New device_id created. New device_id is: "+ str(device_id)
                        userData['API_URL'] = "https://api.crunchyroll.com"
                        userData['API_HEADERS'] = [('User-Agent',"Mozilla/5.0 (PLAYSTATION 3; 4.46)"), ('Host',"api.crunchyroll.com"), ('Accept-Encoding',"gzip, deflate"), ('Accept',"*/*"), ('Content-Type',"application/x-www-form-urlencoded")]
                        userData['API_VERSION'] = "1.0.1"
                        userData['API_ACCESS_TOKEN'] = "S7zg3vKx6tRZ0Sf"
                        userData['API_DEVICE_TYPE'] = "com.crunchyroll.ps3"
                        userData.setdefault('premium_type', 'UNKNOWN')
                        current_datetime = datetime.datetime.now(dateutil.tz.tzutc())
                        userData.setdefault('lastreported', (current_datetime - dateutil.relativedelta.relativedelta( hours = +24 )))
                        self.userData = userData
                except:
                        print "Unexpected error:", sys.exc_info()
                        userData['session_id'] = ''
                        userData['auth_expires'] = current_datetime - dateutil.relativedelta.relativedelta( hours = +24 )
                        userData['lastreported'] = current_datetime - dateutil.relativedelta.relativedelta( hours = +24 )
                        userData['premium_type'] = 'unknown'
                        userData['auth_token'] = ''
                        userData['session_expires'] = current_datetime - dateutil.relativedelta.relativedelta( hours = +24 )
                        self.userData = userData
                        userData.close()
                        print "Crunchyroll -> Unable to Load shelve"
                        return False

                if current_datetime > userData['lastreported']:
                        userData['lastreported'] = (current_datetime + dateutil.relativedelta.relativedelta( hours = +24 ))
                        self.userData = userData
                        self.usage_reporting() #Call for Usage Reporting

                #Check to see if a session_id doesn't exist or if the current auth token is invalid and if so start a new session and log it in.                   
                if (not userData.has_key('session_id')) or (not userData.has_key('auth_expires')) or current_datetime > userData['auth_expires']:
                        #Start new session
                        print "Crunchyroll;xbmc ----> Starting new session"
                        opener = urllib2.build_opener()
                        opener.addheaders = userData['API_HEADERS']
                        options = urllib.urlencode({'device_id':userData["device_id"], 'device_type':userData['API_DEVICE_TYPE'], 'access_token':userData['API_ACCESS_TOKEN'], 'version':userData['API_VERSION'], 'locale': userData['API_LOCALE']})
                        #print options
                        urllib2.install_opener(opener)
                        url = userData['API_URL']+"/start_session.0.json"
                        #print url
                        req = opener.open(url, options)
                        json_data = req.read()
                        if req.headers.get('content-encoding', None) == 'gzip':
				json_data = gzip.GzipFile(fileobj=StringIO.StringIO(json_data)).read().decode('utf-8','ignore')
			req.close()
			#print json_data
                        request = json.loads(json_data)  
                        #print request
                        if request['error'] is False:
                                userData['session_id'] = request['data']['session_id'] 
                                userData['session_expires'] = (current_datetime + dateutil.relativedelta.relativedelta( hours = +4 ))
                                userData['test_session'] = current_datetime 
                                print "Crunchyroll.bundle ----> New session created! Session ID is: "+ str(userData['session_id'])
                        elif request['error'] is True:
                                print "Crunchyroll.bundle ----> Error starting new session. Error message is: "+ str(request['message'])
                                return False
                        #Login the session we just started.
                        if not userData['username'] or not userData['password']:
                                print"Crunchyroll.bundle ----> No Username or Password set"
                                self.userData = userData
                                userData.close()
                                ex = 'XBMC.Notification("'+notice_msg+':","'+setup_msg+'.", 3000)'
                                xbmc.executebuiltin(ex)
                                print "crunchyroll-takeout -> NO CRUNCHYROLL ACCOUNT FOUND!"
                                return False
                        else: 
                                print"Crunchyroll.bundle ----> Logging in the new session we just created."
                                opener = urllib2.build_opener()
                                opener.addheaders = userData['API_HEADERS']
                                options = urllib.urlencode({'session_id':userData['session_id'], 'password':userData['password'], 'account':userData['username'], 'version':userData['API_VERSION'], 'locale': userData['API_LOCALE']})
                                url = userData['API_URL']+"/login.0.json"
                                req = opener.open(url, options)
                                json_data = req.read()
                                if req.headers.get('content-encoding', None) == 'gzip':
                                        json_data = gzip.GzipFile(fileobj=StringIO.StringIO(json_data)).read().decode('utf-8','ignore')
                                req.close()
                                request = json.loads(json_data) 
                                #print request
                                if request['error'] is False:
                                        userData['auth_token'] = request['data']['auth'] 
                                        userData['auth_expires'] = dateutil.parser.parse(request['data']['expires'])
                                        userData['premium_type'] = 'free' if request['data']['user']['premium'] == '' else request['data']['user']['premium']
                                        print"Crunchyroll.bundle ----> Login successful."
                                elif request['error'] is True:
                                        print"Crunchyroll.bundle ----> Error logging in new session. Error message was: "+ str(request['message'])
                                        self.userData = userData
                                        userData.close()
                                        return False
                        #Verify user is premium
                        if userData['premium_type'] in 'anime|drama|manga':
                                print"Crunchyroll.bundle ----> User is a premium "+str(userData['premium_type'])+" member."
                                self.userData = userData
                                userData.close()
                                return True
                        else:
                                print"Crunchyroll.bundle ----> User is not premium. "
                                self.userData = userData
                                userData.close()
                                return True

                #Check to see if a valid session and auth token exist and if so reinitialize a new session using the auth token. 
                elif userData.has_key("session_id") and userData.has_key("auth_expires") and current_datetime < userData['auth_expires'] and current_datetime > userData['session_expires']:

                        #Re-start new session
                        print "Crunchyroll.bundle ----> Valid auth token was detected. Restarting session."
                        opener = urllib2.build_opener()
                        options = urllib.urlencode({'device_id':userData["device_id"], 'device_type':userData['API_DEVICE_TYPE'], 'access_token':userData['API_ACCESS_TOKEN'], 'version':userData['API_VERSION'], 'locale': userData['API_LOCALE'], 'auth':userData['auth_token']})
                        urllib2.install_opener(opener)
                        url = userData['API_URL']+"/start_session.0.json"
                        #print url
                        req = opener.open(url, options)
                        json_data = req.read()
                        if req.headers.get('content-encoding', None) == 'gzip':
				json_data = gzip.GzipFile(fileobj=StringIO.StringIO(json_data)).read().decode('utf-8','ignore')
			req.close()
			#print json_data
                        request = json.loads(json_data)  
                        #print request
                        try:
                                if request['error'] is False:
                                        userData['session_id'] = request['data']['session_id'] 
                                        userData['auth_expires'] = dateutil.parser.parse(request['data']['expires']) 
                                        userData['premium_type'] = 'free' if request['data']['user']['premium'] == '' else request['data']['user']['premium']
                                        userData['auth_token'] = request['data']['auth'] 
                                        userData['session_expires'] = (current_datetime + dateutil.relativedelta.relativedelta( hours = +4 )) #4 hours is a guess. Might be +/- 4.
                                        userData['test_session'] = current_datetime 
                                        print"Crunchyroll.bundle ----> Session restart successful. New session_id is: "+ str(userData['session_id'])
                                                        
                                        #Verify user is premium
                                        if userData['premium_type'] in 'anime|drama|manga':
                                                print"Crunchyroll.bundle ----> User is a premium "+str(userData['premium_type'])+" member."
                                                self.userData = userData
                                                userData.close()
                                                return True
                                        else:
                                                print"Crunchyroll.bundle ----> User is not premium."
                                                self.userData = userData
                                                userData.close()
                                                return True

                                elif request['error'] is True:
                                        #Remove userData so we start a new session next time around. 
                                        del userData['session_id']
                                        del userData['auth_expires']
                                        del userData['premium_type']
                                        del userData['auth_token']
                                        del userData['session_expires']
                                        print"Crunchyroll.bundle ----> Error restarting session. Error message was: "+ str(request['message'])
                                        self.userData = userData
                                        userData.Save()
                                        return False
                        except:
                                userData['session_id'] = ''
                                userData['auth_expires'] = current_datetime - dateutil.relativedelta.relativedelta( hours = +24 )
                                userData['premium_type'] = 'unknown'
                                userData['auth_token'] = ''
                                userData['session_expires'] = current_datetime - dateutil.relativedelta.relativedelta( hours = +24 )
                                print"Crunchyroll.bundle ----> Error restarting session. Error message was: "+ str(request['message'])
                                self.userData = userData
                                userData.Save()
                                return False
                        

                #If we got to this point that means a session exists and it's still valid, we don't need to do anything.
                elif userData.has_key("session_id") and current_datetime < userData['session_expires']:
                    #This secion below is Stupid Slow
                        #return True
                        if userData['test_session'] is None or current_datetime > userData['test_session']:
                                userData['test_session'] = (current_datetime + dateutil.relativedelta.relativedelta( minutes = +10 )) #test once every 10 min 
                                #Test to make sure the session still works. (Sometimes sessions just stop working.) 
                                fields = "media.episode_number,media.name,media.description,media.media_type,media.series_name,media.available,media.available_time,media.free_available,media.free_available_time,media.duration,media.url,media.screenshot_image,image.fwide_url,image.fwidestar_url,series.landscape_image,image.full_url"
                                options = {'media_types':"anime|drama", 'fields':fields}
                                request = self.makeAPIRequest('queue', options)
                                if request['error'] is False:	
                                        print"Crunchyroll.bundle ----> A valid session was detected. Using existing session_id of: "+ str(userData['session_id'])
                                        #Verify user is premium
                                        if userData['premium_type'] in 'anime|drama|manga':
                                                print"Crunchyroll.bundle ----> User is a premium "+str(userData['premium_type'])+" member."
                                                self.userData = userData
                                                userData.close()
                                                return True
                                        else:
                                                print"Crunchyroll.bundle ----> User is not premium."
                                                self.userData = userData
                                                userData.close()
                                                return True					
                                elif request['error'] is True:
                                        print"Crunchyroll.bundle ----> Something in the login process went wrong."
                                        del userData['session_id']
                                        del userData['auth_expires']
                                        del userData['premium_type']
                                        del userData['auth_token']
                                        del userData['session_expires']
                                        self.userData = userData
                                        userData.close()	
                                        return False

                 
                
                #This is here as a catch all in case something gets messed up along the way. Remove userData variables so we start a new session next time around. 
                else:
                        del userData['session_id']
                        del userData['auth_expires']
                        del userData['premium_type']
                        del userData['auth_token']
                        del userData['session_expires']
                        print"Crunchyroll.bundle ----> Something in the login process went wrong."
                        self.userData = userData
                        userData.close()	
                        return False
                    
#-----------------------------------------------------------------------
        def list_series(self, title, media_type, filterx, offset): 
            fields = "series.name,series.description,series.series_id,series.rating,series.media_count,series.url,series.publisher_name,series.year,series.portrait_image,image.large_url,series.landscape_image,image.full_url"
            options = {'media_type':media_type.lower(), 'filter':filterx, 'fields':fields, 'limit':'64', 'offset':int(offset)}
            request = self.makeAPIRequest('list_series', options)
            if request['error'] is False:
                    counter = 0
                    for series in request['data']:
                            counter = counter + 1
                            year = 'None' if series['year'] is None else series['year'] #only available on some series
                            description = '' if series['description'] is None else series['description'].encode('utf-8') #Adding sinopses
                            thumb = '' if (series['portrait_image'] is None or series['portrait_image']['large_url'] is None or 'portrait_image' not in series or 'large_url' not in series['portrait_image']) else series['portrait_image']['full_url'] #Becuase not all series have a thumbnail. 
                            art = '' if (series['landscape_image'] is None or series['landscape_image']['full_url'] is None or 'landscape_image' not in series or 'full_url' not in series['landscape_image']) else series['landscape_image']['full_url'] #Becuase not all series have art. 
                            rating = '0' if (series['rating'] == '' or 'rating' not in series) else series['rating'] #Because Crunchyroll seems to like passing series without ratings
                            if ('media_count' in series and 'series_id' in series and 'name' in series and series['media_count'] > 0): #Because Crunchyroll seems to like passing series without these things
                                crunchy_main.UI().addItem({'Title':series['name'].encode("utf8"),'mode':'list_coll', 'series_id':series['series_id'], 'count':str(series['media_count']), 'Thumb':thumb, 'Fanart_Image':art, 'plot':description, 'year':year}, True) 
                    if counter >= 64:
                            offset = (int(offset) + counter)
                            crunchy_main.UI().addItem({'Title':'...load more','mode':'list_series','showtype':media_type,'filterx':filterx, 'offset':str(offset)})

            crunchy_main.UI().endofdirectory('none')

#-------------------------------------------------------------------------

        def list_categories(self, title, media_type, filterx): 
            options = {'media_type':media_type.lower()}
            request = self.makeAPIRequest('categories', options)
            #print request
            if request['error'] is False:
                    if filterx == 'genre':
                            if 'genre' in request['data']:
                                    for genre in request['data']['genre']:
                                            crunchy_main.UI().addItem({'Title':genre['label'].encode("utf8"),'mode':'list_series','showtype':media_type,'filterx':'tag:'+genre['tag']}, True)

                    if filterx == 'season':
                            if 'season' in request['data']:
                                    for season in request['data']['season']:
                                            crunchy_main.UI().addItem({'Title':season['label'].encode("utf8"),'mode':'list_series','showtype':media_type,'filterx':'tag:'+season['tag']}, True)
            crunchy_main.UI().endofdirectory('none')

 #--------------------------------------------------------------------------
            
        def list_collections(self, series_id, series_name, count, thumb, fanart):
                fields = "collection.collection_id,collection.season,collection.name,collection.description,collection.complete,collection.media_count"
                options = {'series_id':series_id, 'fields':fields, 'sort':'desc', 'limit':count}
                request = self.makeAPIRequest('list_collections', options)
                if request['error'] is False:
                        if len(request['data']) <= 1:
                                for collection in request['data']:
                                        complete = '1' if collection['complete'] else '0'
                                        return self.list_media(collection['collection_id'], series_name, count, complete, '1', fanart)
                        else:
                                for collection in request['data']:
                                        complete = '1' if collection['complete'] else '0'
                                        crunchy_main.UI().addItem({'Title':collection['name'].encode("utf8"),'filterx':series_name.encode("utf8"),'mode':'list_media','count':str(count),'id':collection['collection_id'],'plot':collection['description'].encode("utf8"),'complete':complete,'season':str(collection['season']) , 'series_id':series_id,'Thumb':thumb, 'Fanart_Image':fanart}, True)
                crunchy_main.UI().endofdirectory('none')		

####################################################################################################
        def list_media(self, collection_id, series_name, count, complete, season, fanart):
                #print art
                sort = 'asc' if complete is '1' else 'desc'
                fields = "media.episode_number,media.name,media.description,media.media_type,media.series_name,media.available,media.available_time,media.free_available,media.free_available_time,media.playhead,media.duration,media.url,media.screenshot_image,image.fwide_url,image.fwidestar_url,series.landscape_image,image.full_url"
                options = {'collection_id':collection_id, 'fields':fields, 'sort':sort, 'limit':'256'}
                request = self.makeAPIRequest('list_media', options)
                if request['error'] is False:	
                        return self.list_media_items(request['data'], series_name, season, 'normal', fanart)
            
####################################################################################################
        def list_media_items(self, request, series_name, season, mode, fanart):
                #print request
                for media in request:
                        
                        #print media
                        #print art
                        #The following are items to help display Recently Watched and Queue items correctly
                        season = media['collection']['season'] if mode == "history" else season 
                        series_name = media['series']['name'] if mode == "history" else series_name
                        series_name = media['most_likely_media']['series_name'] if mode == "queue" else series_name
                        fanart = media['series']['landscape_image']['fwide_url'] if (mode == "history" or mode == "queue") else fanart  #On history/queue, the fanart is get directly from the json.
                        media = media['media'] if mode == "history" else media  #History media is one level deeper in the json string than normal media items. 
                        if mode == "queue" and 'most_likely_media' not in media: #Some queue items don't have most_likely_media so we have to skip them.
                                continue 
                        media = media['most_likely_media'] if mode == "queue" else media  #Queue media is one level deeper in the json string than normal media items.
                        
                        #Dates, times, and such
                        current_datetime = datetime.datetime.now(dateutil.tz.tzutc()) 
                        available_datetime = dateutil.parser.parse(media['available_time']).astimezone(dateutil.tz.tzlocal())
                        available_date = available_datetime.date() 
                        available_delta = available_datetime - current_datetime
                        available_in = str(available_delta.days)+" days." if available_delta.days > 0 else str(available_delta.seconds/60/60)+" hours."
                        
                        #Fix Crunchyroll inconsistencies & add details for upcoming or unreleased episodes
                        media['episode_number'] = '0' if media['episode_number'] == '' else media['episode_number'] #PV episodes have no episode number so we set it to 0. 
                        media['episode_number'] = re.sub('\D', '', media['episode_number'])	#Because CR puts letters into some rare episode numbers.
                        if media['episode_number'] == '0':
                                name = "NO NAME" if media['name'] == '' else media['name']
                        else:
                                name = "Episode "+str(media['episode_number']) if media['name'] == '' else "Episode "+media['episode_number']+" - "+media['name'] #CR doesn't seem to include episode names for all media so we have to make one up.
                        name = series_name + " " + name if (mode == "history" or mode == "queue") else name
                        name = "* " + name if media['free_available'] is False else name
                        soon = "Coming Soon - " + series_name + " Episode "+str(media['episode_number']) if mode == "queue" else "Coming Soon - Episode "+str(media['episode_number'])
                        name = soon if media['available'] is False else name #Set the name for upcoming episode
                        #season = '1' if season == '0' else season #There is a bug which prevents Season 0 from displaying correctly in PMC. This is to help fix that. Will break if a series has both season 0 and 1. 
                        thumb = "http://static.ak.crunchyroll.com/i/no_image_beta_full.jpg" if media['screenshot_image'] is None else media['screenshot_image']['fwide_url'] if media['free_available'] is True else media['screenshot_image']['fwidestar_url']#because not all shows have thumbnails.
                        thumb = "http://static.ak.crunchyroll.com/i/coming_soon_beta_fwide.jpg" if media['available'] is False else thumb #Sets the thumbnail to coming soon if the episode isn't available yet.
                        description = '' if media['description'] is None else media['description'].encode('utf-8') #Adding sinopses
                        description = "This episode will be available in "+str(available_in) if media['available'] is False else description #Set the description for upcoming episodes.
                        duration = "0" if media['available'] is False else str(media['duration'])
                        playhead = "0" if media['available'] is False else str(media['playhead']) #current playback point
                        year = 'None' if media['available_time'] is None else media['available_time'][:10] #Adding published date instead
                        url = media['url']
                        media_id = url.split('-')[-1]
                        crunchy_main.UI().addItem({'Title':name.encode("utf8"),'mode':'videoplay', 'id':media_id.encode("utf8"), 'Thumb':thumb.encode("utf8"), 'url':url.encode("utf8"), 'Fanart_Image':fanart, 'plot':description, 'year':year, 'playhead':playhead, 'duration':duration}, False)
                crunchy_main.UI().endofdirectory('none')


#---------------------------------------------------------

        def History(self):
                fields = "media.episode_number,media.name,media.description,media.media_type,media.series_name,media.available,media.available_time,media.free_available,media.free_available_time,media.duration,media.playhead,media.url,media.screenshot_image,image.fwide_url,image.fwidestar_url"
                options = {'media_types':"anime|drama", 'fields':fields, 'limit':'256'}
                request = self.makeAPIRequest('recently_watched', options)
                if request['error'] is False:	
                        return self.list_media_items(request['data'], 'Recently Watched', '1', 'history', 'fanart')

#----------------------------------------------------------------

        def Queue(self):
            queue_type = __settings__.getSetting("queue_type")
            if queue_type == '0':
                    fields = "media.episode_number,media.name,media.description,media.media_type,media.series_name,media.available,media.available_time,media.free_available,media.free_available_time,media.duration,media.playhead,media.url,media.screenshot_image,image.fwide_url,image.fwidestar_url,series.landscape_image,image.full_url"
                    options = {'media_types':"anime|drama", 'fields':fields}
                    request = self.makeAPIRequest('queue', options)
                    if request['error'] is False:	
                            return self.list_media_items(request['data'], 'Queue', '1', 'queue', 'fanart')				

            elif queue_type == '1':
                    fields = "series.name,series.description,series.series_id,series.rating,series.media_count,series.url,series.publisher_name,series.year,series.portrait_image,image.large_url,series.landscape_image,image.full_url"
                    options = {'media_types':"anime|drama", 'fields':fields}
                    request = self.makeAPIRequest('queue', options)
                    if request['error'] is False:
                            for series in request['data']:
                                    series = series['series']
                                    year = 'None' if series['year'] is None else series['year'] #only available on some series
                                    description = '' if series['description'] is None else series['description'].encode('utf-8') #Adding sinopses
                                    
                                    thumb = '' if (series['portrait_image'] is None or series['portrait_image']['large_url'] is None or 'portrait_image' not in series or 'large_url' not in series['portrait_image']) else series['portrait_image']['full_url'] #Becuase not all series have a thumbnail. 
                                    art = '' if (series['landscape_image'] is None or series['landscape_image']['full_url'] is None or 'landscape_image' not in series or 'full_url' not in series['landscape_image']) else series['landscape_image']['full_url'] #Becuase not all series have art. 
                                    #print art
                                    rating = '0' if (series['rating'] == '' or 'rating' not in series) else series['rating'] #Because Crunchyroll seems to like passing series without ratings
                                    if ('media_count' in series and 'series_id' in series and 'name' in series and series['media_count'] > 0): #Because Crunchyroll seems to like passing series without these things
                                            crunchy_main.UI().addItem({'Title':series['name'].encode("utf8"),'mode':'list_coll', 'series_id':series['series_id'], 'Thumb':thumb, 'Fanart_Image':art, 'plot':description, 'year':year}, True)
                            
                            crunchy_main.UI().endofdirectory('none')
                        
 #-------------------------------------------------------------------------                       

        def startPlayback(self, Title, url, media_id, playhead, duration, Thumb):

                #Split the URL to get the session_id & quality
                session_id = self.userData['session_id']
                res_quality = ['low','mid','high','ultra']
                quality = res_quality[int(__settings__.getSetting("video_quality"))]
                if __settings__.getSetting("playback_resume") == 'true':
                        playback_resume = True
                else:
                        playback_resume = False
                if playback_resume is not True:
                        resumetime = "0"
                else:
                        resumetime = playhead
                totaltime = duration
                local_string = __settings__.getLocalizedString
                notice_msg = local_string(30200).encode("utf8")
                setup_msg = local_string(30212).encode("utf8")
                #Make the API call 
                fields = "media.episode_number,media.name,media.description,media.url,media.stream_data"
                values = {'session_id':self.userData['session_id'], 'version':self.userData['API_VERSION'], 'locale':self.userData['API_LOCALE'], 'media_id':media_id, 'fields':fields}
                opener = urllib2.build_opener()
                opener.addheaders = self.userData['API_HEADERS']
                options = urllib.urlencode(values)
                urllib2.install_opener(opener)
                url = self.userData['API_URL']+"/info.0.json"
                req = opener.open(url, options)
                json_data = req.read()
                if req.headers.get('content-encoding', None) == 'gzip':
                    json_data = gzip.GzipFile(fileobj=StringIO.StringIO(json_data)).read().decode('utf-8','ignore')
                req.close()
                request = json.loads(json_data)
                #print request
                if int(resumetime) > 0:
                        playcount=0
                else:
                        playcount=1                      
                item = xbmcgui.ListItem(Title)
                item.setInfo( type="Video", infoLabels={ "Title": Title, "playcount":playcount})
                item.setThumbnailImage(Thumb)
                item.setProperty('TotalTime', totaltime)
                item.setProperty('ResumeTime', resumetime)                        
                count=0
                allurl = {}
                playlist = xbmc.PlayList(1)
                playlist.clear()
                if request['error'] is False:	
                        if request['data']['stream_data'] is not None:
                                for stream in request['data']['stream_data']['streams']:
                                        allurl[stream['quality']] = stream['url']
                                if allurl[quality] is not None:
                                        url = allurl[quality]
                                elif quality == 'ultra' and allurl['high'] is not None:
                                        url = allurl['high']
                                elif allurl['mid'] is not None:
                                        url = allurl['mid']
                                else:
                                        url = allurl['low']
                                playlist.add(url, item)
                                xbmc.Player().play(playlist)
                                timeplayed = 1 + int(resumetime)
                                temptimeplayed = timeplayed
                                time.sleep(1)
                                if playback_resume is True:
                                        xbmc.Player().seekTime(float(resumetime))
                                x = 0
                                try:
                                        while player.isPlaying:
                                                temptimeplayed = xbmc.Player().getTime()
                                                timeplayed = temptimeplayed
                                                if x ==30:
                                                        x = 0
                                                        strTimePlayed = str(int(round(timeplayed)))
                                                        values = {'session_id':session_id, 'event':'playback_status', 'locale':self.userData['API_LOCALE'], 'media_id':media_id, 'version':'221', 'playhead':strTimePlayed}
                                                        request = self.makeAPIRequest('log', values)
                                                        #print request
                                                else:
                                                        x = x + 1
                                                time.sleep(1)
                                except:
                                        print "XBMC stopped playing"
                                strTimePlayed = str(int(round(timeplayed)))
                                values = {'session_id':session_id, 'event':'playback_status', 'locale':self.userData['API_LOCALE'], 'media_id':media_id, 'version':'221', 'playhead':strTimePlayed}
                                request = self.makeAPIRequest('log', values)
                                #print request


        def makeAPIRequest(self, method, options):
                print "Crunchyroll.bundle ----> get JSON"
                values = {'session_id':self.userData['session_id'], 'version':self.userData['API_VERSION'], 'locale':self.userData['API_LOCALE']} 
                values.update(options)	
                opener = urllib2.build_opener()
                opener.addheaders = self.userData['API_HEADERS']
                options = urllib.urlencode(values)
                #print options
                urllib2.install_opener(opener)
                url = self.userData['API_URL']+"/"+method+".0.json"
                #print url
                req = opener.open(url, options)
                json_data = req.read()
                if req.headers.get('content-encoding', None) == 'gzip':
                    json_data = gzip.GzipFile(fileobj=StringIO.StringIO(json_data)).read().decode('utf-8','ignore')
                req.close()
                #print json_data
                return json.loads(json_data)
         
###############################################################################​#####################


        def changeLocale(self):
                import cookielib
                cj = cookielib.LWPCookieJar()
                local_string = __settings__.getLocalizedString
                notice = local_string(30200).encode("utf8")
                notice_msg = local_string(30211).encode("utf8")
                notice_err = local_string(30206).encode("utf8")
                notice_done = local_string(30310).encode("utf8")
                icon = xbmc.translatePath( __settings__.getAddonInfo('icon'))
                if (self.userData['username'] != '' and self.userData['password'] != ''):
                    print "Crunchyroll.language: --> Attempting to log-in with your user account..."
                    xbmc.executebuiltin('Notification('+notice+','+notice_msg+',5000,'+icon+')')
                    url = 'https://www.crunchyroll.com/?a=formhandler'
                    data = urllib.urlencode({'formname':'RpcApiUser_Login', 'next_url':'','fail_url':'/login','name':self.userData['username'],'password':self.userData['password']})
                    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                    opener.addheaders = [('Referer', 'https://www.crunchyroll.com'),('User-Agent','Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0')]
                    # print "Crunchyroll.language: --> Saving new Cookie."
                    urllib2.install_opener(opener)
                    req = opener.open(url, data)
                    req.close()
                else:                    
                    xbmc.executebuiltin('Notification('+notice+','+notice_err+',5000,'+icon+')')
                    print "Crunchyroll.language: --> NO CRUNCHYROLL ACCOUNT FOUND!"
                # print "Crunchyroll.language: --> logged in"
                url = 'https://www.crunchyroll.com/?a=formhandler'
                data = urllib.urlencode({'next_url':'','language':self.userData['API_LOCALE'],'formname':'RpcApiUser_UpdateDefaultSoftSubLanguage'})
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                opener.addheaders = [('Referer', 'https://www.crunchyroll.com/acct/?action=video'),('User-Agent','Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0')]
                self.opener = opener
                urllib2.install_opener(opener)
                #Entering in the video settings page first (don't work if I don't do it)
                req = self.opener.open("https://www.crunchyroll.com/acct/?action=video")
                #Now do the actual language change.
                req = self.opener.open(url, data)
                req.close()
                print 'Crunchyroll.language: --> Now using '+self.userData['API_LOCALE']
                xbmc.executebuiltin('Notification('+notice+','+notice_done+',5000,'+icon+')')
                print "Crunchyroll.language: --> Disabling the force change language setting."
                __settings__.setSetting(id="change_language", value="0")

        def usage_reporting(self):
                import cookielib
                cj = cookielib.LWPCookieJar()
                print "Crunchyroll.usage: --> Attempting to report usage"
                url = 'https://docs.google.com/forms/d/1_qB4UznRfx69JrGCYmKbbeQcFc_t2-9fuNvXGGvl8mk/formResponse'
                
                #print 'entry_1580743010' + self.userData['device_id'] + 'entry_623948459' + self.userData['premium_type'] + 'entry_1130326797' + __version__ + 'entry.590894822' + str(__XBMCBUILD__)
                data = urllib.urlencode({'entry_1580743010':self.userData['device_id'],'entry_623948459':self.userData['premium_type'],'entry_1130326797':__version__,'entry.590894822':__XBMCBUILD__})
                opener = urllib2.build_opener()
                opener.addheaders = [('User-Agent','Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0')]
                urllib2.install_opener(opener)
                req = opener.open(url, data)
                req.close()
                
        
