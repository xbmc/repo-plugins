import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon
import xbmc
import sqlite3
import json
import sys
import re
from six.moves import urllib

addonID = xbmcaddon.Addon().getAddonInfo("id")
addon = xbmcaddon.Addon(addonID)
db_path = addon.getAddonInfo('profile')
if sys.version_info.major == 3:
	db_file = xbmcvfs.translatePath("%s/youtube_channels.db" % db_path)
else:
	db_file = xbmc.translatePath("%s/youtube_channels.db" % db_path)

if not xbmcvfs.exists(db_path):
	xbmcvfs.mkdirs(db_path)

db = sqlite3.connect(db_file)

base_url = sys.argv[0]

my_addon = xbmcaddon.Addon()
YOUTUBE_API_KEY = my_addon.getSetting('youtube_api_key')
addon_handle = int(sys.argv[1])

# https://stackoverflow.com/a/49976787
def yt_time(duration="P1W2DT6H21M32S"):
	"""
	Converts YouTube duration (ISO 8061)
	into Seconds

	see http://en.wikipedia.org/wiki/ISO_8601#Durations
	"""
	ISO_8601 = re.compile(
		'P'   # designates a period
		'(?:(?P<years>\d+)Y)?'   # years
		'(?:(?P<months>\d+)M)?'  # months
		'(?:(?P<weeks>\d+)W)?'   # weeks
		'(?:(?P<days>\d+)D)?'    # days
		'(?:T' # time part must begin with a T
		'(?:(?P<hours>\d+)H)?'   # hours
		'(?:(?P<minutes>\d+)M)?' # minutes
		'(?:(?P<seconds>\d+)S)?' # seconds
		')?')   # end of time part
	# Convert regex matches into a short list of time units
	units = list(ISO_8601.match(duration).groups()[-3:])
	# Put list in ascending order & remove 'None' types
	units = list(reversed([int(x) if x != None else 0 for x in units]))
	# Do the maths
	return sum([x*60**units.index(x) for x in units])

def move_up(id):
	cur = db.cursor()
	cur.execute('SELECT folder, sort FROM Channels WHERE ROWID = ?',(id,))
	rows = cur.fetchall()
	for row in rows:
		folder = row[0]
		sort = row[1]
		new_sort = sort - 1
		cur.execute('UPDATE Channels SET sort = ? WHERE SORT = ?',(sort, new_sort))
		cur.execute('UPDATE Channels SET sort = ? WHERE ROWID = ?',(new_sort, id))
		db.commit()
		cur.close()
	return

def move_down(id):
	cur = db.cursor()
	cur.execute('SELECT folder, sort FROM Channels WHERE ROWID = ?',(id,))
	rows = cur.fetchall()
	for row in rows:
		folder = row[0]
		sort = row[1]
		new_sort = sort + 1
		cur.execute('UPDATE Channels SET sort = ? WHERE SORT = ?',(sort, new_sort))
		cur.execute('UPDATE Channels SET sort = ? WHERE ROWID = ?',(new_sort, id))
		db.commit()
		cur.close()
	return

def build_url(query):
	return base_url + '?' + urllib.parse.urlencode(query)

def check_thumb_db():
	cur = db.cursor()
	columns = [i[1] for i in cur.execute('PRAGMA table_info(Folders)')]
	if 'Thumb' not in columns:
		return False
	else:
		return True

def add_thumb_db():
	# Add thumbnail column to existing database if it doesn't already exist
	cur = db.cursor()
	try: # This should always succeed since this should only get called if the column hasn't been added but using try just in-case
		cur.execute('ALTER TABLE Folders ADD COLUMN Thumb TEXT;')
	except:
		pass
	db.commit()
	cur.close()
	return

def check_sort_db():
	cur = db.cursor()
	columns = [i[1] for i in cur.execute('PRAGMA table_info(Channels)')]
	if 'sort' not in columns:
		return False
	else:
		return True

def add_sort_db():
	# Add sort column to existing database if it doesn't already exist and set initial sort values
	cur = db.cursor()
	try: # This should always succeed since this should only get called if the column hasn't been added but using try just in-case
		cur.execute('ALTER TABLE Channels ADD COLUMN sort INT;')
	except:
		pass
	db.commit()
	cur.close()
	return

def init_sort(folder):
	cur = db.cursor()
	cur.execute('SELECT Channel, ROWID FROM Channels WHERE Folder = ? AND sort IS NULL',(folder,))
	null_rows = cur.fetchall()
	i = 1
	for row in null_rows:
		cur.execute("UPDATE Channels SET sort = ? WHERE ROWID = ?;",(i,row[1]))
		i+=1
	db.commit()
	cur.close()
	return

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
		cur.execute("create table if not exists Folders (Name TEXT, Channel TEXT, Thumb TEXT)")
		cur.execute("create table if not exists Channels (Folder TEXT, Channel TEXT, Channel_ID TEXT,thumb TEXT,sort INT)")
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

	cur.execute("SELECT Channel,Channel_ID,thumb,sort,ROWID FROM Channels WHERE Folder=? ORDER BY sort ASC",(foldername,))

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

	cur.execute("SELECT * FROM Channels WHERE Folder = ?",(foldername,))
	sort = len(cur.fetchall()) + 1
	cur.execute("INSERT INTO Channels(Folder,Channel,Channel_ID,thumb,sort) VALUES (?,?,?,?,?);",(foldername,channel_name,channel_id,thumb,sort))
	db.commit()
	cur.close()

def change_folder(channel_id, folder_name):
	if folder_name=="root":
		folder_name="Other"
	cur = db.cursor()
	cur.execute("begin")
	cur.execute("SELECT * From Channels WHERE Folder = ?",(folder_name,))
	sort = len(cur.fetchall()) + 1
	cur.execute("UPDATE Channels SET Folder = ?, sort = ? WHERE Channel_ID = ?;",(folder_name, sort, channel_id))
	db.commit()
	cur.close()

def remove_channel(id):
	cur = db.cursor()
	cur.execute("begin")

	cur.execute("DELETE FROM Channels WHERE Channel_ID = ?;",(id,))

	db.commit()
	cur.close()

def set_folder_thumbnail(folder_name, image):
	cur = db.cursor()
	cur.execute("begin")
	cur.execute("UPDATE Folders SET Thumb = ? WHERE Name = ?;",(image, folder_name))
	db.commit()
	cur.close()

def get_folder_thumbnail(folder_name):
	cur = db.cursor()
	cur.execute("begin")
	cur.execute("SELECT Thumb FROM Folders WHERE Name = ?;",(folder_name,))
	thumb = cur.fetchone()[0]
	db.commit()
	cur.close()

	return thumb

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
		req_url='https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&fields=items/snippet/resourceId/videoId,nextPageToken&maxResults=%s&playlistId=%s&key='%(str(result_num),channel_id)+YOUTUBE_API_KEY
	else:
		req_url='https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&fields=items/snippet/resourceId/videoId,nextPageToken&pageToken=%s&maxResults=%s&playlistId=%s&key='%(page,str(result_num),channel_id)+YOUTUBE_API_KEY
	read=read_url(req_url)
	decoded_data=json.loads(read)
	listout=[]
	videoids=[]
	try:
		next_page=decoded_data['nextPageToken']
	except:
		next_page='1'
	listout.append(next_page)

	for x in range(0, len(decoded_data['items'])):
		video_id = decoded_data['items'][x]['snippet']['resourceId']['videoId']
		videoids.append(video_id)

	video_req_url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=%s&key=%s' % (','.join(videoids), YOUTUBE_API_KEY)
	video_read = read_url(video_req_url)
	video_decoded = json.loads(video_read)
	sorted_data = sorted((video_decoded['items']), key=(lambda x: x['snippet']['publishedAt']), reverse=True)
	for x in range(0, len(sorted_data)):
		title = sorted_data[x]['snippet']['title']
		video_id = sorted_data[x]['id']
		thumb = sorted_data[x]['snippet']['thumbnails']['high']['url']
		desc = sorted_data[x]['snippet']['description']
		duration = sorted_data[x]['contentDetails']['duration']
		seconds = yt_time(duration)
		date = re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", sorted_data[x]['snippet']['publishedAt'])
		listout.append([title, video_id, thumb, desc, seconds, date.group()])
	return listout

def get_playlists(channelID,page):
	if page=='1':
		url='https://www.googleapis.com/youtube/v3/playlists?part=snippet&channelId=%s&maxResults=10&key=%s'%(channelID,YOUTUBE_API_KEY)
	else:
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

def get_livestreams(channelID,page):
	if page=='1':
		url='https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId=%s&eventType=live&order=date&type=video&key=%s'%(channelID,YOUTUBE_API_KEY)
	else:
		url='https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId=%s&eventType=live%order=date%type=video&pageToken=%s&key=%s'%(channelID,page,YOUTUBE_API_KEY)
	read=read_url(url)
	decoded_data=json.loads(read)
	livestreams=[]
	videoids=[]
	try:
		next_page=decoded_data['nextPageToken']
	except:
		next_page='1'
	livestreams.append(next_page)
	
	for i in range(0, len(decoded_data['items'])):
		video_id = decoded_data['items'][i]['id']['videoId']
		videoids.append(video_id)

	video_req_url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=%s&key=%s' % (','.join(videoids), YOUTUBE_API_KEY)
	video_read = read_url(video_req_url)
	video_decoded = json.loads(video_read)
	sorted_data = sorted((video_decoded['items']), key=(lambda i: i['snippet']['publishedAt']), reverse=True)
	
	for i in range(0, len(sorted_data)):
		title = sorted_data[i]['snippet']['title']
		video_id = sorted_data[i]['id']
		thumb = sorted_data[i]['snippet']['thumbnails']['high']['url']
		desc = sorted_data[i]['snippet']['description']
		livestreams.append([title, video_id, thumb, desc])

	return livestreams

def local_string(string_id):
	return my_addon.getLocalizedString(string_id)
