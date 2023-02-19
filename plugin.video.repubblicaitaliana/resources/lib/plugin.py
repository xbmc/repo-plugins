import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib.parse

from resources.lib.globals import G


def show_root_menu():
    """ Show the plugin root menu """
    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32001) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'camera.jpg'), 'fanart': G.FANART_PATH})
    add_directory_item({"mode": "camera"}, li_style)

    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32002) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'senato.png'), 'fanart': G.FANART_PATH})
    add_directory_item({"mode": "senato"}, li_style)

    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32003) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'tv.png'), 'fanart': G.FANART_PATH})
    add_directory_item({"mode": "tv"}, li_style)

    li_style = xbmcgui.ListItem('[B]' + G.LANGUAGE(32004) + '[/B]', offscreen=True)
    li_style.setArt({'thumb': os.path.join(G.THUMB_PATH, 'radio.png'), 'fanart': G.FANART_PATH})
    add_directory_item({"mode": "radio"}, li_style)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def add_directory_item(parameters, li, folder=True):
    url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=url, listitem=li, isFolder=folder)


def programmi_camera():
    titolo = 'Camera - Canale Assemblea'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'plugin://plugin.video.youtube/play/?video_id=xXWZzIgbh4Y'
    thumb = 'https://webtv.camera.it/system/events/thumbnails/000/014/843/large/AULAXVIIIC.gif'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Camera - Canale Satellitare'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'plugin://plugin.video.youtube/play/?video_id=Cnjs83yowUM'
    thumb = 'https://webtv.camera.it/assets/thumbs/flash_7/2019/EI_20190520_ch4_14419.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Camera - Canale Sottotitolato'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'plugin://plugin.video.youtube/play/?video_id=4ZJz6alUDfc'
    thumb = 'https://webtv.camera.it/assets/thumbs/flash_7/2019/EI_20190520_ch4_14419.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_senato():
    titolo = 'Senato - Web TV 1'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_001/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Senato - Web TV 2'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_002/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Senato - Web TV 3'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_003/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Senato - Web TV 4'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_004/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Senato - Web TV 5'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_005/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Senato - Web TV 6'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_006/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'Senato - Web TV 7'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://senato-live.morescreens.com/SENATO_1_007/playlist.m3u8'
    thumb = 'https://webtv.senato.it/application/xmanager/projects/leg18/img/webtv/logo_senatoTV.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_tv():
    titolo = 'RaiNews24'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://8e7439fdb1694c8da3a0fd63e4dda518.msvdn.net/rainews1/hls/playlist_mo.m3u8'
    thumb = 'https://www.rainews.it/dl/components/img/svg/RaiNewsBarra-logo.png'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'TgCom24'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://live3.msf.cdn.mediaset.net/content/dash_d0_clr_vos/live/channel(kf)/manifest.mpd'
    thumb = 'https://www.mimesi.com/wp-content/uploads/2017/11/tgcom24.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    liStyle.setProperty('inputstream', 'inputstream.adaptive')
    liStyle.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    liStyle.setMimeType('application/dash+xml')
    liStyle.setContentLookup(False)
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'SkyTg24'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://hlslive-web-gcdn-skycdn-it.akamaized.net/TACT/12221/web/master.m3u8?hdnea=st=1639498341~exp=1702463400~acl=/*~hmac=c3c4c2de19ff0df4b4bb20587ce59af5232eadab2995f445b7506525413805dd'
    thumb = 'https://www.motork.io/it/wp-content/uploads/sites/2/2020/02/skytg24-logo.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'R.Radicale TV'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://video-ar.radioradicale.it/diretta/padtv2/playlist.m3u8'
    thumb = 'https://media.cdnandroid.com/97/fe/ae/31/imagen-radio-radicale-tv-0big.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)
    
    titolo = 'Radio24 TV'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://ilsole24ore-radiovisual.akamaized.net/hls/live/2035302/stream/master.m3u8'
    thumb = 'https://www.radio24.ilsole24ore.com/static/images/radio24_share_600x600.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('video', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def programmi_radio():
    titolo = 'RaiGRParlamento'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://radioparlamento-live.akamaized.net/hls/live/2032597/radioparlamento/radioparlamento/playlist.m3u8'
    thumb = 'http://db.radioline.fr/pictures/radio_994f2bf74254de17bb2c096c0cbf9e21/logo200.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('music', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'RadioRadicale'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://live.radioradicale.it/live.mp3'
    thumb = 'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('music', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'R.Radicale Camera'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://live.radioradicale.it/camera.mp3'
    thumb = 'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('music', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'R.Radicale Senato'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://live.radioradicale.it/senato.mp3'
    thumb = 'https://www.radioradicale.it/sites/all/themes/radioradicale_2014/images/audio-400.png'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('music', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    titolo = 'RadioPopolare'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://livex.radiopopolare.it/radiopop2'
    thumb = 'https://www.radiopopolare.it/wp-content/uploads/2019/08/icon-logo@2x-1.png'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('music', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)
    
    titolo = 'Radio24'
    liStyle = xbmcgui.ListItem(titolo, offscreen=True)
    link = 'https://ilsole24ore-radio.akamaized.net/hls/live/2035301/radio24/playlist.m3u8'
    thumb = 'https://www.radio24.ilsole24ore.com/static/images/radio24_share_600x600.jpg'
    liStyle.setArt({'thumb': thumb, 'fanart': G.FANART_PATH})
    liStyle.setInfo('music', {})
    liStyle.setProperty('isPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=G.PLUGIN_HANDLE, url=link, listitem=liStyle, isFolder=False)

    xbmcplugin.endOfDirectory(handle=G.PLUGIN_HANDLE, succeeded=True)


def run(argv):
    """ Addon entry point """
    G.init_globals(argv)

    if G.MODE == "camera":
        programmi_camera()

    elif G.MODE == "senato":
        programmi_senato()

    elif G.MODE == "tv":
        programmi_tv()

    elif G.MODE == "radio":
        programmi_radio()

    else:
        show_root_menu()
