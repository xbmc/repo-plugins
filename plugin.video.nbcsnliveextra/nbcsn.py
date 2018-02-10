from resources.globals import *
from resources.adobepass import ADOBE

#Add-on specific Adobepass variables
SERVICE_VARS = {'requestor_id':'nbcsports',
                'public_key':'nTWqX10Zj8H0q34OHAmCvbRABjpBk06w',
                'private_key':'Q0CAFe5TSCeEU86t',
                'activate_url':'activate.nbcsports.com'
               }

def categories():
    req = urllib2.Request(ROOT_URL+'apps/NBCSports/configuration-ios.json')
    req.add_header("User-Agent", UA_NBCSN)
    response = urllib2.urlopen(req)
    json_source = json.load(response)
    response.close()

    olympic_icon = os.path.join(ROOTDIR, "olympic_icon.png")
    olympic_fanart = 'http://www.nbcolympics.com/sites/default/files/field_no_results_image/06April2016/bg-img-pye-951x536.jpg'
    addDir('Olympics', ROOT_URL+'apps/NBCSports/configuration-ios.json', 3, olympic_icon, olympic_fanart)

    for item in json_source['brands'][0]['sub-nav']:
        display_name = item['display-name']
        url = item['feed-url']
        url = url.replace('/ios','/firetv')

        addDir(display_name,url,4,ICON,FANART)


def olympics(url):
    req = urllib2.Request(url)
    req.add_header("User-Agent", UA_NBCSN)
    response = urllib2.urlopen(req)
    json_source = json.load(response)
    response.close()
    olympic_icon = os.path.join(ROOTDIR,"olympic_icon.png")
    olympic_fanart = 'http://www.nbcolympics.com/sites/default/files/field_no_results_image/06April2016/bg-img-pye-951x536.jpg'

    for item in json_source['sections'][0]['sub-nav']:
        display_name = item['display-name']
        url = item['feed-url']
        url = url.replace('/ios','/firetv')

        addDir(display_name, url, 4, olympic_icon, olympic_fanart)


def scrapeVideos(url,scrape_type=None):
    req = urllib2.Request(url)
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_NBCSN)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')


    response = urllib2.urlopen(req)
    json_source = json.load(response)
    response.close()

    if 'featured' in url:
        json_source = json_source['showCase']

    if 'live-upcoming' not in url:
        json_source = sorted(json_source, key=lambda k: k['start'], reverse = True)
    else:
        json_source = sorted(json_source, key=lambda k: k['start'], reverse = False)


    for item in json_source:
      if 'show-all' in filter_list or item['sport'] in filter_list:
        buildVideoLink(item)



def buildVideoLink(item):
    url = ''
    #Use the ottStreamUrl (v3) until sound is fixed for newer (v4) streams in kodi
    try:
        #url = item['iosStreamUrl']
        url = item['ottStreamUrl']
        if url == '' and item['iosStreamUrl'] != '':
            url = item['iosStreamUrl']
        '''
        if CDN == 1 and item['backupUrl'] != '':
            url = item['backupUrl']
        '''
    except:
        try:
            if item['videoSources']:
                '''
                if 'iosStreamUrl' in item['videoSources'][0]:
                    url =  item['videoSources'][0]['iosStreamUrl']
                    if CDN == 1 and item['videoSources'][0]['backupUrl'] != '':
                        url = item['backupUrl']
                '''
                if 'ottStreamUrl' in item['videoSources'][0]:
                    url =  item['videoSources'][0]['ottStreamUrl']

                    if url == '' and item['iosStreamUrl'] != '':
                        url = item['iosStreamUrl']
                    '''
                    if CDN == 1 and item['videoSources'][0]['backupUrl'] != '':
                        url = item['backupUrl']
                    '''
        except:
            pass
        pass

    menu_name = item['title']
    name = menu_name
    desc = item['info']
    free = int(item['free'])    

    # Highlight active streams
    start_time = item['start']
    pattern = "%Y%m%d-%H%M"

    aired = start_time[0:4]+'-'+start_time[4:6]+'-'+start_time[6:8]
    genre = item['sportName']


    length = 0
    try:
        length = int(item['length'])
    except:
        pass


    info = {'plot':desc,'tvshowtitle':'NBCSN','title':name,'originaltitle':name,'duration':length,'aired':aired,'genre':genre}

    imgurl = "http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/"+item['image']+"_m50.jpg"
    menu_name = filter(lambda x: x in string.printable, menu_name)

    start_date = stringToDate(start_time, "%Y%m%d-%H%M")
    start_date = datetime.strftime(utc_to_local(start_date),xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))
    info['plot'] = 'Starting at: '+start_date+'\n\n'+info['plot']

    if url != '':
        if free:
            menu_name = '[COLOR='+FREE+']'+menu_name + '[/COLOR]'
            #addLink(menu_name,url,name,imgurl,FANART,info)
            if str(PLAY_MAIN) == 'true':
                addFreeLink(menu_name,url,imgurl,FANART,None,info)
            else:
                addDir(menu_name,url,6,imgurl,FANART,None,True,info)
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR='+LIVE+']'+menu_name + '[/COLOR]'
            if str(PLAY_MAIN) == 'true':
                addPremiumLink(menu_name,url,imgurl,FANART,None,info)
            else:
                addDir(menu_name,url,5,imgurl,FANART,None,True,info)

    else:
        #elif my_time < event_start:
        if free:
            menu_name = '[COLOR='+FREE_UPCOMING+']'+menu_name + '[/COLOR]'
            if str(PLAY_MAIN) == 'true':
                addPremiumLink(menu_name,url,imgurl,FANART,None,info)
            else:
                addDir(menu_name + ' ' + start_date,'/disabled',999,imgurl,FANART,None,False,info)

        elif FREE_ONLY == 'false':
            menu_name = '[COLOR='+UPCOMING+']'+menu_name + '[/COLOR]'
            addDir(menu_name + ' ' + start_date,'/disabled',999,imgurl,FANART,None,False,info)




def signStream(stream_url, stream_name, stream_icon):
    adobe = ADOBE(SERVICE_VARS)
    #1. Authorize device
    #2. Get media token
    #3. Sign stream (TV sign)
    #--------------------------
    #http://stream.nbcsports.com/data/mobile/Requestor_ID_Lookup_doc.csv
    #--------------------------
    resource_id = GET_RESOURCE_ID()
    adobe.authorizeDevice(resource_id)
    media_token = adobe.mediaToken(resource_id)
    stream_url = adobe.tvSign(media_token, resource_id, stream_url)

    #Set quality level based on user settings
    #stream_url = SET_STREAM_QUALITY(stream_url)

    listitem = xbmcgui.ListItem(path=stream_url)


    if str(PLAY_MAIN) == 'true':
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    else:
        addLink(stream_name, stream_url, stream_name, stream_icon, FANART)

def logout():
    adobe = ADOBE(SERVICE_VARS)
    adobe.deauthorizeDevice()
    ADDON.setSetting(id='clear_data', value='false')



if CLEAR == 'true':
   logout()

params=get_params()
url=None
name=None
mode=None
scrape_type=None
icon_image = None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    scrape_type=urllib.unquote_plus(params["scrape_type"])
except:
    pass
try:
    icon_image=urllib.unquote_plus(params["icon_image"])
except:
    pass



if mode is None or url is None or len(url)<1:
        categories()
elif mode==3:
    olympics(url)
elif mode==4:
        scrapeVideos(url,scrape_type)
elif mode==5:
        signStream(url, name, icon_image)

elif mode==6:
    #Set quality level based on user settings
    stream_url = SET_STREAM_QUALITY(url)
    listitem = xbmcgui.ListItem(path=stream_url)

    if str(PLAY_MAIN) == 'true':
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    else:
        addLink(name, stream_url, name, icon_image, FANART)


#Don't cache live and upcoming list
if mode==1:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
