# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcplugin

import sys
import shutil
import re, pprint, os

from default import subredditsFile, addon, addon_path, profile_path, ytdl_core_path, pluginhandle, subredditsPickle
from utils import xbmc_busy, log, translation, xbmc_notify
from reddit import get_subreddit_entry_info

ytdl_quality=addon.getSetting("ytdl_quality")
try: ytdl_quality=[0, 1, 2, 3][ int(ytdl_quality) ]
except ValueError: ytdl_quality=1
ytdl_DASH=addon.getSetting("ytdl_DASH")=='true'

def addSubreddit(subreddit, name, type_):
    from utils import colored_subreddit
    from reddit import this_is_a_multireddit, format_multihub
    alreadyIn = False
    with open(subredditsFile, 'r') as fh:
        content = fh.readlines()
    if subreddit:
        for line in content:
            if line.lower()==subreddit.lower():
                alreadyIn = True
        if not alreadyIn:
            with open(subredditsFile, 'a') as fh:
                fh.write(subreddit+'\n')

            get_subreddit_entry_info(subreddit)
        xbmc_notify(colored_subreddit(subreddit), translation(30019))
    else:


        keyboard = xbmc.Keyboard('', translation(30001))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            subreddit = keyboard.getText()

            if this_is_a_multireddit(subreddit):
                subreddit = format_multihub(subreddit)
            else:
                get_subreddit_entry_info(subreddit)

            for line in content:
                if line.lower()==subreddit.lower()+"\n":
                    alreadyIn = True

            if not alreadyIn:
                with open(subredditsFile, 'a') as fh:
                    fh.write(subreddit+'\n')

        xbmc.executebuiltin("Container.Refresh")

def removeSubreddit(subreddit, name, type_):
    log( 'removeSubreddit ' + subreddit)

    with open(subredditsFile, 'r') as fh:
        content = fh.readlines()

    contentNew = ""
    for line in content:
        if line!=subreddit+'\n':

            contentNew+=line
    with open(subredditsFile, 'w') as fh:
        fh.write(contentNew)

    xbmc.executebuiltin("Container.Refresh")

def editSubreddit(subreddit, name, type_):
    from reddit import this_is_a_multireddit, format_multihub
    log( 'editSubreddit ' + subreddit)

    with open(subredditsFile, 'r') as fh:
        content = fh.readlines()

    contentNew = ""

    keyboard = xbmc.Keyboard(subreddit, translation(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        newsubreddit = keyboard.getText()

        if this_is_a_multireddit(newsubreddit):
            newsubreddit = format_multihub(newsubreddit)
        else:
            get_subreddit_entry_info(newsubreddit)

        for line in content:
            if line.strip()==subreddit.strip() :      #if matches the old subreddit,

                contentNew+=newsubreddit+'\n'
            else:
                contentNew+=line

        with open(subredditsFile, 'w') as fh:
            fh.write(contentNew)

        xbmc.executebuiltin("Container.Refresh")

def searchReddits(url, name, type_):
    from default import urlMain
    from main_listing import listSubReddit
    keyboard = xbmc.Keyboard('sort=new&t=week&q=', translation(30005))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():

        search_string = keyboard.getText().replace(" ", "+")

        url = urlMain +"/search.json?" +search_string    #+ '+' + nsfw  # + sites_filter skip the sites filter

        listSubReddit(url, name, "")

def setting_gif_repeat_count():
    srepeat_gif_video= addon.getSetting("repeat_gif_video")
    try: repeat_gif_video = int(srepeat_gif_video)
    except ValueError: repeat_gif_video = 0

    return [0, 1, 3, 10, 100][repeat_gif_video]

def viewImage(image_url, name, preview_url):
    from guis import cGUI

    log('  viewImage %s, %s, %s' %( image_url, name, preview_url))

    msg=""
    li=[]
    liz=xbmcgui.ListItem(label=msg, label2="")
    liz.setInfo( type='video', infoLabels={"plot": msg, } )
    liz.setArt({"thumb": preview_url, "banner":image_url })

    li.append(liz)
    ui = cGUI('view_450_slideshow.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=53)
    ui.include_parent_directory_entry=False

    ui.doModal()
    del ui
    return


def viewTallImage(image_url, width, height):
    log( 'viewTallImage %s: %sx%s' %(image_url, width, height))

    useWindow=xbmcgui.WindowXMLDialog('slideshow05.xml', addon_path)

    screen_w=1920
    screen_h=1080

    log('screen %dx%d'%(screen_w,screen_h))
    try:
        w=int(float(width))
        h=int(float(height))
        ar=float(w/h)
        resize_percent=float(screen_w)/w
        if w > screen_w:
            new_h=int(h*resize_percent)
        else:
            if abs( h - screen_h) < ( screen_h / 10 ):  #if the image height is about 10 percent of the screen height, zoom it a bit
                new_h=screen_h*2
            elif h < screen_h:
                new_h=screen_h
            else:
                new_h=h

        log( '   image=%dx%d resize_percent %f  new_h=%d ' %(w,h, resize_percent, new_h))

        loading_img = xbmc.validatePath('/'.join((addon_path, 'resources', 'skins', 'Default', 'media', 'srr_busy.gif' )))

        slide_h=new_h-screen_h
        log( '  slide_h=' + repr(slide_h))

        img_control = xbmcgui.ControlImage(0, 0, screen_w, new_h, '', aspectRatio=2)  #(values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)

        img_loading = xbmcgui.ControlImage(screen_w-100, 0, 100, 100, loading_img, aspectRatio=2)

        img_control.setImage(image_url, False)

        useWindow.addControls( [ img_loading, img_control])

        img_control.setPosition(0,0)
        scroll_time=(int(h)/int(w))*20000

        img_control.setAnimations( [
                                    ('conditional', "condition=true delay=6000 time=%d effect=slide  start=0,-%d end=0,0 tween=sine easing=inout  pulse=true" %( scroll_time, slide_h) ),
                                    ('conditional', "condition=true delay=0  time=4000 effect=fade   start=0   end=100    "  ) ,
                                    ]  )
        useWindow.doModal()
        useWindow.removeControls( [img_control,img_loading] )
        del useWindow
    except Exception as e:
        log("  EXCEPTION viewTallImage:="+ str( sys.exc_info()[0]) + "  " + str(e) )

def display_album_from(dictlist, album_name):
    from domains import parse_reddit_link, build_DirectoryItem_url_based_on_media_type, sitesBase
    from utils import build_script
    directory_items=[]

    album_viewMode=addon.getSetting("album_viewMode")

    if album_viewMode=='450': #using custom gui
        using_custom_gui=True
    else:
        using_custom_gui=False

    for _, d in enumerate(dictlist):
        ti=d['li_thumbnailImage']
        media_url=d.get('DirectoryItem_url')

        combined = d['infoLabels'].get('plot') if d['infoLabels'].get('plot') else ""
        d['infoLabels']['plot'] = combined

        liz=xbmcgui.ListItem(label=d.get('li_label'), label2=d.get('li_label2') )

        ld=parse_reddit_link(media_url)
        DirectoryItem_url, setProperty_IsPlayable, isFolder, _ = build_DirectoryItem_url_based_on_media_type(ld, media_url, '', '', script_to_call="")

        if using_custom_gui:
            url_for_DirectoryItem=media_url
            liz.setProperty('onClick_action',  DirectoryItem_url )
            liz.setProperty('is_video','true')

            if ld.link_action == sitesBase.DI_ACTION_PLAYABLE:
                liz.setProperty('item_type','playable')
            else:

                liz.setProperty('item_type','script')
        else:

            liz.setProperty('IsPlayable',setProperty_IsPlayable)
            url_for_DirectoryItem=DirectoryItem_url

        liz.setInfo( type='video', infoLabels=d['infoLabels'] ) #this tricks the skin to show the plot. where we stored the picture descriptions
        liz.setArt({"thumb": ti,'icon': ti, "poster":media_url, "banner":media_url, "fanart":media_url, "landscape":media_url   })

        directory_items.append( (url_for_DirectoryItem, liz, isFolder) )

    if using_custom_gui:
        from guis import cGUI
        li=[]
        for di in directory_items:
            li.append( di[1] )

        ui = cGUI('view_450_slideshow.xml' , addon_path, defaultSkin='Default', defaultRes='1080i', listing=li, id=53)
        ui.include_parent_directory_entry=False

        ui.doModal()
        del ui
    else:
        if album_viewMode!='0':
            xbmc.executebuiltin('Container.SetViewMode('+album_viewMode+')')

        xbmcplugin.addDirectoryItems(handle=pluginhandle, items=directory_items )
        xbmcplugin.endOfDirectory(pluginhandle)

def listAlbum(album_url, name, type_):
    from slideshow import slideshowAlbum
    from domains import sitesManager
    log("    listAlbum:"+album_url)

    hoster = sitesManager( album_url )


    if hoster:
        dictlist=hoster.ret_album_list(album_url)

        if type_=='return_dictlist':  #used in autoSlideshow
            return dictlist

        if not dictlist:
            xbmc_notify(translation(32200),translation(32055)) #slideshow, no playable items
            return

        if addon.getSetting('use_slideshow_for_album') == 'true':
            slideshowAlbum( dictlist, name )
        else:
            display_album_from( dictlist, name )

def playURLRVideo(url, name, type_):
    dialog_progress_title='URL Resolver'
    dialog_progress_YTDL = xbmcgui.DialogProgressBG()
    dialog_progress_YTDL.create(dialog_progress_title )
    dialog_progress_YTDL.update(10,dialog_progress_title,translation(30024)  )

    import urlresolver

    dialog_progress_YTDL.update(20,dialog_progress_title,translation(30022)  )

    try:
        media_url = urlresolver.resolve(url)
        dialog_progress_YTDL.update(80,dialog_progress_title,translation(30023)  )
        if media_url:
            log( '  URLResolver stream url=' + repr(media_url ))

            listitem = xbmcgui.ListItem(path=media_url)
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
            log( "  Can't URL Resolve:" + repr(url))
            xbmc_notify('URLresolver',translation(30192))
    except Exception as e:
        xbmc_notify('URLresolver', str(e) )
    dialog_progress_YTDL.close()

def loopedPlayback(url, name, type_):

    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear()
    pl.add(url, xbmcgui.ListItem(name))
    for _ in range( 0, setting_gif_repeat_count() ):
        pl.add(url, xbmcgui.ListItem(name))

    xbmc.Player().play(pl, windowed=False)

def error_message(message, name, type_):
    if name:
        sub_msg=name
    else:
        sub_msg=translation(30021) #Parsing error
    xbmc_notify(message,sub_msg)

def playVideo(url, name, type_):
    if url :

        listitem = xbmcgui.ListItem(label=name,path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
        log("playVideo(url) url is blank")

def playYTDLVideo(url, name, type_):
    if pluginhandle==-1:
        xbmc_notify("Error","Attempt to use invalid handle -1") #saves the user from waiting
        return

    dialog_progress_title='Youtube_dl'  #.format(ytdl_get_version_info())
    dialog_progress_YTDL = xbmcgui.DialogProgressBG()
    dialog_progress_YTDL.create(dialog_progress_title )
    dialog_progress_YTDL.update(10,dialog_progress_title,translation(30024)  )

    from YoutubeDLWrapper import YoutubeDLWrapper, _selectVideoQuality
    from urlparse import urlparse, parse_qs
    import pprint

    o = urlparse(url)
    query = parse_qs(o.query)
    video_index=0

    if 'index' in query:
        try:video_index=int(query['index'][0])
        except (TypeError, ValueError): video_index=0

        dialog_progress_YTDL.update(20,dialog_progress_title,translation(30025)  )
    else:

        dialog_progress_YTDL.update(20,dialog_progress_title,translation(30022)  )

    ytdl=YoutubeDLWrapper()
    try:
        ydl_info=ytdl.extract_info(url, download=False)

        video_infos=_selectVideoQuality(ydl_info, quality=ytdl_quality, disable_dash=(not ytdl_DASH))

        dialog_progress_YTDL.update(80,dialog_progress_title,translation(30023)  )

        if len(video_infos)>1:
            log('    ***ytdl link resolved to %d streams. playing #%d' %(len(video_infos), video_index))


        li=ytdl_video_info_to_listitem(video_infos, video_index, name)
        xbmcplugin.setResolvedUrl(pluginhandle, True, li)

    except Exception as e:
        ytdl_ver=dialog_progress_title+' v'+ytdl_get_version_info('local')
        err_msg=str(e)+';'  #ERROR: No video formats found; please report this issue on https://yt-dl.org/bug . Make sure you are using the latest vers....
        short_err=err_msg.split(';')[0]
        log( "playYTDLVideo Exception:" + str( sys.exc_info()[0]) + "  " + str(e) )
        xbmc_notify(ytdl_ver, short_err)

        log('   trying urlresolver...')
        playURLRVideo(url, name, type_)

    dialog_progress_YTDL.update(100,dialog_progress_title ) #not sure if necessary to set to 100 before closing dialogprogressbg
    dialog_progress_YTDL.close()

def ytdl_video_info_to_listitem(video_infos, video_index, title=None):

    if video_index > 0 and video_index<len(video_infos):
        video_info=video_infos[video_index-1]
    else:

        video_info=video_infos[0]

    url=video_info.get('xbmc_url')
    title=video_info.get('title') or title

    ytdl_format=video_info.get('ytdl_format')
    if ytdl_format:
        description=ytdl_format.get('description')

        try:
            start_time=ytdl_format.get('start_time',0)   #int(float(ytdl_format.get('start_time')))
            duration=ytdl_format.get('duration',0)
            StartPercent=(float(start_time)/duration)*100
        except (ValueError, TypeError, ZeroDivisionError):
            StartPercent=0

        video_thumbnail=video_info.get('thumbnail')
        li=xbmcgui.ListItem(label=title,
                            label2='',
                            path=url)
        li.setInfo( type="Video", infoLabels={ "Title": title, "plot": description } )
        li.setArt( {'icon':video_thumbnail, 'thumb':video_thumbnail} )

        li.setProperty('StartPercent', str(StartPercent))

        return li

def playYTDLVideoOLD(url, name, type_):

    from urlparse import urlparse
    parsed_uri = urlparse( url )
    domain = '{uri.netloc}'.format(uri=parsed_uri)

    dialog_progress_YTDL = xbmcgui.DialogProgressBG()
    dialog_progress_YTDL.create('YTDL' )
    dialog_progress_YTDL.update(10,'YTDL','Checking link...' )

    try:
        from domains import ydtl_get_playable_url
        stream_url = ydtl_get_playable_url(url)
        if stream_url:
            dialog_progress_YTDL.update(80,'YTDL', 'Playing' )
            listitem = xbmcgui.ListItem(path=stream_url[0])   #plugins play video like this.
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
            dialog_progress_YTDL.update(40,'YTDL', 'Trying URLResolver' )
            log('YTDL Unable to get playable URL, Trying UrlResolver...' )

            media_url = urlresolver.resolve(url)
            if media_url:
                dialog_progress_YTDL.update(88,'YTDL', 'Playing' )

                listitem = xbmcgui.ListItem(path=media_url)
                xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
            else:
                log('UrlResolver cannot get a playable url' )
                xbmc_notify(translation(30192), domain)

    except Exception as e:
        xbmc_notify("%s(YTDL)"% domain,str(e))
    finally:
        dialog_progress_YTDL.update(100,'YTDL' ) #not sure if necessary to set to 100 before closing dialogprogressbg
        dialog_progress_YTDL.close()

def parse_url_and_play(url, name, type_):
    from domains import parse_reddit_link, sitesBase, ydtl_get_playable_url, build_DirectoryItem_url_based_on_media_type


    log('parse_url_and_play url='+url)

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    ld=parse_reddit_link(url,True, False, False  )

    DirectoryItem_url, setProperty_IsPlayable, isFolder, title_prefix = build_DirectoryItem_url_based_on_media_type(ld, url)

    if setProperty_IsPlayable=='true':
        log( '---------IsPlayable---------->'+ DirectoryItem_url)
        playVideo(DirectoryItem_url,'','')
    else:
        if isFolder: #showing album
            log( '---------using ActivateWindow------>'+ DirectoryItem_url)
            xbmc.executebuiltin('ActivateWindow(Videos,'+ DirectoryItem_url+')')
        else:  #viewing image
            log( '---------using setResolvedUrl------>'+ DirectoryItem_url)


            listitem = xbmcgui.ListItem(path='')
            listitem.setProperty('IsPlayable', 'false')
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

            xbmc.executebuiltin('RunPlugin(%s)' % ( DirectoryItem_url ) )


def queueVideo(url, name, type_):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)






YTDL_VERSION_URL = 'https://yt-dl.org/latest/version'
YTDL_LATEST_URL_TEMPLATE = 'https://yt-dl.org/latest/youtube-dl-{}.tar.gz'

def ytdl_get_version_info(which_one='latest'):
    import urllib2
    if which_one=='latest':
        try:
            newVersion = urllib2.urlopen(YTDL_VERSION_URL).read().strip()
            return newVersion
        except:
            return "0.0"
    else:
        try:

            from youtube_dl.version import __version__
            return __version__
        except Exception as e:
            log('error getting ytdl local version:'+str(e))
            return "0.0"

def update_youtube_dl_core(url,name,action_type):

    import urllib
    import tarfile

    if action_type=='download':
        newVersion=note_ytdl_versions()
        LATEST_URL=YTDL_LATEST_URL_TEMPLATE.format(newVersion)

        profile = xbmc.translatePath(profile_path)  #xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')
        archivePath = os.path.join(profile,'youtube_dl.tar.gz')
        extractedPath = os.path.join(profile,'youtube-dl')
        extracted_core_path=os.path.join(extractedPath,'youtube_dl')


        try:
            if os.path.exists(extractedPath):
                shutil.rmtree(extractedPath, ignore_errors=True)
                update_dl_status('temp files removed')

            update_dl_status('Downloading {0} ...'.format(newVersion))
            log('  From: {0}'.format(LATEST_URL))
            log('    to: {0}'.format(archivePath))
            urllib.urlretrieve(LATEST_URL,filename=archivePath)

            if os.path.exists(archivePath):
                update_dl_status('Extracting ...')

                with tarfile.open(archivePath,mode='r:gz') as tf:
                    members = [m for m in tf.getmembers() if m.name.startswith('youtube-dl/youtube_dl')] #get just the files from the youtube_dl source directory
                    tf.extractall(path=profile,members=members)
            else:
                update_dl_status('Download failed')
        except Exception as e:
            update_dl_status('Error:' + str(e))

        update_dl_status('Updating...')

        if os.path.exists(extracted_core_path):
            log( '  extracted dir exists:'+extracted_core_path)

            if os.path.exists(ytdl_core_path):
                log( '  destination dir exists:'+ytdl_core_path)
                shutil.rmtree(ytdl_core_path, ignore_errors=True)
                update_dl_status('    Old ytdl core removed')
                xbmc.sleep(1000)
            try:
                shutil.move(extracted_core_path, ytdl_core_path)
                update_dl_status('    New core copied')
                xbmc.sleep(1000)
                update_dl_status('Update complete')
                xbmc.Monitor().waitForAbort(2.0)

                setSetting('ytdl_btn_check_version', "")
                setSetting('ytdl_btn_download', "")
            except Exception as e:
                update_dl_status('Failed...')
                log( 'move failed:'+str(e))

    elif action_type=='checkversion':
        note_ytdl_versions()

def note_ytdl_versions():

    setSetting('ytdl_btn_check_version', "checking...")
    ourVersion=ytdl_get_version_info('local')
    setSetting('ytdl_btn_check_version', "{0}".format(ourVersion))

    setSetting('ytdl_btn_download', "checking...")
    newVersion=ytdl_get_version_info('latest')
    setSetting('ytdl_btn_download',      "latest {0}".format(newVersion))

    return newVersion


def update_dl_status(message):
    log(message)
    setSetting('ytdl_btn_download', message)

def setSetting(setting_id, value):
    addon.setSetting(setting_id, value)

def delete_setting_file(url,name,action_type):

    if action_type=='requests_cache':
        file_to_delete=CACHE_FILE+'.sqlite'
    elif action_type=='icons_cache':
        file_to_delete=subredditsPickle
    elif action_type=='subreddits_setting':
        file_to_delete=subredditsFile

    try:
        os.remove(file_to_delete)
        xbmc_notify("Deleting", '..'+file_to_delete[-30:])
    except OSError as e:
        xbmc_notify("Error:", str(e))

def listRelatedVideo(url,name,type_):

    from domains import ClassYoutube
    from domains import parse_reddit_link, build_DirectoryItem_url_based_on_media_type

    match=re.compile( ClassYoutube.regex, re.I).findall( url )
    if match:

        yt=ClassYoutube(url)
        links_dictList=yt.ret_album_list(type_)  #returns a list of dict same as one used for albums
        if links_dictList:


            for _, d in enumerate(links_dictList):
                label=d.get('li_label')
                label2=d.get('li_label2')

                ti=d.get('li_thumbnailImage')
                media_url=d.get('DirectoryItem_url')


                liz=xbmcgui.ListItem(label,label2)
                liz.setInfo( type='video', infoLabels=d['infoLabels'] ) #this tricks the skin to show the plot. where we stored the descriptions
                liz.setArt({"thumb": ti,'icon': ti, "poster":ti, "banner":ti, "fanart":ti, "landscape":ti   })

                ld=parse_reddit_link(media_url)
                DirectoryItem_url, setProperty_IsPlayable, isFolder, _ = build_DirectoryItem_url_based_on_media_type(ld, media_url, '', '', script_to_call="")

                liz.setProperty('IsPlayable', setProperty_IsPlayable)
                xbmcplugin.addDirectoryItem(pluginhandle, DirectoryItem_url, liz, isFolder)

            xbmcplugin.endOfDirectory(handle=pluginhandle,
                              succeeded=True,
                              updateListing=False,   #setting this to True causes the ".." entry to quit the plugin
                              cacheToDisc=True)
        else:
            xbmc_notify('Nothing to list', url)
    else:
        xbmc_notify('cannot identify youtube url', url)

if __name__ == '__main__':
    pass
