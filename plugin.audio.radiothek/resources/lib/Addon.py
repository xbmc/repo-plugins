from resources.lib.RadioThek import *
import os
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import sys


def get_media_path():
    settings = xbmcaddon.Addon()
    basepath = settings.getAddonInfo('path')
    img_path = os.path.join(basepath, "resources")
    return os.path.join(img_path, "media")


def add_directory_item(directory, mode, pluginhandle):
    parameters = {"link": directory.link.encode('utf-8'), "mode": mode}
    u = sys.argv[0] + '?' + url_encoder(parameters)
    liz = xbmcgui.ListItem(directory.title)
    info_labels = {
        "Title": directory.title,
        "Plot": directory.description
    }
    liz.setInfo(type="Video", infoLabels=info_labels)

    if directory.logo:
        channel_icon_base = get_media_path()
        logo_path = os.path.join(channel_icon_base, directory.logo)
        if not directory.thumbnail:
            directory.thumbnail = logo_path
        liz.setArt({'thumb': logo_path, 'icon': logo_path, 'poster': directory.thumbnail, 'banner': directory.thumbnail, 'fanart': directory.backdrop})
    else:
        liz.setArt({'thumb': directory.thumbnail, 'icon': directory.thumbnail, 'poster': directory.thumbnail, 'banner': directory.thumbnail, 'fanart': directory.backdrop})
    liz.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=liz, isFolder=True)


def add_directory(title, banner, backdrop, logo, description, link, mode, pluginhandle):
    parameters = {"link": link.encode('utf-8'), "mode": mode}
    u = sys.argv[0] + '?' + url_encoder(parameters)
    liz = xbmcgui.ListItem(title)
    info_labels = {
        "Title": title,
        "Plot": description
    }
    liz.setInfo(type="Video", infoLabels=info_labels)

    if not banner:
        banner = logo
    if logo:
        channel_icon_base = get_media_path()
        logo_path = os.path.join(channel_icon_base, logo)
        liz.setArt({'thumb': logo_path, 'icon': logo_path, 'poster': banner, 'banner': banner, 'clearlogo': banner, 'clearart': banner, 'fanart': backdrop, 'landscape': backdrop})
    else:
        liz.setArt({'thumb': banner, 'icon': banner, 'poster': banner, 'banner': banner, 'clearlogo': banner, 'clearart': banner, 'fanart': backdrop, 'landscape': backdrop})
    liz.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=liz, isFolder=True)


def get_translation(msgid, default=False):
    settings = xbmcaddon.Addon()
    translation = settings.getLocalizedString
    try:
        if not translation(msgid+100) and default:
            return default
        return translation(msgid+100).encode('utf-8')
    except:
        return translation(msgid+100)


def add_episode(episode, pluginhandle):
    if not episode.hidden:
        if episode.artist:
            generated_title = "[%s] %s - %s" % (episode.time, episode.artist, episode.trackname)
        elif episode.time:
            generated_title = "[%s] %s" % (episode.time, episode.title)
        else:
            generated_title = episode.title
        parameters = {"link": episode.files[0], "mode": "play", "label": generated_title.encode('utf-8')}
        u = sys.argv[0] + '?' + url_encoder(parameters)
        liz = xbmcgui.ListItem(label=generated_title.encode('utf-8'))
        liz.setInfo(type="Music", infoLabels={"mediatype": 'music'})

        liz.setProperty('Music', 'true')
        liz.setProperty('mimetype', 'audio/mpeg')
        if episode.duration:
            liz.setInfo('video', {'duration': episode.duration/1000})

        info_labels = {
            "Title": generated_title,
            "Plot": episode.description,
        }
        if episode.item_type == 'BroadcastItem' and episode.artist:
            info_labels['Plot'] = "[B]%s:[/B] [COLOR blue]%s[/COLOR] \n[B]%s:[/B] [COLOR blue]%s[/COLOR]\n\n[LIGHT]%s[/LIGHT]" % (get_translation(30003, 'Artist'), episode.artist, get_translation(30004, 'Track'), episode.trackname, info_labels['Plot'])

        liz.setInfo(type="Video", infoLabels=info_labels)
        if episode.thumbnail:
            liz.setArt({'thumb': episode.thumbnail, 'icon': episode.thumbnail})
        else:
            liz.setArt({'thumb': episode.logo, 'icon': episode.logo})
        liz.setProperty('IsPlayable', 'true')
        xbmcplugin.addSortMethod(handle=pluginhandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.setContent(pluginhandle, "music")
        xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=liz, isFolder=False)


def add_stream(episode, pluginhandle):
    if episode.item_type == 'Broadcast' or episode.item_type == 'BroadcastItem':
        generated_title = "%s | %s" % (episode.time, episode.title)
    else:
        generated_title = episode.title

    parameters = {"link": episode.files[0], "mode": "play", "label": generated_title.encode('utf-8')}
    u = sys.argv[0] + '?' + url_encoder(parameters)
    liz = xbmcgui.ListItem(label=generated_title.encode('utf-8'))

    if episode.logo:
        channel_icon_base = get_media_path()
        logo_path = os.path.join(channel_icon_base, episode.logo)
        liz.setArt({'thumb': logo_path, 'icon': logo_path, 'poster': episode.thumbnail, 'banner': episode.thumbnail, 'clearlogo': episode.thumbnail, 'clearart': episode.thumbnail})
    else:
        liz.setArt({'thumb': episode.thumbnail, 'icon': episode.thumbnail, 'poster': episode.thumbnail, 'banner': episode.thumbnail, 'clearlogo': episode.thumbnail, 'clearart': episode.thumbnail})

    liz.setProperty('Music', 'true')
    liz.setProperty('mimetype', 'audio/mpeg')

    info_labels = {
        "Title": generated_title,
        "Plot": episode.description,
    }
    if episode.item_type == 'BroadcastItem' and episode.artist:
        info_labels['Plot'] = "[B]%s:[/B] [COLOR blue]%s[/COLOR] \n[B]%s:[/B] [COLOR blue]%s[/COLOR]\n\n[LIGHT]%s[/LIGHT]" % (get_translation(30003, 'Artist'), episode.artist, get_translation(30004, 'Track'), episode.trackname, info_labels['Plot'])

    liz.setInfo(type="Video", infoLabels=info_labels)
    liz.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=liz, isFolder=False)


def get_navigation(pluginhandle):
    add_directory(get_translation(30005, "Highlights"), "", "", "", "", "", "highlights", pluginhandle)
    add_directory(get_translation(30006, "Broadcasts"), "", "", "", "", "", "broadcast", pluginhandle)
    add_directory(get_translation(30007, "Podcasts"), "", "", "", "", "", "podcasts", pluginhandle)
    add_directory(get_translation(30008, "Topics"), "", "", "", "", "", "tags", pluginhandle)
    add_directory(get_translation(30009, "Archive"), "", "", "", "", "", "archive", pluginhandle)
    add_directory(get_translation(30010, "Live"), "", "", "", "", "", "live", pluginhandle)
    add_directory(get_translation(30011, "Search"), "", "", "", "", "", "search", pluginhandle)
    add_directory(get_translation(30012, "Missed a show?"), "", "", "", "", "", "missed_show", pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)


def get_input():
    kb = xbmc.Keyboard()
    kb.setDefault('')
    kb.setHeading(get_translation(30013, 'Enter a search phrase ...'))
    kb.setHiddenInput(False)
    kb.doModal()
    if kb.isConfirmed():
        search_term = kb.getText()
        searchHistoryPush(search_term)
        return search_term
    else:
        return


def searchHistoryPush(title):
    if not title:
        return
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.audio.radiothek")
    json_file = os.path.join(addonUserDataFolder, 'searchhistory.json')
    title = unquote_url(title)
    title = title.replace("+", " ").strip()
    # check if file exists
    if os.path.exists(json_file):
        # check if file already has an entry
        if os.path.getsize(json_file) > 0:
            # append value to JSON File
            data = getJsonFile(json_file)
            data.append(title)
            saveJsonFile(data, json_file)
        # found empty file - writing first record
        else:
            data = [title]
            saveJsonFile(data, json_file)
    # create json file
    else:
        if not os.path.exists(addonUserDataFolder):
            os.makedirs(addonUserDataFolder)
        data = [title]
        saveJsonFile(data, json_file)


def searchHistoryGet():
    addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/plugin.audio.radiothek")
    json_file = os.path.join(addonUserDataFolder, 'searchhistory.json')
    if os.path.exists(json_file):
        if os.path.getsize(json_file) > 0:
            data = getJsonFile(json_file)
            return data
    return []


def saveJsonFile(data, file):
    with open(file, 'w') as data_file:
        data_file.write(json.dumps(data))
    data_file.close()


def getJsonFile(file):
    with open(file, 'r') as data_file:
        data = json.load(data_file)
    return data


def getSearchHistory(pluginhandle):
    history = searchHistoryGet()
    for search_query in reversed(history):
        if search_query.strip() != '':
            add_directory(search_query, "", "", "", "", search_query, "search_detail", pluginhandle)


def getAudioQuality():
    quality_list = ['q1a', 'q2a', 'q3a', 'q4a', 'qxb']
    audio_protocol = getAudioProtocol()
    if audio_protocol == 'shoutcast':
        quality_index = int(xbmcaddon.Addon().getSetting('audioQuality'))
    else:
        quality_index = int(xbmcaddon.Addon().getSetting('audioQualityHLS'))

    try:
        return quality_list[quality_index]
    except:
        return quality_list[0]


def getAudioProtocol():
    if xbmcaddon.Addon().getSetting('useHlsLive') == 'true':
        return 'hls'
    return 'shoutcast'


def main(pluginhandle):
    params = parameters_string_to_dict(sys.argv[2])
    mode = params.get('mode')
    link = unquote_url(params.get('link'))

    if mode is None:
        get_navigation(pluginhandle)
    elif mode == 'broadcast':
        list_items = api.get_broadcast()
        for list_item in list_items:
            add_directory_item(list_item, "broadcast_detail", pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'podcasts':
        list_items = api.get_podcasts()
        for list_item in list_items:
            add_directory_item(list_item,  "podcast_detail", pluginhandle)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'highlights':
        list_items = api.get_highlights()
        for list_item in list_items:
            add_directory_item(list_item, "broadcast_detail", pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'tags':
        list_items = api.get_tags()
        for list_item in list_items:
            add_directory_item(list_item,  "tags_detail", pluginhandle)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'archive':
        list_items = api.get_archive()
        for list_item in list_items:
            add_directory_item(list_item, "podcast_detail", pluginhandle)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'live':
        episodes = api.get_livestream()
        for episode in episodes:
            add_stream(episode, pluginhandle)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'search':
        add_directory(get_translation(30014, "Search ..."), "", "", "", "", "", "search_detail", pluginhandle)
        getSearchHistory(pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'search_detail':
        if not link:
            query = get_input()
        else:
            query = link
        if query:
            list_items = api.get_search(query)
            for list_item in list_items:
                add_directory_item(list_item, "broadcast_detail", pluginhandle)
            xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'podcast_detail':
        episodes = api.get_podcast_details(link)
        for episode in episodes:
            add_episode(episode, pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'tags_detail':
        list_items = api.get_tag_details(link)
        for list_item in list_items:
            add_directory_item(list_item, "broadcast_detail", pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'broadcast_detail':
        broadcasts = api.get_broadcast_details(link)
        for broadcast in broadcasts:
            add_episode(broadcast, pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'missed_show':
        station_list_keys = list(api.station_nice.keys())
        station_list = list(api.station_nice.values())
        dialog = xbmcgui.Dialog()
        station_selected = dialog.contextmenu(station_list)
        station_code = station_list_keys[station_selected]
        if station_code:
            day_list_items = api.get_day_selection(station_code)
            if day_list_items:
                for day_item in day_list_items:
                    add_directory_item(day_item, "missed_show_detail", pluginhandle)
            else:
                add_directory(get_translation(30015, "No items for this station"), "", "", "", "", "", "missed_show", pluginhandle)
            xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'missed_show_detail':
        list_items = api.get_day_selection_details(link)
        for list_item in list_items:
            add_directory_item(list_item, "broadcast_detail", pluginhandle)
        xbmcplugin.endOfDirectory(pluginhandle)
    elif mode == 'play':
        play_link = "%s|User-Agent=%s" % (link, api.user_agent)
        title = params.get('label')
        play_item = xbmcgui.ListItem(label=title, path=play_link)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)
        xbmcplugin.endOfDirectory(pluginhandle)

settings = xbmcaddon.Addon()
translation_ref = settings.getLocalizedString
resource_path = get_media_path()
protocol = getAudioProtocol()
quality = getAudioQuality()
api = RadioThek(resource_path, translation_ref, protocol, quality)
