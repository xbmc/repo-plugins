# -*- coding: utf-8 -*-
#!/usr/bin/python
#
#
#
# Auth: Jarkko Vesiluoma
#       jvesiluoma@gmail.com
#
# Version history:
#  [B]2.0.3[/B] - Watson 2.2.1 release, plugin fixed to work with recent updates. Thanks to Antti Kerola recurring recordings, fixes to searchrec and setContent in Addir Func.
#  [B]2.0.2[/B] - Watson 2.2.0 release, plugin fixed to work with recent updates.
#  [B]2.0.1[/B] - Watson 2.0 release, plugin fixed to work with new Watson.
#  [B]1.1.1[/B] - Download function improved, will now download to single file, some minor updates. New icon.
#  [B]1.1.0[/B] - Beta, programs can now be removed from recordings / favourites.
#  [B]1.0.9[/B] - Beta, Context menu to save program to recordings / favourites added, tmp dirs now selectable from settings
#  [B]1.0.8[/B] - Beta, Search for recordings added
#  [B]1.0.7[/B] - Beta, Download and Plot context menus added
#  [B]1.0.6[/B] - Beta, Minor fixes
#  [B]1.0.5[/B] - Beta, LiveTV added
#  [B]1.0.4[/B] - Pre-Alpha2, Video stop now fixed, started to code "LiveTV" option 
#  [B]1.0.3[/B] - Pre-Alpha2, tmpfile location check (os-check)
#  [B]1.0.2[/B] - Pre-Alpha2, minor modifications
#  [B]1.0.1[/B] - Pre-Alpha2, modified menu structure
#  [B]1.0.0[/B] - Initial version for XBMC 
#
#
#
# Watson 1 API description:
#
# User recordings (user archive):
#   http://www.watson.fi/pctv/RSS?action=getfavoriterecordings
# 
#   XML format:
#     TITLE		= Program title
#     DESC		= Program description
#     AIRDATE	= Program airdate
#     LINK		= Program link to RSS, e.g: http://www.watson.fi/pctv/rss/recordings/1382979
#     PLINK		= Program permanent link, e.g: 1382979
#     SOURCEURL = Program source url, e.g: http://www.watson.fi/pctv/rss/channels/317994
#     SRCURLINF = Program source url info, e.g: 317994 - HLS/Unknown
#     DURL      = Program download url, if bitrate is '-1', then program is scheduled for recording, but not yet in archive e.g: http://www.watson.fi/pctv/Download?id=1382979&amp;format=HLS&amp;bitrate=-1
#                 If bitrate is for example 1974558, program is recorded and of course, state is 'active and reason is 'Completed' instead of 'blocked' and 'Queued'.
#     THUMBNAIL = Program thumbnail url, e.g: http://www.watson.fi/pctv/resources/recordings/screengrabs/1375085.jpg
#
#         <item>
#            <title>TITLE</title>
#            <description>DESC</description>
#            <dc:date>AIRDATE</dc:date>
#            <link>LINK</link>
#            <guid isPermaLink="false">PLINK</guid>
#            <source url="SOURCEURL">SRCURLINF</source>
#                        <media:content url="DURL" medium="video" type="video/mp4"  expression="full" duration="1980"/>
#            <media:status  state="blocked"  reason="Queued" />
#            <media:community><media:starRating average="0"  min="0" max="5"/></media:community>
#         </item>
#
#     This is how few last line looks, when program is already recorded, notice that 'content url' - line has video type, medium, filesize etc. and state is now 'active' and reason is changed to 'Complete'
#
#                        <media:content url="http://www.watson.fi/pctv/Download?id=1375085&amp;format=HLS&amp;bitrate=1974558" medium="video" type="video/mp4" fileSize="1091264424" expression="full" duration="3180"/>
#            <media:status  state="active"  reason="Completed" />
#            <media:community><media:starRating average="0"  min="0" max="5"/></media:community>
#            <media:thumbnail url="THUMBNAIL" height="72" width="96"/>
#
#
# EPG from last 120 hours:
#   http://www.watson.fi/pctv/RSS?action=getprograms&hours=120
#
#
# Users scheduled recordings: 
#   http://www.watson.fi/pctv/RSS?action=getscheduledrecordings
#   
#   XML format:
#     NAME		= Program name, e.g: Paljastavat valheet
#     CHANID	= Channel Id, e.g: 1011
#     LINK		= Program link, e.g: http://www.watson.fi/pctv/rss/scheduledrecordings/756093
#     PLINK		= Program permanent link, e.g: 756093
#     SURL		= Source URL: http://www.watson.fi/pctv/rss/channels/1011
#
#         <item>
#            <title>NAME</title>
#            <description>Scheduled Recording for Program Title NAME, Every Day from Channel ID CHANID</description>
#            <link>LINK</link>
#            <guid isPermaLink="false">PLINK</guid>
#            <source url="SURL">CHANID</source>
#         </item>
#
# Add recording to favorites:
#   RECORDINGID = 7 digit recodring id (permlink), e.g: 1264516
#   http://www.watson.fi/pctv/RSS?action=addfavorite&amp;id=RECORDINGID
#
#
# Remove program from recordings / favorites:
#    RECORDINGID = 7 digit recodring id (permlink), e.g: 1264516
#    http://www.watson.fi/pctv/RSS?action=removerecording&id=RECORDINGID
#
#
# Search recordings and programs:
#   SEARCHSTRING	= Search string to find recordings and programs
#   http://www.watson.fi/pctv/RSS?action=search&type=all&field=all&term=SEARCHSTRING
#
# 
# 
#
# TV channel Id list: 
#   1006	= Jim
#   1007	= Yle something???
#   1008	= Nelonen
#   1010	= TV1
#   1011	= MTV3
#   1012	= TV2
#   1013	= SVT1
#   1014	= TV5
#   1015	= Sub
#   161260	= ???
#   642360  = TV6
#   629149	= AVA
#   642360	= MTV?
#   317994	= FOX





# Global variables
VERSION = "2.2.1"
MYHEADERS = { 'User-Agent': "Watson-XBMC version "+VERSION+";" }
DEBUG=1
# 1=low, 2=high, any other ==> low
QUALITY=2

# Imports
import locale
locale.setlocale(locale.LC_ALL, 'C')
import urllib, urllib2, cookielib , re, os, sys, time, linecache, StringIO, time, xbmcplugin, xbmcaddon, xbmcgui, socket, operator, httplib, base64
#import CommonFunctions as common
from xml.dom import minidom
from urlparse import urlparse
watson_addon = xbmcaddon.Addon("plugin.video.watson");
channeldict={'1006':'Jim','1007':'Yle?','1008':'Nelonen','1010':'TV1','1011':'MTV3','1012':'TV2','1013':'SVT1','1014':'TV5','1015':'Sub','629149':'AVA','317994':'Fox','642360':"TV6"}
url_archive='http://www.watson.fi/pctv/RSS?action=getfavoriterecordings'

tmpfile=watson_addon.getSetting("tempdir")+"tmp_m3u8a"
tmpfile2=watson_addon.getSetting("tempdir")+"tmp_m3u8b"


# Check settings
def settings():
  # Is account setup properly? Well...at least something given?
  
  if watson_addon.getSetting("username") != '' and watson_addon.getSetting("password") != '' and tmpfile != ""  and tmpfile2 != "":
    INDEX()
  else:
    u=sys.argv[0]+"?url=Settings&mode=5"
    listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30207))
    listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30207)})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

    
# Get first selection list and display items from tuples
def INDEX():
  
  # Live TV
  u=sys.argv[0]+"?url=LiveTV&mode=1"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30201))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30201)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  
  # Archive
  u=sys.argv[0]+"?url=Arc hive&mode=2"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30202))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30202)})    
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
  
  # Recent and user movies
  u=sys.argv[0]+"?url=Movies&mode=11"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30205))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30205)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)  
  
  
  # Search recordings
  u=sys.argv[0]+"?url=SearchRec&mode=7"
  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30203))
  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30203)})
  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)    

  
#  # Testing, comment before release
#  u=sys.argv[0]+"?url=Testing&mode=12"
#  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30208))
#  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30208)})
#  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)   

#  # Local archive option
#  u=sys.argv[0]+"?url=LocalArchive&mode=13"
#  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30209))
#  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30209)})
#  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
	
  # Recent and user movies
#  u=sys.argv[0]+"?url=VODMovies&mode=12"
#  listfolder = xbmcgui.ListItem(watson_addon.getLocalizedString(30206))
#  listfolder.setInfo('video', {'Title': watson_addon.getLocalizedString(30206)})
#  xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)  


# ===== By Antti Kerola: ====
  week=watson_addon.getLocalizedString(30210).split(',') #"maanantai,tiistai,..."
  t=time.time()
  for i in range(0,13):
    tt=time.localtime(t-86400*i)
    title='%s %s' % (week[tt[6]], (time.strftime("%d.%m",tt)))
    listfolder = xbmcgui.ListItem(title)
    listfolder.setInfo('video', {'Title': title})
    u=sys.argv[0]+"?url=EPG&year=%d&month=%d&day=%d&mode=13" % (tt[0],tt[1],tt[2])
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)

# ===== By Antti Kerola ==== ^^^
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

  


def showmovies(url):
  # Find movies: https://www.watson.fi/pctv/RSS?action=search&type=all&field=all&term=elokuva&58;
  url = "https://www.watson.fi/pctv/RSS?action=search&type=all&field=all&term=elokuva&58;"
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()

  # Save everyhing we need to tuples...
  recsearchmatch=re.compile('<title\>(.+?)<\/title\>\n            <description\>(.+?)<\/description\>\n                    <dc:date\>(.+?)<\/dc:date\>\n            <link\>(.+?)<\/link\>\n            <guid isPermaLink="(.+?)"\>(.+?)<\/guid\>\n            <source url="(.+?)"\>(.+?)<\/source\>\n                                        <media:content url="(.+?)" medium="(.+?)" type="(.+?)" fileSize="(.+?)" expression="(.+?)" duration="(.+?)"\/\>\n                    <media:status  state="(.+?)"  reason="(.+?)" \/\>\n            <media:community\><media:starRating average="(.+?)"  min="(.+?)" max="(.+?)"\/\><\/media:community\>\n                    <media:thumbnail url="(.+?)" height="(.+?)" width="(.+?)"\/\>').findall(searchcontent)
  recsearchmatch.sort(key=operator.itemgetter(2), reverse=True)
  
  # Add search results
  for matchitem in recsearchmatch:    
    sendurl=matchitem[8]
    sendday=matchitem[2].split("T")[0]
    sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
    sendname=matchitem[0]+" - "+sendday+" "+sendtime
    sendname=sendname.replace("&#228;","a")
    senddesc=matchitem[1].replace("&#228;","a")
    senddesc=senddesc.replace("&#246;","o")
    senddesc=senddesc.replace("&amp;","&")

    #Format: addDir(name,url,mode,thumbnail, description, permlink)   
    if "Elokuva" in sendname:
	  addDir(sendname,sendurl.replace("&amp;","&"),4,matchitem[17]+"?width=640&height=480",senddesc, matchitem[5])  

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
# Ask search string from user
def search(url):
  keyboard = xbmc.Keyboard('', watson_addon.getLocalizedString(30204))
  keyboard.doModal()
  if keyboard.isConfirmed() and keyboard.getText():
    search_string = keyboard.getText().replace(" ","+")
    searchrec("https://www.watson.fi/pctv/RSS?action=search&type=all&field=all&term="+search_string)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
# Search from programs *** Not in use ***        
def searchproc(url):
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()

  # Save everyhing we need to tuples...
#  procsearchmatch=re.compile('<title>(.+?)</title>\n            <description>(.+?)</description>\n            <dc:date>(.+?)</dc:date>\n            <guid isPermaLink="false">(.+?)</guid>\n            <link>(.+?)</link>\n            <source url="(.+?)">(.+?)</source>\n            <media:content duration="(.+?)"/>\n').findall(searchcontent)
  procsearchmatch=re.compile('<title\>(.+?)<\/title\>\n            <description\>(.+?)<\/description\>\n                    <dc:date\>(.+?)<\/dc:date\>\n            <link\>(.+?)<\/link\>\n            <guid isPermaLink="(.+?)"\>(.+?)<\/guid\>\n            <source url="(.+?)"\>(.+?)<\/source\>\n                                        <media:content url="(.+?)" medium="(.+?)" type="(.+?)" fileSize="(.+?)" expression="(.+?)" duration="(.+?)"\/\>\n                    <media:status  state="active"  reason="Completed" \/\>\n            <media:community\><media:starRating average="0"  min="0" max="5"\/\><\/media:community\>\n                    <media:thumbnail url="https:\/\/www.watson.fi\/pctv\/resources\/recordings\/screengrabs\/2173711.jpg" height="72" width="96"\/\>').findall(searchcontent)
  procsearchmatch.sort(key=operator.itemgetter(0), reverse=True)
  
  # Add search results
  for matchitem in procsearchmatch:    
    sendurl=matchitem[4]
    sendday=matchitem[2].split("T")[0]
    sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
    sendname=matchitem[0]+" - "+sendday+" "+sendtime
    sendname=sendname.replace("&#228;","a")
	
    senddesc=matchitem[1].replace("&#228;","a")
    senddesc=senddesc.replace("&#246;","o")
    senddesc=senddesc.replace("&amp;","&")
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    addDir(sendname,sendurl.replace("&amp;","&"),4,"",senddesc, "")    
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
    
# Add recording to 'favourites' by plink (seven digit recording id)
def addrecording(name, plink):

  # Compile url
  url="http://www.watson.fi/pctv/RSS?action=addfavorite&id="+plink
         
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()
  
  xbmcgui.Dialog().ok("Info","Recording %s \n added to recordings."%(name))
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
def removerecording(url,name):
    
  # Compile url
  url="http://www.watson.fi/pctv/RSS?action=removerecording&id="+plink
   
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()
  
  xbmcgui.Dialog().ok("Info","Recording %s \n removed from recordings."%(name))  
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))


def searchrec(url):
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  searchcontent = opener.open(request).read()

  # Save everyhing we need to tuples...
  recsearchmatch=re.compile('<title\>(.+?)<\/title\>\n            <description\>(.+?)<\/description\>\n                    <dc:date\>(.+?)<\/dc:date\>\n            <link\>(.+?)<\/link\>\n            <guid isPermaLink="(.+?)"\>(.+?)<\/guid\>\n            <source url="(.+?)"\>(.+?)<\/source\>\n                                        <media:content url="(.+?)" medium="(.+?)" type="(.+?)" fileSize="(.+?)" expression="(.+?)" duration="(.+?)"\/\>\n                    <media:status  state="(.+?)"  reason="(.+?)" \/\>\n            <media:community\><media:starRating average="(.+?)"  min="(.+?)" max="(.+?)"\/\><\/media:community\>\n                    <media:thumbnail url="(.+?)" height="(.+?)" width="(.+?)"\/\>').findall(searchcontent)
  recsearchmatch.sort(key=operator.itemgetter(2), reverse=True)
  
  # Add search results
  for matchitem in recsearchmatch:    
    sendurl=matchitem[8]
    sendday=matchitem[2].split("T")[0]
    sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
    sendname=matchitem[0]+" - "+sendday+" "+sendtime
    sendname=sendname.replace("&#228;","a")
    senddesc=matchitem[1].replace("&#228;","a")
    senddesc=senddesc.replace("&#246;","o")
    senddesc=senddesc.replace("&amp;","&")

    #Format: addDir(name,url,mode,thumbnail, description, permlink)
    addDir(sendname,sendurl.replace("&amp;","&"),4,matchitem[19]+"?width=640&height=480",senddesc, matchitem[5])    

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

  
# Fetch XML and parse channel list from there and make list of channels
def channellist(url,showmode):
  auth_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handler.add_password(None, "https://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handler))
  request = urllib2.Request(url, headers=MYHEADERS)
  content = opener.open(request).read()
  dom = minidom.parseString(content)
  items = dom.getElementsByTagName('item')
    
  for i in items:
    if i.getElementsByTagName('hbx:channel')[0].getAttribute("encrypted") == "false" and i.getElementsByTagName('hbx:channel')[0].getAttribute("clientSideSecured") == "false":
      programtitle=i.getElementsByTagName('title')[0].childNodes[0].nodeValue
      programdesc=i.getElementsByTagName('description')[0].childNodes[0].nodeValue
      programstream1=i.getElementsByTagName('media:content')[0].getAttribute("url")
      programthumb=i.getElementsByTagName('media:thumbnail')[0].getAttribute("url")
      channel=int(i.getElementsByTagName('guid')[0].childNodes[0].nodeValue)
      if (showmode is 'live'):
        addDir(programtitle,programstream1,6,programthumb+"?width=320&height=240",programdesc,"NoContext")
      else:
        u=sys.argv[0]+"?url=EPG&year=%d&month=%d&day=%d&mode=14&channel=%d" % (year,month,day,channel)
        listfolder=xbmcgui.ListItem(programtitle, iconImage="DefaultFolder.png", thumbnailImage=programthumb+"?width=320&height=240")
        listfolder.setInfo('video', {'Title': programtitle})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listfolder, isFolder=1)
    else:
      print "Encrypted channel: " + i.getElementsByTagName('title')[0].childNodes[0].nodeValue.encode('utf-8') + ", skipping.."

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
      	  


# Get first selection list and display items from tuples
def programs(url):

  checked = []
  ie=0
  if LoginError==False:
    for e in match:
      if e[0].split("(")[0].rstrip() not in checked:
        #print "e: "+e[0].split("(")[0]+", length: "+str(len(e[0].split("(")[0]))
        checked.append(e[0].split("(")[0].rstrip())
  
  checked.sort()
  i=0
  for item in checked:
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    itemname=item.replace("&#228;","a")
    itemname=itemname.replace("&#196;","A")
    itemname=itemname.replace("&#246;","o")
    itemname=itemname.replace("&apos;","'")
    itemname=itemname.replace("&amp;","&")
	   
    addDir(itemname,item,3,"","","NoContext")  
    i+=1
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
      
# Get first selection list and display items from tuples
def episodelist	(url,name):
  i=0
  name=url
  # Sort results by time 
  match.sort(key=operator.itemgetter(2), reverse=True)
  #print "name: "+name.split("(")[0].rstrip()+", length: "+str(len(name.split("(")[0].rstrip()))
  
  for matchitem in match:
    
    if matchitem[0].split("(")[0].rstrip()==name.split("(")[0].rstrip():
      #adddir uniques
      sendurl=matchitem[8]
      sendday=matchitem[2].split("T")[0]
      sendtime=matchitem[2][matchitem[2].find("T")+1:matchitem[2].find("+")]
      # Try to get Channel name
      try:
        sendname=matchitem[0]+" - "+channeldict[matchitem[7].split(" ")[0]]+" - "+sendday+" "+sendtime
      except:
        print "Some error getting channelname with ID: " + matchitem[7].split(" ")[0]
        sendname=matchitem[0]+" - Unknown - "+sendday+" "+sendtime
      sendname=sendname.replace("&#228;","a")
      sendname=sendname.replace("&#196;","A")
      sendname=sendname.replace("&#246;","ö")
      sendname=sendname.replace("&amp;","&")
	  
      senddesc=matchitem[1].replace("&#228;","a")
      senddesc=senddesc.replace("&#246;","o")
      senddesc=senddesc.replace("&amp;","&")
      #Format: addDir(name,url,mode,thumbnail, description, permlink)
   
      addDir(sendname,sendurl.replace("&amp;","&"),4,matchitem[17]+"?width=640&height=480",senddesc, matchitem[5])    
  
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
  
  
# Add item to XBMC display list
def addDir(name,url,mode,iconimage,pdesc,plink):
  name=name.encode('utf-8')
  name=name.replace("&#228;","a")
  
  u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
  ok=True
  list=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
  contextMenuItems = []
  
  if url.startswith("http"):
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')


    # Create context menu if needed
    if plink != "NoContext":
      contextMenuItems.append(('Download Video', 'XBMC.RunPlugin(%s?url=%s&name=%s&pdesc=%s&mode=9)'%(sys.argv[0],url,name,pdesc)))
      contextMenuItems.append(( "Plot", "XBMC.Action(Info)", ))
      contextMenuItems.append(('Remove from recordings', 'XBMC.RunPlugin(%s?url=%s&name=%s&plink=%s&mode=10)'%(sys.argv[0],"removerecording",name,plink)))
      if plink != "":
        contextMenuItems.append(('Add to recordings', 'XBMC.RunPlugin(%s?url=%s&name=%s&plink=%s&mode=8)'%(sys.argv[0],"addrecording",name,plink)))

    list.addContextMenuItems( contextMenuItems )

    list.setInfo( type="Video", infoLabels={ "Title": name, 'Plot': pdesc } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=list,isFolder=False)                    

  else:
    list.setInfo( type="Video", infoLabels={ "Title": name, 'Plot': pdesc } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=list,isFolder=True)          

  return ok

# Play LiveTV, url can be played directly
def playlive(url):
  # Play selected video
  playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )

  # Read playlist
  try:
    response = urllib2.urlopen(url)
  except urllib2.HTTPError as e:
    print "DEBUG: ERROR; Can't open url "+url+". Code: "+str(e.code)
  
  try:
    firstplaylist=str(response.read())
    print "FIRSTPLAYLIST: "+str(firstplaylist)
  except urllib2.HTTPError as e:
    print "DEBUG: ERROR; Can't fetch channel playlist. Code: "+str(e.code)
  
  try:
    redirurl=str(response.geturl())
    print "REDIRURL: "+redirurl
  except urllib2.HTTPError as e:
    print "DEBUG: ERROR; Can't get channel redirection url from headers. Code: "+str(e.code)
    		
  # Get correct urls for streams..playlist contains current program files???.
  playurl={}
  i=0
  for line in firstplaylist.split("\n"):
    if "m3u8" in line:
      if i==0:
        playurl["Lo"]=line
      else:
        playurl["Hi"]=line
      i+=1

  tmpstring1=redirurl.rpartition('/')
  try:
    liveplayurl=tmpstring1[0]+tmpstring1[1]+playurl["Hi"]+"?"+tmpstring1[2].split('?')[1]
    #Format: addDir(name,url,mode,thumbnail, description, permlink)    
  except:
    print "DEBUG: ERROR; creating final playlist url."
  
  # Clear playlist before adding new stuff...
  playlist.clear()
  playlist.add(liveplayurl)
  xbmc.Player().play( playlist)
  while xbmc.Player().isPlaying():
    xbmc.sleep(250)
    
#  if xbmc.Player().onPlayBackStopped():

    
  xbmc.Player().stop()
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

  
# Retrieve m3u8 file, the dirty, dirty, dirty way, parse it and get and create real playlist
def playlocal(file):

  playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )

  # Clear playlist before adding new stuff...
  playlist.clear()
  #playlist.add(file)

  # Play from playlist
  xbmc.Player().play(file)
  while xbmc.Player().isPlaying():
    xbmc.sleep(250) 
  xbmc.Player().stop()
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))  
        
# Retrieve m3u8 file, the dirty, dirty, dirty way, parse it and get and create real playlist
def playurl(url):

  playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )

  # Clear playlist before adding new stuff...
  playlist.clear()
  playlist.add(getplaylisturl(url))

  # Play from playlist
  xbmc.Player().play( playlist)
  while xbmc.Player().isPlaying():
    xbmc.sleep(250) 
  xbmc.Player().stop()
    
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getplaylisturl(urlin):
  playurllow=""
  playurlhigh=""

  # Compile and retrieve redirection and right npvr server
  compiledurl='https://'+watson_addon.getSetting("username")+':'+watson_addon.getSetting("password")+'@'+urlin.split("//")[1]
  try:
    compiledurl='https://'+watson_addon.getSetting("username")+':'+watson_addon.getSetting("password")+'@'+urlin.split("//")[1]
    urllib.urlretrieve(compiledurl, tmpfile)
  except:
    print "DEBUG: Error; Error creating playlist download URL."

  # Read playlist
  try:
    fdbc=urllib.urlopen(compiledurl)
    redirection=urlparse(fdbc.url)
    redirectionNEW=redirection.geturl()
  except:
    e = sys.exc_info()[0]
    print "DEBUG: Exception: "+str(e)
    redirection=""
  
  playurl={}
  if "RSS" in urlin:
    linestring=open(tmpfile, 'r').read()
    for line in linestring.split("\n"):  
      if "01.m3u8" in line:
        playurl["Lo"]=line
      elif "02.m3u8" in line:
        playurl["Hi"]=line
	
    tmpstring1=redirectionNEW.rpartition('/')
    try:
      finalplaylist=tmpstring1[0]+tmpstring1[1]+playurl["Hi"]+"?"+tmpstring1[2].split('?')[1]
      #Format: addDir(name,url,mode,thumbnail, description, permlink)    
    except:
      print "DEBUG: ERROR; creating final archive playlist url."
	
  else:
    linestring=open(tmpfile, 'r').read()
    for line in linestring.split("\n"):   
      if "01.m3u8?session" in line:
        playurllow=line
      elif "02.m3u8?session" in line:
        playurlhigh=line

    if watson_addon.getSetting("bitrate") == 1:
      finalplaylist="http://"+watson_addon.getSetting("username")+":"+watson_addon.getSetting("password")+"@"+redirection.netloc+"/recorder/resources/"+playurllow
    elif watson_addon.getSetting("bitrate") == 0:
      finalplaylist="http://"+watson_addon.getSetting("username")+":"+watson_addon.getSetting("password")+"@"+redirection.netloc+"/recorder/resources/"+playurlhigh
    else:
      finalplaylist="http://"+watson_addon.getSetting("username")+":"+watson_addon.getSetting("password")+"@"+redirection.netloc+"/recorder/resources/"+playurlhigh

  return finalplaylist  
  
# Download selected video
def downloadvideo(durl,dname,pdesc):

  downloadurl=getplaylisturl(durl)
  print "pdesc: " + str(pdesc)

  # Get download url (playlist)
  try:
    urllib.urlretrieve(downloadurl, tmpfile2)
    fdbc=urllib.urlopen(downloadurl)
    redirection=urlparse(fdbc.url)
    redirectionNEW=redirection.geturl()
    time.sleep(1)
    linestring=open(tmpfile2)

    xbmcgui.Dialog().ok("Status","Starting to download %s in background, \n file is saved to %s. Don't turn off XBMC/Kodi!"%(dname.replace(':','-'), watson_addon.getSetting("savedir")))   	
  except:
    xbmcgui.Dialog().ok("Status","Error getting download url!")    
  # Fetch video files and create playlist from files.
 
  uriPB = xbmcgui.DialogProgress()
  downloadstring="Downloading " + dname.replace(':','-') + ", please wait..."
  uriPB.create('Downloading', downloadstring)
  
  savedir=watson_addon.getSetting("savedir")+dname.replace(':','-')
  savedir=savedir.replace('(','')
  savedir=savedir.replace(')','')
  savedir=savedir.replace(' ','_')+".ts"
  savedir=savedir.replace('&#228;','a')
  savedir=savedir.replace("&#246;","o")
  savedir=savedir.replace('&amp;','_')

  playing=0
  ifds=0
  progresslines=0
  progresslines=sum(1 for line in open(tmpfile2))
  progress=1 
  # Update progress bar
  totalprogress = int((progress / round(float(progresslines),2)) * 100)

  uriPB.update(totalprogress, 'Downloading...')
  progress = progress + 1

  try:  
    finaldurl=""
    #print "Lines: " + str(sum(1 for ".ts" in linestring))
    # How many video files is in playlist

    if playing==0:
      for line in iter(linestring):

        if "ts" in line:
          # Update progress bar
          totalprogress = int((progress / round(float(progresslines),2)) * 100)
          uriPB.update(totalprogress, downloadstring)
          progress = progress + 1
		  
          tmpstring1=redirectionNEW.rpartition('/')
          finaldurl=tmpstring1[0]+tmpstring1[1]+line.replace("\n", "")+"?"+tmpstring1[2].split('?')[1]

        if finaldurl and not finaldurl.isspace() and "ts" in line:
		  
          wwwfile=urllib.urlopen(finaldurl)
          # Open local file for writing (append)...
          localfile=open(savedir, 'ab+')
          # Write remote file to local file...
          localfile.write(wwwfile.read())        
          print "...downloading " + line + "..."
          localfile.close()
       
    print "...downloading completed!"
    xbmcgui.Dialog().ok("Status","Download completed for %s !"%(savedir))    
  except:
    print "Status","Error fetching video files!"    
 
  # added 9.2
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
          
def get_params():
  param=[]
  paramstring=sys.argv[2]
    
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
      
    pairsofparams=cleanedparams.split('&')
    
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
        
    if paramstring.endswith("mode=9"):
      print "AB"
      downloadurl=paramstring.split('=')[1]+"="+paramstring.split('=')[2]+"="+paramstring.split('=')[3]+"="+paramstring.split('=')[4].split('&')[0]
      print "AB"
      param.update({'url' : downloadurl })
      
  return param

  
# Main program
params=get_params()
url=None
name=None
mode=None
plink=None
pdesc=None
LoginError=True
# Try to get XML list
try:
  cookiejar=cookielib.CookieJar()
  auth_handlerb = urllib2.HTTPPasswordMgrWithDefaultRealm()
  auth_handlerb.add_password(None, "http://www.watson.fi", watson_addon.getSetting("username"), watson_addon.getSetting("password"))
  opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(auth_handlerb),urllib2.HTTPCookieProcessor(cookiejar))
  request = urllib2.Request(url_archive, headers=MYHEADERS)
  urllib2.install_opener(opener)
  content = opener.open(request).read()
  
  # Save everyhing we need to tuples...
  match=re.compile('<title\>(.+?)<\/title\>\n            <description\>(.+?)<\/description\>\n                    <dc:date\>(.+?)<\/dc:date\>\n            <link\>(.+?)<\/link\>\n            <guid isPermaLink="(.+?)"\>(.+?)<\/guid\>\n            <source url="(.+?)"\>(.+?)<\/source\>\n                                        <media:content url="(.+?)" medium="(.+?)" type="(.+?)" fileSize="(.+?)" expression="(.+?)" duration="(.+?)"\/\>\n                    <media:status  state="(.+?)"  reason="(.+?)" \/\>\n            <media:community\><media:starRating average="(.+?)"  min="(.+?)" max="(.+?)"\/\><\/media:community\>\n                    <media:thumbnail url="(.+?)" height="(.+?)" width="(.+?)"\/\>').findall(content)

  LoginError=False
except:
  print "Error opening XML"
  LoginError=True
  

# Get 'url'
try:
  url=urllib.unquote_plus(params["url"])
except:
  pass
  

# Get 'name'
try:
  name=urllib.unquote_plus(params["name"])
except:
  pass

# Get 'pdesc', plot / description
try:
  pdesc=urllib.unquote_plus(params["pdesc"])
except:
  pass

try:
  plink=urllib.unquote_plus(params["plink"])
except:
  pass        
  
try:
  mode=int(params["mode"])
except:
  pass

try:
  year=int(params["year"])
except:
  pass

try:
  month=int(params["month"])
except:
  pass

try:
  day=int(params["day"])
except:
  pass

try:
  channel=int(params["channel"])
except:
  pass

if mode==None or url==None or len(url)<1:
  settings()

# Show main menu, livetv / archive / search programs / search recordings
elif mode==0:
  INDEX()

# LiveTV
elif mode==1:
  channellist('https://www.watson.fi/pctv/RSS?action=getavailableretvchannels', 'live')

# Archive
elif mode==2:
  programs('https://www.watson.fi/pctv/RSS?action=getfavoriterecordings')
  
# Archive episodelist
elif mode==3:
  episodelist(url,name)
  
# Play from download url...
elif mode==4:
  playurl(url)

# Show settings if not defined or something wrong...
elif mode==5:
  watson_addon.openSettings(url=sys.argv[0])  

# Play live feed
elif mode==6:
  playlive(url)

# Search records
elif mode==7:
  search(url)  
  
# Add recording to favorites / recordings
elif mode==8:  
  addrecording(name,plink)
  
# Download video
elif mode==9:
  print "mode==9, URL: " + url
  print "mode==9, name: " + name
  print "mode==9, pdesc: " + pdesc
  downloadvideo(url,name,pdesc)
  
# Remove video
elif mode==10:
  removerecording(name,plink)  

# Show all movies (archive + last two weeks from ReTV channels
elif mode==11:
  showmovies(url) 

# Show all movies (archive + last two weeks from ReTV channels
#elif mode==12:
#  testing(url) 

elif mode==13:
  channellist('https://www.watson.fi/pctv/RSS?action=getactiveretvchannels','rec') 

elif mode==14:
  searchrec("https://www.watson.fi/pctv/RSS?action=getrecordings&channel=%d&year=%d&month=%d&day=%d"% (channel,year,month,day)) 
  
xbmcplugin.endOfDirectory(int(sys.argv[1]))
