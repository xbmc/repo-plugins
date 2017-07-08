# -*- coding: utf-8 -*-
import urllib, urlparse
import xbmc, xbmcgui,xbmcaddon,xbmcplugin
import re, htmlentitydefs
import pickle
import json
import sys,os #os is used in open_web_browser()

from urllib import urlencode



addon         = xbmcaddon.Addon()
addonID       = addon.getAddonInfo('id')  #plugin.video.reddit_viewer

DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')

pluginhandle  = int(sys.argv[1])

image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp'] #exclude 'gif' as we consider it as gifv

def save_dict( dict_to_save, pickle_filename ):
    with open(pickle_filename, 'wb') as output:
        pickle.dump(dict_to_save, output)
        output.close()

def append_dict( dict_to_save, pickle_filename ):
    with open(pickle_filename, 'a+b') as output:
        pickle.dump(dict_to_save, output)
        output.close()

def load_dict( pickle_filename ):
    with open(pickle_filename, 'rb') as inputpkl:
        rows_dict= pickle.load(inputpkl)
        inputpkl.close()
    return rows_dict

def xbmc_busy(busy=True):
    if busy:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
    else:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

def log(message, level=xbmc.LOGDEBUG):
    import threading
    t=threading.currentThread()
    xbmc.log("reddit_viewer {0}:{1}".format(t.name, message), level=level)

def translation(id_):
    return addon.getLocalizedString(id_).encode('utf-8')

def compose_list_item(label,label2,iconImage,property_item_type, onClick_action, infolabels=None  ):


    liz=xbmcgui.ListItem(label=label,
                         label2=label2,
                         path="") #<-- DirectoryItem_url is not used here by the xml gui
    liz.setArt({"icon":iconImage, "thumb":iconImage,})
    liz.setProperty('item_type', property_item_type)  #item type "script" -> ('RunAddon(%s):' % di_url )

    liz.setProperty('onClick_action', onClick_action)

    if infolabels==None:
        pass
    else:
        liz.setInfo(type="Video", infoLabels=infolabels)

    return liz


def build_script( mode, url="", name="", type_="", script_to_call=''):

    if script_to_call: #plugin://plugin.video.reddit_viewer/

        pass
    else:

        name='' if name==None else name.decode('unicode_escape').encode('ascii','ignore')
        url=''  if url==None else url.decode('unicode_escape').encode('ascii','ignore') #causes error in urllib.quote_plus() if None
        script_to_call=addonID

        return "RunAddon({script_to_call},mode={mode}&url={url}&name={name}&type={type})".format( script_to_call=script_to_call,
                                                                                                  mode=mode,
                                                                                                  url=urllib.quote_plus(url),
                                                                                                  name=urllib.quote_plus(name),
                                                                                                  type=str(type_)  )

def build_playable_param( mode, url, name="", type_="", script_to_call=addonID):

    return "plugin://" +script_to_call+"mode="+ mode+"&url="+urllib.quote_plus(url)+"&name="+str(name)+"&type="+str(type_)

def ret_info_type_icon(info_type, modecommand, domain=''):


    from domains import sitesBase
    icon="type_unsupp.png"
    if info_type==sitesBase.TYPE_VIDEO:
        icon="type_video.png"
        if modecommand==sitesBase.DI_ACTION_YTDL:
            icon="type_ytdl.png"
        if modecommand==sitesBase.DI_ACTION_URLR:
            icon="type_urlr.png"
        if any( x in domain for x in ['youtube','youtu.be']):
            icon="type_youtube.png"


    elif info_type==sitesBase.TYPE_ALBUM:
        icon="type_album.png"
    elif info_type==sitesBase.TYPE_GIF:
        icon="type_gif.png"
    elif info_type==sitesBase.TYPE_IMAGE:
        icon="type_image.png"
    elif info_type==sitesBase.TYPE_REDDIT:
        icon="alienicon.png"

    return icon

def pretty_datediff(dt1, dt2):
    try:
        diff = dt1 - dt2

        sec_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return 'future'

        if day_diff == 0:
            if sec_diff < 10:
                return translation(30060)     #"just now"
            if sec_diff < 60:
                return str(sec_diff) + translation(30061)      #" secs ago"
            if sec_diff < 120:
                return translation(30062)     #"a min ago"
            if sec_diff < 3600:
                return str(sec_diff / 60) + translation(30063) #" mins ago"
            if sec_diff < 7200:
                return translation(30064)     #"an hour ago"
            if sec_diff < 86400:
                return str(sec_diff / 3600) + translation(30065) #" hrs ago"
        if day_diff == 1:
            return translation(30066)         #"Yesterday"
        if day_diff < 7:
            return str(day_diff) + translation(30067)      #" days ago"
        if day_diff < 31:
            return str(day_diff / 7) + translation(30068)  #" wks ago"
        if day_diff < 365:
            return str(day_diff / 30) + translation(30069) #" months ago"
        return str(day_diff / 365) + translation(30070)    #" years ago"
    except:
        pass

def is_filtered(filter_csv, str_to_check):

    filter_list=filter_csv.split(',')
    if any(word in str_to_check for word in filter_list if word):
        return True

def post_excluded_from( filter_, str_to_check):

    if filter_:
        filter_list=filter_.split(',')
        filter_list=[x.lower().strip() for x in filter_list]  #  list comprehensions

        if str_to_check.lower() in filter_list:
            return True
    return False

def add_to_csv_setting(setting_id, string_to_add):

    addon=xbmcaddon.Addon()
    csv_setting=addon.getSetting(setting_id)
    csv_list=csv_setting.split(',')
    csv_list=[x.lower().strip() for x in csv_list]
    csv_list.append(string_to_add)

    csv_list = filter(None, csv_list)                 #removes empty string
    addon.setSetting(setting_id, ",".join(csv_list))

    if setting_id=='domain_filter':
        s=colored_subreddit( string_to_add, 'tan',False )
    elif setting_id=='subreddit_filter':
        s=colored_subreddit( string_to_add )
    xbmc_notify(s, translation(30020)+' '+setting_id.replace('_',' ')) #translation(30020)=Added to


def post_is_filtered_out( data ):
    from default import hide_nsfw, domain_filter, subreddit_filter

    domain=clean_str(data,['domain'])
    if post_excluded_from( domain_filter, domain ):
        log( '  POST is excluded by domain_filter [%s]' %domain )
        return True

    subreddit=clean_str(data,['subreddit'])
    if post_excluded_from( subreddit_filter, subreddit ):
        log( '  POST is excluded by subreddit_filter [r/%s]' %subreddit )
        return True

    try:    over_18 = data.get('over_18')
    except: over_18 = False

    if over_18 and hide_nsfw:
        log( '  POST is excluded by NSFW filter'  )
        return True

    return False

def addtoFilter(to_filter, name, type_of_filter):

    if type_of_filter=='domain':

        add_to_csv_setting('domain_filter',to_filter)
    elif type_of_filter=='subreddit':

        add_to_csv_setting('subreddit_filter',to_filter)
    else:
        return

def prettify_reddit_query(subreddit_entry):


    if subreddit_entry.startswith('?'):

        tbn=subreddit_entry.split('/')[-1]
        tbn=urllib.unquote_plus(tbn)

        tbn=tbn.replace('?q=','[LIGHT]search:[/LIGHT]' )
        tbn=tbn.replace('site:','' )
        tbn=tbn.replace('&sort=','[LIGHT] sort by:[/LIGHT]' )
        tbn=tbn.replace('&t=','[LIGHT] from:[/LIGHT]' )
        tbn=tbn.replace('subreddit:','r/' )
        tbn=tbn.replace('author:','[LIGHT] by:[/LIGHT]' )
        tbn=tbn.replace('&restrict_sr=on','' )
        tbn=tbn.replace('&restrict_sr=','' )
        tbn=tbn.replace('nsfw:no','' )
        tbn=tbn.replace('nsfw:yes','nsfw' )

        return tbn
    else:
        return subreddit_entry

def calculate_zoom_slide(img_w, img_h):
    screen_w = 1920
    screen_h = 1080


    shrink_percent = (float(screen_h) / img_h)
    slide_end = float(img_h-screen_h) * shrink_percent

    log("  shrink_percentage %f " %(shrink_percent) )

    if img_w > screen_w:

        s_w=img_w*shrink_percent

        zoom_percent = (float(screen_w) / s_w) - shrink_percent
        log("  percent 2 zoom  %f " %(zoom_percent) )

        s_h=img_h*shrink_percent  #==screen_h

        nso_h=s_h* zoom_percent
        log("  img h  %f " %(nso_h) )

        slide_end = float(nso_h-screen_h) * 1/zoom_percent   #shrink_percent
    else:

        zoom_percent = ( float(1) / shrink_percent )



        log("  percent to zoom  %f " %(zoom_percent) )

    return zoom_percent * 100, slide_end


def parse_filename_and_ext_from_url(url=""):
    filename=""
    ext=""

    path = urlparse.urlparse(url).path

    try:
        if '.' in path:

            filename = path.split('/')[-1].split('.')[0]
            ext      = path.split('/')[-1].split('.')[-1]

            if not ext=="":

                ext=re.split("\?|#",ext)[0]

            return filename, ext.lower()
    except:
        pass

    return "", ""

def link_url_is_playable(url):
    ext=ret_url_ext(url)
    if ext in image_exts:
        return 'image'
    if ext in ['mp4','webm','mpg','gifv','gif']:
        return 'video'

    return False

def ret_url_ext(url):
    if url:
        url=url.split('?')[0]

        if url:
            _,ext=parse_filename_and_ext_from_url(url)

            return ext
    return False


def remove_duplicates(seq, idfun=None):

    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)

        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def remove_dict_duplicates(list_of_dict, key):

    seen = set()
    return [x for x in list_of_dict if [ x.get(key) not in seen, seen.add(  x.get(key) ) ] [0]]

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default

def cleanTitle(title):

    title = title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"")
    return title.strip()

def unescape(text):


    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":

            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:

            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    text=re.sub("&#?\w+;", fixup, text)
    text=text.replace('&nbsp;',' ')
    text=text.replace('\n\n','\n')
    return text

def strip_emoji(text):

    emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
        "+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text) # no emoji

def markdown_to_bbcode(s):

    links = {}
    codes = []
    try:


        def translate(p="%s", g=1):
            def inline(m):
                s = m.group(g)

                s = re.sub(r"\B([*_]{2})\b(.+?)\1\B", "[B]\\2[/B]", s)
                s = re.sub(r"\B([*_])\b(.+?)\1\B", "[I]\\2[/I]", s)
                return p % s
            return inline

        s = re.sub(r"(?m)^#{4,6}\s*(.*?)\s*#*$", translate("[LIGHT]%s[/LIGHT]"), s)       #heading4-6 becomed light
        s = re.sub(r"(?m)^#{1,3}\s*(.*?)\s*#*$", translate("[B]%s[/B]"), s)               #heading1-3 becomes bold


        s = re.sub(r"(?m)^>\s*(.*)$", translate("|%s"), s)                                #quotes  get pipe character beginning

        s = re.sub(r"(?m)^((?!~).*)$", translate(), s)


        s = re.sub(r"<strong>(.*?)<\/strong>$", translate("[B]%s[/B]"), s)                                #<strong></strong>  becomes bold
        return s
    except:
        return s

def format_description(s, hide_text_in_parens=True):

    formatted=unescape(s)  #convert html entities e.g.:(&#39;)

    if hide_text_in_parens:
        formatted=re.sub(r']\([^)]*\)', ']', formatted)
    else:

        formatted=s.replace('](', '] (')

    formatted=markdown_to_bbcode(formatted)
    formatted=strip_emoji(formatted)
    return formatted

def convert_date(stamp):

    import time

    date_time = time.localtime(stamp)
    if DATEFORMAT[1] == 'd':
        localdate = time.strftime('%d-%m-%Y', date_time)
    elif DATEFORMAT[1] == 'm':
        localdate = time.strftime('%m-%d-%Y', date_time)
    else:
        localdate = time.strftime('%Y-%m-%d', date_time)
    if TIMEFORMAT != '/':
        localtime = time.strftime('%I:%M%p', date_time)
    else:
        localtime = time.strftime('%H:%M', date_time)
    return localtime + '  ' + localdate


def xbmcVersion():

    build = xbmc.getInfoLabel('System.BuildVersion')

    methods = [
        lambda b: float(b.split()[0]),               # sample input: 10.1 Git:Unknown
        lambda b: float(b.split()[0].split('-')[1]), # sample input: PRE-11.0 Git:Unknown
        lambda b: float(b.split()[0].split('-')[0]), # sample input: 11.0-BETA1 Git:20111222-22ad8e4
        lambda b: 0.0
    ]

    for m in methods:
        try:
            version = m(build)
            break
        except ValueError:

            pass

    return version

def clean_str(dict_obj, keys_list, default=''):
    dd=dict_obj
    try:
        for k in keys_list:
            if isinstance(dd, dict):
                dd=dd.get(k)
            elif isinstance(dd, list):
                dd=dd[k]

            if dd is None:
                return default
            else:
                continue
        return unescape(dd.encode('utf-8'))
    except (AttributeError,IndexError) as e:
        log( 'clean_str:' + str(e) )
        return default

def get_int(dict_obj, keys_list, default=0):
    dd=dict_obj
    try:
        for k in keys_list:
            if isinstance(dd, dict):

                dd=dd.get(k)
            elif isinstance(dd, list):

                dd=dd[k]

            if dd is None:
                return default
            else:
                continue
        return int(dd)
    except AttributeError as e:
        log( 'get_int AttributeError:' + str(e) )
    except ValueError as e:
        log( 'get_int ValueError:' + str(e) )

    return default

def xstr(s):

    if s is None:
        return ''
    return str(s)


def samealphabetic(*args):

    return len(set(filter(lambda s: s.isalpha(), arg.lower()) for arg in args)) <= 1

def hassamealphabetic(*args):

    return len(set(filter(lambda s: s.isalpha(), arg) for arg in args)) <= 2

def colored_subreddit(subreddit,color='cadetblue', add_r=True):

    return "[COLOR %s]%s%s[/COLOR]" %(color,('r/' if add_r else ''),subreddit )

def truncate(string, length, ellipse='...'):
    return (string[:length] + ellipse) if len(string) > length else string

def xbmc_notify(line1, line2, time=2000, icon=''):
    if icon and os.path.sep not in icon:
        icon=os.path.join(addon.getAddonInfo('path'), 'resources','skins','Default','media', icon)

    xbmcgui.Dialog().notification( line1, line2, icon, time)  #<-- use this instead of  xbmc.executebuiltin('XBMC.Notification("%s", "%s", %d, %s )' %( Line1, line2, time, icon) )
    log("User notification: %s: %s" %(line1, line2) )

def open_web_browser(url,name,type_):

    osWin = xbmc.getCondVisibility('system.platform.windows')
    osOsx = xbmc.getCondVisibility('system.platform.osx')
    osLinux = xbmc.getCondVisibility('system.platform.linux')
    osAndroid = xbmc.getCondVisibility('System.Platform.Android')


    custom_link_command=addon.getSetting('custom_link_command')
    if custom_link_command:
        custom_link_command=custom_link_command.replace('{url}',url)
        log('Running custom command for link:\n' + custom_link_command)
        exec( custom_link_command )

    else:

        if osOsx:

            xbmc.executebuiltin("System.Exec(open "+url+")")
        elif osWin:

            xbmc.executebuiltin("System.Exec(cmd.exe /c start "+url+")")
        elif osLinux and not osAndroid:

            xbmc.executebuiltin("System.Exec(xdg-open "+url+")")
        elif osAndroid:

            xbmc.executebuiltin("StartAndroidActivity(com.android.browser,android.intent.action.VIEW,,"+url+")")

def addDir(name, url, mode, iconimage, type_="", listitem_infolabel=None, label2=""):

    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type_)

    ok = True
    liz = xbmcgui.ListItem(label=name, label2=label2)
    if iconimage:
        liz.setArt({ 'thumb': iconimage, 'icon': iconimage, 'clearlogo': iconimage  })

    if listitem_infolabel==None:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)


    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def addDirR(name, url, mode, icon_image='', type_="", listitem_infolabel=None, file_entry="", banner_image=''):


    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type_)

    ok = True
    liz = xbmcgui.ListItem(name)

    if icon_image:
        liz.setArt({ 'thumb': icon_image, 'icon': icon_image, 'clearlogo': icon_image  })  #thumb is used in 'shift' view (estuary)   thunb,icon are interchangeable in list view

    if banner_image:
        liz.setArt({ 'banner': banner_image  })

        liz.setArt({ 'fanart': banner_image  })


    if listitem_infolabel==None:

        liz.setInfo(type="Video", infoLabels={"Title": name})
    else:
        liz.setInfo(type="Video", infoLabels=listitem_infolabel)

    if file_entry:
        liz.setProperty("file_entry", file_entry)

    liz.addContextMenuItems([(translation(30003), 'RunPlugin(plugin://'+addonID+'/?mode=editSubreddit&url='+urllib.quote_plus(file_entry)+')',)     ,
                             (translation(30002), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(file_entry)+')',)
                             ])

    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def json_query(query, ret):
    try:
        xbmc_request = json.dumps(query)
        result = xbmc.executeJSONRPC(xbmc_request)

        if ret:
            return json.loads(result)['result']
        else:
            return json.loads(result)
    except:
        return {}

def nested_lookup(key, document):
    """Lookup a key in a nested document, return a list of values"""
    return list(_nested_lookup(key, document))

def _nested_lookup(key, document):

    """Lookup a key in a nested document, yield a value"""
    if isinstance(document, list):
        for d in document:
            for result in _nested_lookup(key, d):
                yield result

    if isinstance(document, dict):
        for k, v in dict.items(document): #iteritems(document):
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in _nested_lookup(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in _nested_lookup(key, d):
                        yield result

def dictlist_to_listItems(dictlist):
    from domains import sitesBase

    directory_items=[]

    for idx, d in enumerate(dictlist):
        label=d.get('li_label')
        label2=d.get('li_label2')

        ti=d.get('li_thumbnailImage')
        media_url=d.get('DirectoryItem_url')
        media_type=d.get('type')
        isPlayable=d.get('isPlayable')
        link_action=d.get('link_action')
        channel_id=d.get('channel_id')
        video_id=d.get('video_id')
        infoLabels=d.get('infoLabels')


        liz=xbmcgui.ListItem(label=label, label2=label2)

        if media_type==sitesBase.TYPE_IMAGE:
            liz.setProperty('item_type','script')
            liz.setProperty('onClick_action', build_script('viewImage', media_url,'',ti) )
            liz.setArt({"thumb": ti, "banner":media_url })
        else:  #if media_type==sitesBase.TYPE_VIDEO:

            if not link_action:
                link_action='playYTDLVideo' #default action is to send link to ytdl

            if isPlayable=='true':
                liz.setProperty('item_type','playable')
                liz.setProperty('onClick_action', media_url )
                liz.setProperty('is_video','true')
            else:
                liz.setProperty('item_type','script')
                liz.setProperty('onClick_action', build_script(link_action, media_url,'','') )

            liz.setArt({"thumb": ti })

        liz.setProperty('link_url', media_url )  #added so we have a way to retrieve the link
        liz.setProperty('channel_id', channel_id )
        liz.setProperty('video_id', video_id )   #youtube only for now
        liz.setProperty('label', label )

        liz.setInfo( type='video', infoLabels=infoLabels ) #this tricks the skin to show the plot. where we stored the picture descriptions


        directory_items.append( liz )

    return directory_items

def generator(iterable):
    for element in iterable:
        yield element

def setting_entry_is_domain(setting_entry):
    try:
        domain=re.findall(r'(?::|\/domain\/)(.+)',setting_entry)[0]
    except IndexError:
        domain=''
    return domain

def get_domain_icon( entry_name, domain ):
    import requests
    from CommonFunctions import parseDOM
    subs_dict={}

    req='http://%s' %domain

    r = requests.get( req )

    if r.status_code == requests.codes.ok:
        try:og_url=parseDOM(r.text, "meta", attrs = { "property": "og:url" }, ret="content" )[0]  #<meta content="https://www.blogger.com" property="og:url">
        except:og_url=req

        a=parseDOM(r.text, "meta", attrs = { "property": "og:image" }, ret="content" )
        b=parseDOM(r.text, "link", attrs = { "rel": "apple-touch-icon" }, ret="href" )
        c=parseDOM(r.text, "link", attrs = { "rel": "apple-touch-icon-precomposed" }, ret="href" )
        d=parseDOM(r.text, "link", attrs = { "rel": "icon" }, ret="href" )

        i=next((item for item in [a,b,c,d] if item ), '')
        if i:

            try:
                icon=urlparse.urljoin(og_url, i[-1]) #handle relative or absolute

                subs_dict.update( {'entry_name':entry_name,
                                   'display_name':domain,
                                   'icon_img': icon,

                                   } )

                return subs_dict

            except IndexError: pass
        else:
            log( "    can't parse icon: get_domain_icon (%s)" %(domain) )
    else:
        log( '    getting get_domain_icon (%s) info:%s' %(domain, r.status_code) )

def set_query_field(url, field, value, replace=False):


    components = urlparse.urlparse(url)

    query_pairs = urlparse.parse_qsl(components.query)

    if replace:
        query_pairs = [(f, v) for (f, v) in query_pairs if f != field]
    query_pairs.append((field, value))

    new_query_str = urllib.urlencode(query_pairs)

    new_components = (
        components.scheme,
        components.netloc,
        components.path,
        components.params,
        new_query_str,
        components.fragment
    )
    return urlparse.urlunparse(new_components)

if __name__ == '__main__':
    pass