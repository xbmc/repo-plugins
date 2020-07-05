from __future__ import unicode_literals
import urllib2
import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import re
from BeautifulSoup import BeautifulSoup as bs
import os
import datetime
import json
import sqlite3


db_dir = xbmc.translatePath("special://database")
db_path = os.path.join(db_dir, 'folders.db')

addonID=xbmcaddon.Addon().getAddonInfo("id")

db_dir = xbmc.translatePath("special://profile/addon_data/"+addonID)
new_db_path = os.path.join(db_dir, 'youtube_channels.db')

try:
    import shutil
    if os.path.isfile('folders.db'):
        shutil.copyfile('folders.db', db_path)
        os.remove('folders.db')
    if os.path.isfile(db_path):
        shutil.move(db_path,new_db_path)

        
except:
    pass

db=sqlite3.connect(new_db_path)



my_addon = xbmcaddon.Addon()
enable_playlists = my_addon.getSetting('enable_playlists')

YOUTUBE_API_KEY = my_addon.getSetting('youtube_api_key')

categories_list=[['Autos and vehicles','http://vidstatsx.com/youtube-top-100-most-viewed-autos-vehicles'],['Comedy','http://vidstatsx.com/youtube-top-100-most-viewed-comedy'],
            ['Education','http://vidstatsx.com/youtube-top-100-most-viewed-education'],['Entertainment','http://vidstatsx.com/youtube-top-100-most-viewed-entertainment'],
            ['Film & Animation','http://vidstatsx.com/youtube-top-100-most-viewed-film-animation'],['Games & gaming','http://vidstatsx.com/youtube-top-100-most-viewed-games-gaming'],
            ['How To & Style','http://vidstatsx.com/youtube-top-100-most-viewed-how-to-style'],['Music','http://vidstatsx.com/youtube-top-100-most-viewed-music'],
            ['News & Politics','http://vidstatsx.com/youtube-top-100-most-viewed-news-politics'],['Non profit & Activism','http://vidstatsx.com/youtube-top-100-most-viewed-nonprofit-activism'],
            ['People & Vlogs','http://vidstatsx.com/youtube-top-100-most-viewed-people-vlogs'],['Pets & Animals','http://vidstatsx.com/youtube-top-100-most-viewed-pets-animals'],
            ['Science & Tech','http://vidstatsx.com/youtube-top-100-most-viewed-science-tech'],['Shows','http://vidstatsx.com/youtube-top-100-most-viewed-shows'],
            ['Sports','http://vidstatsx.com/youtube-top-100-most-viewed-sports'],['Travel & Events','http://vidstatsx.com/youtube-top-100-most-viewed-travel-events']]



def import_from_old_addon():
    old_addonID='plugin.video.youtube.channels'
    channelFile=xbmc.translatePath("special://profile/addon_data/"+old_addonID+"/youtube.channels")


    if os.path.exists(channelFile):
        cats = []
        fh = open(channelFile, 'r')
        numb=0

        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Youtube Channels', 'Importing channels...')
        
        for line in fh:
            try:
                pDialog.update(75, 'Importing channels...')

                
                match=re.compile('(.+?)#(.+?)#(.+?)#(.+?)#', re.DOTALL).findall(line)
                
                channel_username=match[0][1]
                folder=match[0][3]
                channel_info=search_channel_by_username(channel_username)

                channel_name=channel_info[0]
                
                channel_id=channel_info[1]
                thumb=channel_info[2]


                folders=get_folders()
                if folder=="NoCat":
                    if 'Other' not in folders:
                        add_folder('Other')
                        folder='Other'
                    
                elif folder not in folders:
                    add_folder(folder)
                    
                channel_id=get_channel_id(channel_username)
                add_channel(folder,channel_name,channel_id,thumb)
                numb+=1
            except:
                pass
        pDialog.update(100, 'Importing channels...')
        pDialog.close()
        
        xbmcgui.Dialog().ok("Youtube Channels", "%s channels imported."%numb)
               
              
        fh.close()







def list_categories():
    for i in range (len(categories_list)):
        url = build_url({'mode': 'open_category', 'foldername': '%s'%categories_list[i][0], 'site': '%s'%categories_list[i][1]})
        li = xbmcgui.ListItem('%s'%categories_list[i][0], iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/folder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li,isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
    
def open_category(site):

    my_addon = xbmcaddon.Addon()
    num = int(my_addon.getSetting('result_number_channels_cat'))
    read=read_url(site)
    channels=[]
    soup=bs(read)
    
    tag=site.replace('http://vidstatsx.com/','')
    table=soup.find('table',{'id':'%s'%tag}).find('tbody')
    items=table.findAll('tr')
    for i in range(num):
        channel_name=items[i].find('td').find('a').getText()
        if '#' not in channel_name:
            channel_username=items[i].find('td')['id']
            
            channels+=[channel_username]
    for i in range(len(channels)):
        channel=search_channel_by_username(channels[i])
        if channel!='not found':
            url = build_url({'mode': 'open_channel', 'foldername': '%s'%str(channel[1]), 'page':'1'})
            li = xbmcgui.ListItem('%s'%channel[0], iconImage='%s'%channel[2])


            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)
        else:
            pass


    xbmcplugin.endOfDirectory(addon_handle)



def delete_database():
    
    with db:
    
        cur = db.cursor()
         
    
        cur.execute("drop table if exists Folders")
        cur.execute("drop table if exists Channels")
        cur.close()


    return

def read_url(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:33.0) Gecko/20100101 Firefox/33.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link.decode('utf-8')

def init_database():
    
    with db:
    
        cur = db.cursor()    
        cur.execute("begin") 
        cur.execute("create table if not exists Folders (Name TEXT, Channel TEXT)")
        cur.execute("create table if not exists Channels (Folder TEXT, Channel TEXT, Channel_ID TEXT,thumb TEXT)")
        db.commit()
        cur.close()
    return
def get_folders():
    init_database()
    #db=sqlite3.connect('folders.db')

    cur = db.cursor()
    cur.execute("begin")     
    cur.execute("SELECT Name FROM Folders")
    
    rows = cur.fetchall()
    cur.close()
    folders=[]
    for i in range (len(rows)):
        folder=rows[i]
        folders+=folder
    

    
    return folders

def add_folder(foldername):
    init_database()

    #db=sqlite3.connect('folders.db')

    cur = db.cursor()  
    cur.execute("begin")   
    cur.execute('INSERT INTO Folders(Name) VALUES ("%s");'%foldername)
    db.commit()
    cur.close()
    

def remove_folder(name):
    #DELETE FROM COMPANY WHERE ID = 7

    

    cur = db.cursor()  
    cur.execute("begin")  
    cur.execute("DELETE FROM Folders WHERE Name = ?;",(name,))
    cur.execute("DELETE FROM Channels WHERE Folder = ?;",(name,))

    db.commit()
    cur.close()


def get_channels(foldername):
    

    cur = db.cursor()    
    cur.execute("begin")  

    cur.execute("SELECT Channel,Channel_ID,thumb FROM Channels WHERE Folder=?",(foldername,))

    rows = cur.fetchall()
    cur.close()
    channels=[]
    
    
    for i in range (len(rows)):
        channel=list(rows[i])
        channels+=[channel]
    return channels

def get_channel_id_from_uploads_id(uploads_id):
    url='https://www.googleapis.com/youtube/v3/playlists?part=snippet&id=%s&key=%s'%(uploads_id,YOUTUBE_API_KEY)
    read=read_url(url)
    decoded_data=json.loads(read)
    channel_id=decoded_data['items'][0]['snippet']['channelId']

    return channel_id
    



def add_channel(foldername,channel_name,channel_id,thumb):
    cur = db.cursor() 
    cur.execute("begin")   
    try:
        cur.execute("DELETE FROM Channels WHERE Folder = ? AND Channel = ? AND Channel_ID = ? AND thumb = ?",(foldername,channel_name,channel_id,thumb))
    except:
        pass
  
     
    cur.execute("INSERT INTO Channels(Folder,Channel,Channel_ID,thumb) VALUES (?,?,?,?);",(foldername,channel_name,channel_id,thumb))
    db.commit()
    cur.close()

def remove_channel(id):
    
    cur = db.cursor()    
    cur.execute("begin")   

    cur.execute("DELETE FROM Channels WHERE Channel_ID = ?;",(id,))

    db.commit()
    cur.close()


def search_channel(channel_name):

    my_addon = xbmcaddon.Addon()
    result_num = my_addon.getSetting('result_number_channels')

    
    req_url='https://www.googleapis.com/youtube/v3/search?q=%s&type=channel&part=snippet&maxResults=%s&key=%s'%(channel_name.replace(' ','%20'),str(result_num),YOUTUBE_API_KEY)
    #req_url='https://www.googleapis.com/youtube/v3/search?q=%stype=channel&maxResults=20&part=snippet&key='%channel_name.replace(' ','%20') + YOUTUBE_API_KEY
    read=read_url(req_url)
    decoded_data=json.loads(read)
    listout=[]
    
    
    for x in range(0, len(decoded_data['items'])):
        title=decoded_data['items'][x]['snippet']['title']
        thumb=decoded_data['items'][x]['snippet']['thumbnails']['high']['url']
        channel_id=decoded_data['items'][x]['snippet']['channelId']
        req1='https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id=%s&key=%s'%(channel_id,YOUTUBE_API_KEY)
        read2=read_url(req1)
        decoded_data2=json.loads(read2)
        try:
            channel_uplid=decoded_data2['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            listout.append([title,channel_uplid,thumb,channel_id])
        except:
            pass

    return listout

def search_channel_by_username(username):
    req_url='https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forUsername=%s&key=%s'%(username,YOUTUBE_API_KEY)
    read=read_url(req_url)
    decoded_data=json.loads(read)
    listout=[]

    if decoded_data['pageInfo']['totalResults']==1:
        channel_id=decoded_data['items'][0]['id']
        uploads_id=decoded_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        req2='https://www.googleapis.com/youtube/v3/channels?part=snippet&id=%s&key=%s'%(channel_id,YOUTUBE_API_KEY)
        read=read_url(req2)
        decoded_data=json.loads(read)
        
        title=decoded_data['items'][0]['snippet']['title']
        thumb=decoded_data['items'][0]['snippet']['thumbnails']['high']['url']
        channel_uplid=uploads_id
        listout.append(title)
        listout.append(channel_uplid)
        listout.append(thumb)
        listout.append(channel_id)
        return listout
    elif decoded_data['pageInfo']['totalResults']==0:
        return 'not found'

def get_channel_id(channel_username):
    req_url='https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forUsername=%s&key=%s'%(channel_username,YOUTUBE_API_KEY)
    read=read_url(req_url)
    decoded_data=json.loads(read)
    
    if decoded_data['pageInfo']['totalResults']==1:
        uploads_id=decoded_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return uploads_id

    elif decoded_data['pageInfo']['totalResults']==0:
        return 'not found'


def get_latest_from_channel(channel_id, page):

    my_addon = xbmcaddon.Addon()
    result_num = my_addon.getSetting('result_number')

    if page=='1':
        req_url='https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=%s&playlistId=%s&key='%(str(result_num),channel_id)+YOUTUBE_API_KEY
    else:
        req_url='https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&pageToken=%s&maxResults=%s&playlistId=%s&key='%(page,str(result_num),channel_id)+YOUTUBE_API_KEY
    read=read_url(req_url)
    decoded_data=json.loads(read)
    listout=[]
    try:
        next_page=decoded_data['nextPageToken']
    except:
        next_page='1'
    listout.append(next_page)
    for x in range(0, len(decoded_data['items'])):
        title=decoded_data['items'][x]['snippet']['title']
        video_id=decoded_data['items'][x]['snippet']['resourceId']['videoId']
        thumb=decoded_data['items'][x]['snippet']['thumbnails']['high']['url']
        desc=decoded_data['items'][x]['snippet']['description']
        listout.append([title,video_id,thumb,desc])
    return listout

               
def get_chart_50():
    my_addon = xbmcaddon.Addon()
    num = int(my_addon.getSetting('result_number_channels_cat'))
    
    site='http://vidstatsx.com/youtube-top-100-most-viewed'
    read=read_url(site)
    channels=[]
    soup=bs(read)
    table=soup.find('table',{'id':'youtube-top-100-most-viewed'}).find('tbody')
    items=table.findAll('tr')
    for i in range(num):
        channel_name=items[i].find('td').find('a').getText()
        if '#' not in channel_name:
            channel_username=items[i].find('td')['id']
            #channel=search_channel_by_username(channel_username)

            channels+=[channel_username]
    for i in range(len(channels)):
        channel=search_channel_by_username(channels[i])
        if channel!='not found':
         
            url = build_url({'mode': 'open_channel', 'foldername': '%s'%str(channel[1]), 'page':'1'})
            li = xbmcgui.ListItem('%s'%channel[0], iconImage='%s'%channel[2])


            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)
        else:
            pass


    xbmcplugin.endOfDirectory(addon_handle)


def get_playlists(channelID,page):
    if page=='1':
        url='https://www.googleapis.com/youtube/v3/playlists?part=snippet&channelId=%s&maxResults=10&key=%s'%(channelID,YOUTUBE_API_KEY)
    else:#
        url='https://www.googleapis.com/youtube/v3/playlists?part=snippet&channelId=%s&maxResults=10&pageToken=%s&key=%s'%(channelID,page,YOUTUBE_API_KEY)
    read=read_url(url)
    decoded_data=json.loads(read)
    playlists=[]
    try:
        next_page=decoded_data['nextPageToken']
    except:
        next_page='1'
    playlists.append(next_page)
    for i in range(len(decoded_data['items'])):
        if decoded_data['items'][i]['kind']=='youtube#playlist':
            playlist_id=decoded_data['items'][i]['id']
            playlist_name=decoded_data['items'][i]['snippet']['title']
            thumb=decoded_data['items'][i]['snippet']['thumbnails']['high']['url']

            playlists.append([playlist_id,playlist_name,thumb])
    return playlists















base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', None)

my_addon = xbmcaddon.Addon()

show_lists=my_addon.getSetting('show_lists')
show_adds=my_addon.getSetting('show_adds')


if mode is None:
    folders=get_folders()
    
    for i in range(len(folders)):
        if folders[i]!='Other':
            url = build_url({'mode': 'open_folder', 'foldername': '%s'%folders[i]})
            li = xbmcgui.ListItem('%s'%folders[i], iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/folder.png')

            rem_uri = build_url({'mode': 'rem_folder', 'foldername': '%s'%str(folders[i])})
            
            add_uri = build_url({'mode': 'add_folder'})
            addch_uri = build_url({'mode': 'add_channel', 'foldername': 'Other'})
            li.addContextMenuItems([ ('Remove folder', 'RunPlugin(%s)'%rem_uri),
                                    ('Add folder', 'RunPlugin(%s)'%add_uri),
                                    ('Add channel to root', 'RunPlugin(%s)'%addch_uri)])

            
            


            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)


    if show_lists !='false':
        url = build_url({'mode': 'categories', 'foldername': 'Categories'})
        li = xbmcgui.ListItem('Categories', iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/category.png')

        add_uri = build_url({'mode': 'add_folder'})
        addch_uri = build_url({'mode': 'add_channel', 'foldername': 'Other'})
        li.addContextMenuItems([('Add folder', 'RunPlugin(%s)'%add_uri),
                                    ('Add channel to root', 'RunPlugin(%s)'%addch_uri)])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)

        url = build_url({'mode': 'top50', 'foldername': 'Top Channels'})
        li = xbmcgui.ListItem('Top Channels', iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/top.png')

        add_uri = build_url({'mode': 'add_folder'})
        addch_uri = build_url({'mode': 'add_channel', 'foldername': 'Other'})
        li.addContextMenuItems([('Add folder', 'RunPlugin(%s)'%add_uri),
                                    ('Add channel to root', 'RunPlugin(%s)'%addch_uri)])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)
    
    channels=get_channels('Other')
    for i in range(len(channels)):
        url = build_url({'mode': 'open_channel', 'foldername': '%s'%str(channels[i][1]), 'page':'1'})
        li = xbmcgui.ListItem('%s'%channels[i][0], iconImage='%s'%channels[i][2])

        rem_uri = build_url({'mode': 'rem_channel', 'channel_id': '%s'%str(channels[i][1])})
        add_uri = build_url({'mode': 'add_folder'})
        addch_uri = build_url({'mode': 'add_channel', 'foldername': 'Other'})
        li.addContextMenuItems([('Remove channel', 'RunPlugin(%s)'%rem_uri),('Add folder', 'RunPlugin(%s)'%add_uri),
                                    ('Add channel to root', 'RunPlugin(%s)'%addch_uri)])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li,isFolder=True)
    
    if show_adds !='false' or (len(folders) == 0):

        url = build_url({'mode': 'add_folder', 'foldername': 'Add folder'})
        li = xbmcgui.ListItem('[COLOR green]Add folder[/COLOR]', iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/plus.png')
        add_uri = build_url({'mode': 'add_folder'})
        addch_uri = build_url({'mode': 'add_channel', 'foldername': 'Other'})
        li.addContextMenuItems([('Add folder', 'RunPlugin(%s)'%add_uri),
                                    ('Add channel to root', 'RunPlugin(%s)'%addch_uri)])

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)
        
        url = build_url({'mode': 'add_channel', 'foldername': 'Other'})
        li = xbmcgui.ListItem('[COLOR green]Add channel to [/COLOR][COLOR blue] root[/COLOR]', iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/plus.png')
        add_uri = build_url({'mode': 'add_folder'})
        addch_uri = build_url({'mode': 'add_channel', 'foldername': 'Other'})
        li.addContextMenuItems([('Add folder', 'RunPlugin(%s)'%add_uri),
                                    ('Add channel to root', 'RunPlugin(%s)'%addch_uri)])
        
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)
                              

    xbmcplugin.endOfDirectory(addon_handle)


elif mode[0]=='del_all':
    delete_database()
    xbmc.executebuiltin("Container.Refresh")

elif mode[0]=='add_folder':
    keyboard = xbmc.Keyboard('', 'Folder name:', False)
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        folder_name = keyboard.getText()

        add_folder(folder_name)
    xbmc.executebuiltin("Container.Refresh")

elif mode[0]=='open_folder':

    dicti=urlparse.parse_qs(sys.argv[2][1:])
    foldername=dicti['foldername'][0]
    
    channels=get_channels(foldername)
    
    for i in range(len(channels)):
        url = build_url({'mode': 'open_channel', 'foldername': '%s'%str(channels[i][1]), 'page':'1'})
        li = xbmcgui.ListItem('%s'%channels[i][0], iconImage='%s'%channels[i][2])

        rem_uri = build_url({'mode': 'rem_channel', 'channel_id': '%s'%str(channels[i][1])})
        li.addContextMenuItems([ ('Remove channel', 'RunPlugin(%s)'%rem_uri)])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li,isFolder=True)
        url = build_url({'mode': 'add_channel', 'foldername': '%s'%foldername})
        li = xbmcgui.ListItem('[COLOR green]Add channel to [/COLOR][COLOR blue] root[/COLOR]', iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/plus.png')
        



    url = build_url({'mode': 'add_channel', 'foldername': '%s'%foldername})
    li = xbmcgui.ListItem('[COLOR green]Add channel to[/COLOR][COLOR blue] %s[/COLOR]'%foldername, iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/plus.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li,isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0]=='top50':
    get_chart_50()


elif mode[0]=='categories':
    list_categories()

elif mode[0]=='open_channel':
    dicti=urlparse.parse_qs(sys.argv[2][1:])
    page=dicti['page'][0]

    id=dicti['foldername'][0]

    try:
        playlist=dicti['playlist'][0]
        if playlist=='yes':
            playlista=True
    except:
        playlista=False

    
    if not playlista and enable_playlists=='true':

        url = build_url({'mode': 'open_playlists', 'id':'%s'%id, 'page':'1'})
        li = xbmcgui.ListItem('[COLOR yellow]Playlists [/COLOR]',iconImage='https://raw.githubusercontent.com/natko1412/repo.natko1412/master/img/playlist.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li,isFolder=True)




    game_list=get_latest_from_channel(id,page)
    next_page=game_list[0]

    for i in range(1,len(game_list)):
        title=game_list[i][0]
        video_id=game_list[i][1]
        thumb=game_list[i][2]
        desc=game_list[i][3]
        
        uri='plugin://plugin.video.youtube/play/?video_id='+video_id
        li = xbmcgui.ListItem('%s'%title, iconImage=thumb)
        li.setProperty('IsPlayable', 'true')
        li.setInfo('video', { 'genre': 'YouTube' } )

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=uri, listitem=li)#,isFolder=True)

    if next_page!='1':
        if playlista:
            uri = build_url({'mode': 'open_channel', 'foldername': '%s'%id, 'page' : '%s'%next_page ,'playlist':'yes'})
        else:
            uri = build_url({'mode': 'open_channel', 'foldername': '%s'%id, 'page' : '%s'%next_page })

        li = xbmcgui.ListItem('Next Page >>', iconImage=thumb)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=uri, listitem=li,isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)


elif mode[0]=='open_playlists':
    dicti=urlparse.parse_qs(sys.argv[2][1:])
    id=dicti['id'][0]
    page=dicti['page'][0]
    channel_id=get_channel_id_from_uploads_id(id)
    playlists=get_playlists(channel_id,page)

    next_page=playlists[0]
    for i in range (1,len(playlists)):
        id=playlists[i][0]
        name=playlists[i][1]
        thumb=playlists[i][2]


        url = build_url({'mode': 'open_channel', 'foldername': '%s'%id, 'page':'1', 'playlist':'yes'})
        li = xbmcgui.ListItem('%s'%name, iconImage='%s'%thumb)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li,isFolder=True)


    if next_page!='1':
        
        uri = build_url({'mode': 'open_playlists', 'id': '%s'%id, 'page' : '%s'%next_page ,'playlist':'yes'})
      

        li = xbmcgui.ListItem('Next Page >>', iconImage=thumb)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=uri, listitem=li,isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
    











elif mode[0]=='add_channel':
    options=['Search for channel','Add by username']
    ind = xbmcgui.Dialog().select('Choose option', options)
    if ind==0:

        dicti=urlparse.parse_qs(sys.argv[2][1:])
        foldername=dicti['foldername'][0]
        
        keyboard = xbmc.Keyboard('', 'Search channel:', False)
        keyboard.doModal()
        
        if keyboard.isConfirmed():
            channel_name = keyboard.getText()
        


            results=search_channel(channel_name)
            
            result_list=[]
            for i in range(len(results)):
                result_list+=[results[i][0]]
            dialog = xbmcgui.Dialog()
            index = dialog.select('Choose channel', result_list)
            if index>-1:
                channel_uplid=results[index][1]
                channel_name=results[index][0]
                thumb=results[index][2]
                channel_id=results[index][3]

                add_channel(foldername,channel_name,channel_uplid,thumb)
    elif ind==1:
        dicti=urlparse.parse_qs(sys.argv[2][1:])
        foldername=dicti['foldername'][0]
        
        keyboard = xbmc.Keyboard('', 'Enter username:', False)
        keyboard.doModal()
        
        if keyboard.isConfirmed():
            channel_name = keyboard.getText()
            help_list=search_channel_by_username(channel_name)
            
            if help_list== 'not found':
                xbmcgui.Dialog().ok("Youtube Channels", 'Channel with username "%s" does not exist.'%channel_name)
            else:
                channel_name=help_list[0]
                channel_id=help_list[1]
                thumb=help_list[2]
                add_channel(foldername,channel_name,channel_id,thumb)

    xbmc.executebuiltin("Container.Refresh")


elif mode[0]=='rem_channel':
    dicti=urlparse.parse_qs(sys.argv[2][1:])
    channel_id=dicti['channel_id'][0]
    remove_channel(channel_id)
    xbmc.executebuiltin("Container.Refresh")

elif mode[0]=='rem_folder':
    dicti=urlparse.parse_qs(sys.argv[2][1:])
    foldername=dicti['foldername'][0]
    remove_folder(foldername)
    xbmc.executebuiltin("Container.Refresh")

elif mode[0]=='erase_all':
    ret = xbmcgui.Dialog().yesno('Erase database', 'Do you wish to erase your Youtube Channels database?' ) 
    
    if ret:       

        delete_database()
        xbmcgui.Dialog().ok("Youtube Channels", "Successfully erased folder database!")


elif mode[0]=='open_category':
    dicti=urlparse.parse_qs(sys.argv[2][1:])
    site=dicti['site'][0]

    open_category(site)

elif mode[0]=='import':

    import_from_old_addon()
