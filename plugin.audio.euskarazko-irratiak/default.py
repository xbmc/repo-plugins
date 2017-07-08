# https://docs.python.org/2.7/
import os
import sys
import urllib
import urlparse
import operator
# http://mirrors.kodi.tv/docs/python-docs/
import xbmcaddon
import xbmcgui
import xbmcplugin

import resources.lib.basque_online_radios as basque_online_radios
import resources.lib.arrosa_scraper as arrosa_scraper
import resources.lib.eitb_nahieran_client as eitb_nahieran_client
import resources.lib.etzi_pm_client as etzi_pm_client

ADDONID = 'plugin.audio.euskarazko-irratiak'
ADDON = xbmcaddon.Addon(ADDONID)

def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)

def list_streams(streams):
    stream_list = []

    # iterate over the contents of the dictionary songs to build the list
    for stream in streams:
        # create a list item using the stream's name for the label
        li = xbmcgui.ListItem(label=stream['name'])
        # set the thumbnail image
        li.setArt({'thumb': stream['logo']})
        # set the list item to playable
        li.setProperty('IsPlayable', 'true')
        # build the plugin url for Kodi
        url = build_url({'mode': 'stream', 'url': stream['url'], 'title': stream['name']})
        # add the current list item to a list
        stream_list.append((url, li, False))

    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, stream_list, len(stream_list))

    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)

def play_audio(url):
    # set the path of the stream to a list item
    play_item = xbmcgui.ListItem(path=url)

    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

def list_podcast_radios(radios):
    radio_list = []

    # iterate over the contents of the list of radios
    for radio in sorted(radios, key=operator.itemgetter('name')):
        url = build_url({'mode': 'podcasts-radio', 'foldername': radio['name'], 'url': radio['url'], 'name': radio['name']})
        li = xbmcgui.ListItem(radio['name'], iconImage='DefaultFolder.png')
        radio_list.append((url, li, True))

    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, radio_list, len(radio_list))

    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)

def list_podcast_programs(programs):
    program_list = []

    # iterate over the contents of the list of programs
    for program in programs:
        url = build_url({'mode': 'podcasts-radio-program', 'foldername': urllib.quote(program['name'].encode('utf8')), 'url': program['url'], 'name': urllib.quote(program['name'].encode('utf8')), 'radio': program['radio']})
        li = xbmcgui.ListItem(program['name'], iconImage='DefaultFolder.png')
        program_list.append((url, li, True))

    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, program_list, len(program_list))

    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)

def list_podcast_audios(audios):
    audio_list = []

    # iterate over the audios to build the list
    for audio in audios:
        # create a list item using the audio's title for the label
        li = xbmcgui.ListItem(audio['date'] + " - " + audio['title'])

        if 'image' in audio:
            # set the thumbnail image
            li.setArt({'thumb': audio['image']})

        # set the list item to playable
        li.setProperty('IsPlayable', 'true')

        # build the plugin url for Kodi
        url = build_url({'mode': 'stream', 'url': audio['url'].encode('utf8'), 'title': audio['date'] + " - " + urllib.quote(audio['title'].encode('utf8'))})

        # add the current list item to a list
        audio_list.append((url, li, False))

    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, audio_list, len(audio_list))

    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)

def show_main_menu():
    # Create menu directory for the live radios
    url = build_url({'mode': 'streams', 'foldername': ADDON.getLocalizedString(30001)})
    li = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    # Create menu directory for the podcasts
    url = build_url({'mode': 'podcasts-radios', 'foldername': ADDON.getLocalizedString(30002)})
    li = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

def main():
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)

    # initial launch of add-on
    if mode is None:
        show_main_menu()

    # the user wants to see the list of streams
    elif mode[0] == 'streams':
        # get the JSON
        streams = basque_online_radios.get_streams()

        # display the list of streams in Kodi
        list_streams(streams)

    # a stream from the list has been selected
    elif mode[0] == 'stream':
        # pass the url of the stream to play_audio
        play_audio(args['url'][0])

    # the user wants to see the list of radios that have podcasts
    elif mode[0] == 'podcasts-radios':
        # get the list of radios from Arrosa irrati sarea that have podcasts
        podcasts = arrosa_scraper.get_radios()

        # append the list of radios from EITB Nahieran that have podcasts in Basque language
        podcasts = podcasts + eitb_nahieran_client.get_radios()

        # append the list of radios from Etzi.pm
        podcasts = podcasts + etzi_pm_client.get_radios()

        # display the list of radios that have podcasts
        list_podcast_radios(podcasts)

    # the user wants to see the list of programs of a radio
    elif mode[0] == 'podcasts-radio':
        radio_name = args['name'][0]

        # if the selected radio is from EITB Nahieran
        if eitb_nahieran_client.is_in_list_of_radios(radio_name):
            programs = eitb_nahieran_client.get_programs(radio_name)
        # else if the selected radio is from Etzi.pm
        elif etzi_pm_client.is_in_list_of_radios(radio_name):
            programs = etzi_pm_client.get_programs()
        # else is from Arrosa irrati sarea
        else:
            programs = arrosa_scraper.get_programs(args['url'][0], radio_name)

        # display the list of programs of the selected radio
        list_podcast_programs(programs)

    # the user wants to see the list of audios of a program
    elif mode[0] == 'podcasts-radio-program':
        radio_name = args['radio'][0]
        program_url = args['url'][0]

        # if the selected radio is from EITB Nahieran
        if eitb_nahieran_client.is_in_list_of_radios(radio_name):
            audios = eitb_nahieran_client.get_audios(program_url)
        # else if the selected radio is from Etzi.pm
        elif etzi_pm_client.is_in_list_of_radios(radio_name):
            audios = etzi_pm_client.get_audios(program_url)
        # else is from Arrosa irrati sarea
        else:
            audios = arrosa_scraper.get_audios(program_url)

        # display the list of audios of the selected program
        list_podcast_audios(audios)

    # the user selected an audio from the list
    elif mode[0] == 'stream':
        # pass the url of the stream to play_audio
        play_audio(args['url'][0])

if __name__ == '__main__':
    addon_handle = int(sys.argv[1])
    main()
