import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon
import xbmc
import sqlite3
import json
import sys
from six.moves import urllib

addonID = xbmcaddon.Addon().getAddonInfo("id")
addon = xbmcaddon.Addon(addonID)
db_path = addon.getAddonInfo('profile')
db_file = xbmc.translatePath("%s/youtube_channels.db" % db_path)

if not xbmcvfs.exists(db_path):
	xbmcvfs.mkdirs(db_path)

db = sqlite3.connect(db_file)

base_url = sys.argv[0]

my_addon = xbmcaddon.Addon()
YOUTUBE_API_KEY = my_addon.getSetting('youtube_api_key')
addon_handle = int(sys.argv[1])

def build_url(query):
	return base_url + '?' + urllib.parse.urlencode(query)

def delete_database():
	
	with db:
	
		cur = db.cursor()
		
		cur.execute("drop table if exists Folders")
		cur.execute("drop table if exists Channels")
		db.commit()
		cur.close()

	return

def read_url(url):
		req = urllib.request.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:33.0) Gecko/20100101 Firefox/33.0')
		response = urllib.request.urlopen(req)
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

	cur = db.cursor()
	cur.execute("begin")     
	cur.execute("SELECT Name FROM Folders")

	rows = cur.fetchall()
	db.commit()
	cur.close()
	folders=[]
	for i in range (len(rows)):
		folder=rows[i]
		folders+=folder
		
	return folders

def add_folder(foldername):
	init_database()

	cur = db.cursor()  
	cur.execute("begin")   
	cur.execute('INSERT INTO Folders(Name) VALUES ("%s");'%foldername)
	db.commit()
	cur.close()
	

def remove_folder(name):
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
	db.commit
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

def local_string(string_id):
	return my_addon.getLocalizedString(string_id)