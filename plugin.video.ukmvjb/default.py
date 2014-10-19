import sys
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmc
import xbmcplugin
import string

db_url='http://874.esy.es/i.php?'
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
xbmcplugin.setContent(addon_handle, 'movies')
name=None
mode = args.get('mode', None)

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def buildMenu(mode, foldername, description, icon, thumbnail):
    url = build_url({'mode': mode, 'foldername': foldername})
    li = xbmcgui.ListItem(description, iconImage=icon, thumbnailImage=thumbnail)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def getUrl(query2):
    req = urllib2.Request(query2)
    req.add_header('User-Agent', 'UK Music Video Jukebox XBMC Addon')
    response = urllib2.urlopen(req)
    content = response.read()
    response.close()
    return content

def listArtists(query):
    db_request = db_url + query
    content = getUrl(db_request)
    spl = content.split("|")
    for i in range(1, len(spl), 1):
        if i%2 != 0:
            artist = spl[i]
        else:
            #img = img_url+"/a/"+spl[i]            
            img = spl[i]            
            buildMenu(mode="Artist", foldername=artist, description=artist, icon=img, thumbnail=img);

def listSongs(query):
    db_request = db_url + query
    content = getUrl(db_request)
    spl = content.split("|")
    for i in range(1, len(spl), 1):
        if i%3 == 1:
            id = spl[i]
        if i%3 == 2:
            artist_year = spl[i]
        if i%3 == 0:
            song = spl[i]
            title = "[COLOR blue]"+artist_year+"[/COLOR] | [COLOR red]"+song+"[/COLOR]"
            img="http://img.youtube.com/vi/"+id+"/0.jpg"
            buildMenu(mode="Song", foldername=id, description=title, icon=img, thumbnail=img);

def listTags(query):
    db_request = db_url + query
    content = getUrl(db_request)
    spl = content.split("|")
    for i in range(1, len(spl), 1):
        if i%2 == 1:
            tag = spl[i]
        if i%2 == 0:
            img = spl[i]
            buildMenu(mode="Tag_"+tag, foldername=tag, description=tag, icon=img, thumbnail=img);

def listYears(query):
    db_request = db_url + query
    content = getUrl(db_request)
    spl = content.split("|")
    for i in range(1, len(spl), 1):
        year = spl[i]
        buildMenu(mode="Year_"+year, foldername=year, description=year, icon="icon.png", thumbnail="thumbnail.png");
        
if mode is None:
    
    buildMenu(mode="folder4", foldername="Search", description="Search for a Song", icon="icon.png", thumbnail="thumbnail.png");
    buildMenu(mode="folder5", foldername="Latest", description="Latest videos", icon="icon.png", thumbnail="thumbnail.png");
    buildMenu(mode="folder1", foldername="Artist", description="Browse by Artist", icon="icon.png", thumbnail="thumbnail.png");
    buildMenu(mode="folder2", foldername="Year", description="Browse by Year", icon="icon.png", thumbnail="thumbnail.png");
    buildMenu(mode="folder3", foldername="Tag", description="Browse Collections", icon="icon.png", thumbnail="thumbnail.png");
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder1':
    foldername = args['foldername'][0]
    buildMenu(mode="A-Z_1", foldername=1, description="0-9", icon="icon.png", thumbnail="thumbnail.png");
    alphabets = string.ascii_uppercase
    for i in alphabets:
        buildMenu(mode="A-Z_"+i, foldername=i, description=i, icon="icon.png", thumbnail="thumbnail.png");
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0][:3] == 'A-Z':
    foldername = args['foldername'][0]
    letter=mode[0][-1:]
    listArtists(query='a='+letter)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'Artist':
    foldername = args['foldername'][0]
    song=urllib.quote_plus(foldername)
    listSongs(query='a='+song)
    xbmcplugin.endOfDirectory(addon_handle)
    

elif mode[0] == 'Song':
    foldername = args['foldername'][0]
    xbmc.Player().play('plugin://plugin.video.youtube/?path=root/video&action=play_video&videoid='+foldername)
    
elif mode[0] == 'folder2':
    # browse by year
    foldername = args['foldername'][0]
    listYears(query='y=1')
    xbmcplugin.endOfDirectory(addon_handle)


elif mode[0][:4] == 'Year':
    foldername = args['foldername'][0]
    year=foldername
    listSongs(query='y='+year)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder3':
    # Display all tags
    foldername = args['foldername'][0]
    listTags(query='t=1')
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0][:3] == 'Tag':
    # Show songs for selected tag
    foldername = args['foldername'][0]
    tag=urllib.quote_plus(foldername)
    listSongs(query='t='+tag)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder4':
    # Display Search menu
    foldername = args['foldername'][0]
    buildMenu(mode="search", foldername="artist", description="Search by Artist name", icon="icon.png", thumbnail="thumbnail.png");
    buildMenu(mode="search", foldername="song", description="Search by Song name", icon="icon.png", thumbnail="thumbnail.png");
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'search':
    # Search videos
    search_type = args['foldername'][0]
    keyboard = xbmc.Keyboard('', name, False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
        if len(query) > 0:
            query=urllib.quote_plus(query)
            listSongs(query="s="+query+"&type="+search_type)
            xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder5':
    # Display latest songs
    foldername = args['foldername'][0]
    listSongs(query='l=1')
    xbmcplugin.endOfDirectory(addon_handle)
