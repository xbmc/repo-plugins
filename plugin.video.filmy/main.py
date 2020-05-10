import sys
import xbmcgui
import xbmcplugin
import requests
from urlparse import parse_qsl

__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

channels = eval(requests.get(url='https://filmy.ml/app/channels.js').text.split("var channels = ")[1].split(";")[0].replace('title', '"title"').replace('description', '"description"').replace('previewImage', '"previewImage"').replace('liveStream', '"liveStream"'))

def list_videos():
    listing = []
    for video in channels:
        list_item = xbmcgui.ListItem(label=video['title'], thumbnailImage=video['previewImage'])
        list_item.setProperty('fanart_image', video['previewImage'])
        list_item.setInfo('video', {'title': video['title'], 'genre': 'Filmy'})
        list_item.setProperty('IsPlayable', 'true')
        url = '{0}?action=play&video={1}'.format(__url__, video['liveStream'])
        is_folder = False
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(__handle__)

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(__handle__, True, listitem=play_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        if params['action'] == 'play':
            play_video(params['video'])
    else:
        list_videos()

if __name__ == '__main__':
    router(sys.argv[2])
