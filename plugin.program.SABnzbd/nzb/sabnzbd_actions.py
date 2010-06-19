import urllib
import re
import xbmc
import xbmcgui
import xbmcplugin
import sys
import simplejson
from misc import _get_path
from settings import category_list

__settings__ = sys.modules[ "__main__" ].__settings__

class SABnzbdActions:
    def __init__(self, title=None):
        # Grab the settings
        host = __settings__.getSetting( "sab_host" )
        port = __settings__.getSetting( "sab_port" )
        username = __settings__.getSetting( "sab_user" )
        password = __settings__.getSetting( "sab_pass" )
        apikey = __settings__.getSetting( "sab_key" )
        self.category_prompt = __settings__.getSetting( "cat_prompt" ) == "true"
         
        self.RE_NEWZBIN_URL = re.compile(r'/browse/post/(\d+)')
        
        self.sabnzbd_url = 'http://%s:%s@%s:%s/sabnzbd/ACTION_HERE' % (username,password,host, port)
        if username and password:
            print 'sabnzbd-xbmc: user/pass found'
            login_details = '&ma_username=%s&ma_password=%s' % (username, password)
            self.sabnzbd_url += login_details
        if apikey:
            print "sabnzbd-xbmc: using api key"
            key = '&apikey=%s' % (apikey)
            self.sabnzbd_url += key
             
    def _download_nzb(self, url, title='', category='default'):
        try:
            #offer an option for download or stream (not implemented)
            #dl_type = xbmcgui.Dialog().select('Select a download type', ['Download', 'Stream'])
            dl_type = 0
            if dl_type == 1:
                category = 'streaming'
            if category == 'default' and self.category_prompt:
                i = xbmcgui.Dialog().select('Select a download type', category_list)
                category = category_list[i]
            url = url.strip()
            
            # decide whether to add it as a url, or a newzbin messageid
            newzbin_url = self.RE_NEWZBIN_URL.search(urllib.unquote(url).lower())
            if url and (url.isdigit() or len(url)==5):
                type = 'addid'
                value = url
            elif newzbin_url:
                type = 'addid'
                value = newzbin_url.group(1)
            else:
                type = 'addurl'
                value = url

            # Prepare the needed url
            action = 'api?mode=%s&name=%s&pp=-1&cat=%s' % (type, value, category)
            sab_url = self.sabnzbd_url.replace('ACTION_HERE', action)
            print 'sab debug: %s' % sab_url
            
            resp = self._connection(sab_url)
            if resp.startswith('ok'):
                msg = 'Added %s to the queue.' % title
                thumbnail = _get_path('default.tbn')
                ex = 'XBMC.Notification(Added to queue,%s,image=%s)' % (msg, thumbnail)
                xbmc.executebuiltin(ex)
            elif 'error: API Key Required' in resp:
                self.dialog('Please enter the API key from SABnzbd into the plugin settings')
            elif 'error: API Key Incorrect' in resp:
                self.dialog('The API key in the plugin settings is incorrect, please change')
            else:
                self.dialog('Failed adding %s.\n Please check the settings of this script and sabnzbd.' % title)
                print "sabnzbd-xbmc: Error accessing sabnzbd: %s" % resp


        except:
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )

    def dialog(self, msg):
        xbmcgui.Dialog().ok('SABnzbd', msg)
        
    def _sabnzbd_action(self, nzo_id):
        ''' Queue actions such as delete, pause and move to top '''
        dl_type = xbmcgui.Dialog().select('Select an action', ['Delete', 'Move to top','Pause','Resume','Pause All','Resume All','Pause for 10 minutes','Pause for 30 minutes','Pause for 60 minutes','Pause for 5 hours',])
        print 'dl_type:%s' % dl_type
        if dl_type == 0:
            action = 'queue/delete?uid=%s' % (nzo_id)
            actmsg = 'Item Deleted'
        elif dl_type == 1:
            action = 'queue/switch?uid1=%s&uid2=%s' % (nzo_id, '0')
            actmsg = 'Moved To Top'
        elif dl_type == 2:
            action = 'api?mode=queue&name=pause&value=%s' % (nzo_id)
            actmsg = 'Item Paused'
        elif dl_type == 3:
            action = 'api?mode=queue&name=resume&value=%s' % (nzo_id)
            actmsg = 'Item Resumed'
        elif dl_type == 4:
            action = 'api?mode=pause'
            actmsg = 'All Items Paused'
        elif dl_type == 5:
            action = 'api?mode=resume'
            actmsg = 'All Items Resumed'
        elif dl_type == 6:
            action = 'api?mode=config&name=set_pause&value=10'
            actmsg = 'Paused all for 10 minutes'
        elif dl_type == 5:
            action = 'api?mode=config&name=set_pause&value=30'
            actmsg = 'Paused all for 30 minutes'
        elif dl_type == 5:
            action = 'api?mode=config&name=set_pause&value=60'
            actmsg = 'Paused all for 60 minutes'
        elif dl_type == 5:
            action = 'api?mode=config&name=set_pause&value=300'
            actmsg = 'Pause all for 5 hours'
        else: action = ''

        sab_url = self.sabnzbd_url.replace('ACTION_HERE', action)
        print 'sab debug url: %s' % sab_url
        resp = self._connection(sab_url, read=False)
        comMsg = 'Item Moved To Top'
        thumbnail2 = _get_path('default.tbn')
        ex2 = 'XBMC.Notification(Action Completed,%s,image=%s)' % (actmsg, thumbnail2)
        xbmc.executebuiltin(ex2)
        print 'action completed'
        xbmc.executebuiltin('Container.Refresh')

    def _sabnzbd_queue(self):
        ''' Load sabnzbd's queue using the API and return it as a dictionary '''
        try:
            dict = { "status": "fail", 'folder':'false'}
            sab_url = self.sabnzbd_url.replace('ACTION_HERE', 'api?mode=qstatus&output=json')
            print 'sab_url: %s' % sab_url
            
            resp = self._connection(sab_url)
            print 'resp:%s' % resp
            if not resp:
                msg = 'Failed to load the SABnzbd queue - Check your settings'
                xbmcgui.Dialog().ok('SABnzbd', msg)
                print 'failed to load sabnzbd queue'
                return {}
            elif '<html>' in resp:
                msg = 'Please add your sabnzbd user/pass in the settings.'
                xbmcgui.Dialog().ok('SABnzbd', msg)
                return {}
            elif 'error: API Key Required' in resp:
                self.dialog('Please enter the API key from SABnzbd into the plugin settings')
            elif 'error: API Key Incorrect' in resp:
                self.dialog('The API key in the plugin settings is incorrect, please change')
            else:
                #proccess the json from sabnzbd into a dictionary
                json = simplejson.loads(resp)

                #extract some info from the json that sabnzbd outputs
                items = []
                for job in json['jobs']:
                    extra = ''
                    item = {}
                    mb = float(job['mb'])
                    mbleft = float(job['mbleft'])
                    if mbleft or mb:
                        perc = (1.0 - mbleft/mb) * 100.00
                    else:
                        perc = 0
                    extra = ' (%d%%)' % perc
                    item['name'] = job['filename'] + extra
                    item['url'] = ''
                    item['id'] = job['id']
                    item['type'] = 'sab_item'
                    items.append(item)

                if not items:
                    item = {}
                    item['name'] = 'The queue is empty'
                    item['url'] = ''
                    item['type'] = 'sab_item'
                    item['id'] = 'empty'
                    items.append(item)

                dict[ "items" ] = {"assets": items, 'folder':False }
                dict[ "status" ] = "ok"
                
                return dict
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return {}
        
    def _connection(self, sab_url, read=True):
        ''' General wrapper for sending actions or retrieving a response from the SABnzbd api  '''
        try:
            print 'url:%s' % sab_url
            print 'read:%s' % read
            req = urllib.urlopen(sab_url)
            # return the server responce if requested
            if read:
                print 'getting response'
                resp = req.read()
                req.close()
                return resp
            else:
                req.close()
                return True
        except:
            print 'sab connection failed'
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            if read:
                return 'failed'
            else:
                return False
