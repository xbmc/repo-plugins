import xbmc, xbmcgui, xbmcplugin, xbmcaddon, sys, urllib2, datetime, time, threading, urlparse, os, urllib, re, zipfile, random
from xml.dom import Node, minidom
from random import randint



global mode
global GetURL
global IP
global WebPort
global StreamPort
global Password
global VB
global VS
global AB
global AC
global xml
global SID
global PICON
global epgtextarray




Settings = xbmcaddon.Addon('plugin.video.enigmatv')
cache_dir = unicode(os.path.join(xbmc.translatePath(Settings.getAddonInfo('profile')), 'cache'),'utf-8')
if not os.path.isdir(cache_dir):

   os.makedirs(cache_dir)
XMLFile = os.path.join(cache_dir, 'data.xml')

picon_dir = unicode(os.path.join(xbmc.translatePath(Settings.getAddonInfo('profile')), 'picons'),'utf-8')
if not os.path.isdir(picon_dir):

   os.makedirs(picon_dir)
PICONFile = os.path.join(picon_dir, 'picons.zip')

#view-mode
current_skin = xbmc.getSkinDir();
if 'confluence' in current_skin:
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'
thumbViewMode = 'Container.SetViewMode(500)'
smallListViewMode = 'Container.SetViewMode(51)'

IP = str(Settings.getSetting('IPServer'))
WebPort = str(Settings.getSetting('WebPort'))
StreamPort = str(Settings.getSetting('StreamPort'))
Password = str(Settings.getSetting('Password'))
VB = int(Settings.getSetting('VB'))
VS = int(Settings.getSetting('VS'))
AB = int(Settings.getSetting('AB'))
AC = int(Settings.getSetting('AC'))


language = Settings.getLocalizedString

Error10 = str(language(30009).encode('utf-8'))
Error11 = str(language(30010).encode('utf-8'))
Error12 = str(language(30011).encode('utf-8'))
Error13 = str(language(30012).encode('utf-8'))

Error20 = str(language(30013).encode('utf-8'))
Error21 = str(language(30014).encode('utf-8'))

Error30 = str(language(30015).encode('utf-8'))
Error31 = str(language(30016).encode('utf-8'))

Error40 = str(language(30017).encode('utf-8'))
Error41 = str(language(30018).encode('utf-8'))

GetURL = 'http://'+IP+':'+WebPort+'/CMD.php?FNC=GETCHANNELS&PASSWORD='+Password

mode = 'init'
PNames = []
PIDs = []
CNames = []

CIDs = []
PCIDs = []
Picons = []

epgtextDict = {}


CEPGs = []
CEPGsDescription = []
CEPGsStart = []
CEPGsEnd = []
CEPGsDuration = []
CEPGsNEXT = []
CEPGsNEXTDescription = []
CEPGsNEXTStart = []
CEPGsNEXTEnd = []
CEPGsNEXTDuration = []


OK = True

addon = xbmcaddon.Addon('plugin.video.enigmatv')



def save_data(txt, temp):
   try:
      file(temp, 'w').write(repr(txt))
   except:
      print 'Error while saving data %s' % temp


def addItem(caption, link, epg, description, epgstart, epgend, epgduration, epgnext, descriptionnext, epgnextstart, epgnextend, epgnextduration, icon=None, thumbnail=None, folder=False):
   try:
      ProviderItem = xbmcgui.ListItem(unicode(caption, "ascii"), icon, icon)
   except UnicodeError:
      ProviderItem = xbmcgui.ListItem(unicode(caption, "utf-8"), icon, icon)

   epgtext = description
   epgtextNext = descriptionnext
   epgnowtext = (language(40002)).encode("utf-8")
   epgnextext = (language(40003)).encode("utf-8")
   epgdescriptiontext = (language(40004)).encode("utf-8")
   btnshowepginfo = (language(40005)).encode("utf-8")
   btnshowepginfoNEXT = (language(40006)).encode("utf-8")

   epgstillrunningtimeoutput = ""

   timenowH = (time.strftime("%H"))
   timenowM = (time.strftime("%M"))

   timenowH = int(timenowH)*60
   timenowM = int(timenowM)
   timenowMs = timenowH+timenowM
   print "timenowMs: " + str(timenowMs)

   if epgend != "":
      timeepgendH = epgend[0:2]
      timeepgendM = epgend[-2:]

      if timeepgendH == "00":
         timeepgendH = "0"
      if timeepgendM == "00":
         timeepgendM = "0"
      timeepgendH = int(timeepgendH)*60
      timeepgendM = int(timeepgendM)
      timeepgendMs = timeepgendH+timeepgendM
      print "timeepgendMs: " + str(timeepgendMs)

      epgdiff=timeepgendMs-timenowMs

      if epgdiff < 0:
         epgdiff = 1440-epgdiff

      if epgdiff < 720:
         epgstillrunningtimeoutput = " (+"+str(epgdiff)+" min)"
      else:
         epgstillrunningtimeoutput = ""



   if epgstart == "" or epgend == "":
      epgnowtime = ""
   else:
      epgnowtime = " " + epgstart + " - " + epgend

   if epgnextstart == "" or epgnextend == "":
      epgnexttime = ""
   else:
      epgnexttime = " " + epgnextstart + " - " + epgnextend

   if epgnextduration != "":
      epgnextduration = " (" + epgnextduration + " min)"

   
   epg = shortnstring(epg)
   epgnext = shortnstring(epgnext)

   if epgtext == '' or epgtext == 'None' or epgnext == ' ':
      epgtext = (language(40001)).encode("utf-8")
   description = epgnowtext + epgnowtime + epgstillrunningtimeoutput + '\r\n' + epg + '\r\n\r\n' + epgnextext + epgnexttime + epgnextduration + '\r\n' + epgnext

   if folder==True:
      description = ''

   if folder==False:
      ProviderItem.addContextMenuItems([(btnshowepginfo, unicode('XBMC.RunScript(special://home/addons/plugin.video.enigmatv/epgdescriptiondialog.py,'+epgdescriptiontext+epgtext+', '+epgnowtext+epg+')','utf-8')), (btnshowepginfoNEXT, unicode('XBMC.RunScript(special://home/addons/plugin.video.enigmatv/epgdescriptiondialog.py,'+epgdescriptiontext+epgtextNext+', '+epgnextext+epgnext+')','utf-8'))])

   ProviderItem.setInfo( type="Video", infoLabels={ "Title": unicode(caption, "utf-8") } )
   ProviderItem.setInfo( type="Video", infoLabels={ "Plot": description } )
   ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=link, listitem=ProviderItem, isFolder=folder)
   return ok

def shortnstring (text):
   size=50
   info = text[0:size]
   if len(info) == size:
      info = info+"..."
   return info


def end_of_directory(OK):
   xbmcplugin.setContent(int(sys.argv[1]),'episodes')
   xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=OK, updateListing=False, cacheToDisc=False)
   xbmc.executebuiltin(defaultViewMode)

def createArrays(xml):
   for providers in xml.getElementsByTagName('EnigmaTVProvider'):
      PNames.append(providers.getAttribute('Name').encode('utf8'))
      currentPID = providers.getAttribute('ID').encode('utf8')
      PIDs.append(currentPID)
      CurrentCID = 0
      for channels in providers.getElementsByTagName('EnigmaTVChannel'):
         CurrentCID = CurrentCID + 1
         PCIDs.append(currentPID)
         CIDs.append(CurrentCID)
         CNames.append(channels.getAttribute('Name').encode('utf8'))

         CEPGs.append(channels.getAttribute('EPG').encode('utf8'))
         CEPGsDescription.append(channels.getAttribute('EPGDesc').encode('utf8'))
         CEPGsStart.append(channels.getAttribute('EPGStart').encode('utf8'))
         CEPGsEnd.append(channels.getAttribute('EPGEnd').encode('utf8'))
         CEPGsDuration.append(channels.getAttribute('EPGDuration').encode('utf8'))


         CEPGsNEXT.append(channels.getAttribute('EPGNext').encode('utf8'))
         CEPGsNEXTDescription.append(channels.getAttribute('EPGNextDesc').encode('utf8'))
         CEPGsNEXTStart.append(channels.getAttribute('EPGNextStart').encode('utf8'))
         CEPGsNEXTEnd.append(channels.getAttribute('EPGNextEnd').encode('utf8'))
         CEPGsNEXTDuration.append(channels.getAttribute('EPGNextDuration').encode('utf8'))

         Picons.append(channels.getAttribute('PiconID').encode('utf8'))
         

def createProvList(url):
   print 'Creating Providers list'
   try:
      response = urllib2.urlopen(url)
      if response and response.getcode() == 200:
         xml = response.read()
         save_data(xml,XMLFile)
         #print xml
         xmlstr = minidom.parseString(xml)

      createArrays(xmlstr)

      for index in range(len(PIDs)):
         addon = xbmcaddon.Addon('plugin.video.enigmatv')
         piconx = os.path.join(addon.getAddonInfo('path'), 'defaultpicon.png')
         addItem(PNames[index], 'plugin://plugin.video.enigmatv/?mode=GetChannels&ProvID='+PIDs[index], '', '', '', '', '', '', '', '', '', '', piconx, piconx, True)

      end_of_directory(OK)
      


   except Exception, e:
      print 'Error connecting to the Server : ' + str(e)
      xbmcgui.Dialog().ok(Error10,Error11,Error12,Error13)

def createChanList(ProvID):
   print 'Creating Channels list with ProvID = ' + str(ProvID)
   response = urllib2.urlopen(GetURL)
   if response and response.getcode() == 200:
      xml = response.read()
      save_data(xml,XMLFile)
      #print xml
      xmlstr = minidom.parseString(xml)

   createArrays(xmlstr)

   
   for xxx in range(len(CEPGs)):
      if CEPGs[xxx]=="":
         CEPGs[xxx] = (language(40001)).encode("utf-8")
   for xxx in range(len(CEPGsDescription)):
      if CEPGsDescription[xxx]=="":
         CEPGsDescription[xxx] = (language(40001)).encode("utf-8")

   for xxx in range(len(CEPGsNEXT)):
      if CEPGsNEXT[xxx]=="":
         CEPGsNEXT[xxx] = (language(40001)).encode("utf-8")
   for xxx in range(len(CEPGsNEXTDescription)):
      if CEPGsNEXTDescription[xxx]=="":
         CEPGsNEXTDescription[xxx] = (language(40001)).encode("utf-8")


   for index in range(len(PCIDs)):
      if int(PCIDs[index]) == int(ProvID):
         addon = xbmcaddon.Addon('plugin.video.enigmatv')
         folder = picon_dir
         the_file = Picons[index]+'.png'
         file_path = os.path.join(folder, the_file)
         if os.path.isfile(file_path):
            piconx = os.path.join(picon_dir, the_file)
         else:
            piconx = os.path.join(addon.getAddonInfo('path'), 'defaultpicon.png')

         addItem("[B]"+CNames[index] +"[/B]           "+ CEPGs[index]+'      ', 'plugin://plugin.video.enigmatv/?mode=SetChannels&ProvID='+str(PCIDs[index])+'&ChanID='+str(CIDs[index])+'&ChanName='+str(CNames[index])+'&ChanEPG='+str(CEPGs[index])+'&ChanEPGNEXT='+str(CEPGsNEXT[index])+'&ChanPicon='+str(Picons[index])+'&ChanDescription='+str(CEPGsDescription[index]), CEPGs[index], CEPGsDescription[index], CEPGsStart[index], CEPGsEnd[index], CEPGsDuration[index], CEPGsNEXT[index], CEPGsNEXTDescription[index], CEPGsNEXTStart[index], CEPGsNEXTEnd[index], CEPGsNEXTDuration[index], piconx, piconx, False)
         #print CNames[index] + " EPGNOW: "+ CEPGs[index]
   


def SetChannel(ProvID, ChanID, ChanName, ChanEPG, ChanEPGNEXT, ChanPicon, ChanDescription):

   xbmc.executebuiltin('ActivateWindow(busydialog)')

   IsStopRetry = 0
   while True:
      xbmc.Player().stop()
      time.sleep(2)
      IsStopRetry = IsStopRetry + 1
      if xbmc.Player().isPlaying()==False or IsPlayRetry==10:
         break

   SID = ''
   for index in range(20):
      SID = SID + str(randint(1,9))

   #print 'SID = ' + str(SID)

   url = 'http://'+str(IP)+':'+str(WebPort)+'/CMD.php?FNC=SETTV&PID='+str(ProvID)+'&CID='+str(ChanID)+'&TV=1&PASSWORD='+str(Password)+'&SID='+str(SID)+'&VTYPE=1&OS=XBMC&VB='+str(VB)+'&VS='+str(VS)+'&AB='+str(AB)+'&AC='+str(AC)
   #print 'URL = ' + str(url)

   IsOkSETTV = 1


   try:
      print 'Sending SETTV command to the server'
      response = urllib2.urlopen(url, timeout=3)
   except Exception, e:
      IsOkSETTV = 0
   
   if IsOkSETTV==1:
      if response and response.getcode() == 200:
         checkurl = 'http://'+str(IP)+':'+str(StreamPort)+'/'+str(SID)+'_stream.flv'
         IsCheckOK = 0
         DoRetry = 0
      
         while True:
            DoRetry = DoRetry + 1
            try:
               time.sleep(3)
               streamcheck = urllib2.urlopen(checkurl, timeout=3)
               IsCheckOK = 1
            except Exception, e:
               print 'Stream not yet ready, retry '+str(DoRetry)+'/10'
      
            if IsCheckOK==1 or DoRetry==10:
               break

         if IsCheckOK==1:
            IsOkXBMC=1
            try:
               
               StreamURL=str(checkurl)
               print 'Stream URL = ' + StreamURL
               addon = xbmcaddon.Addon('plugin.video.enigmatv')

               folder = picon_dir
               the_file = ChanPicon+'.png'
               file_path = os.path.join(folder, the_file)
               if os.path.isfile(file_path):
                  piconx = os.path.join(addon.getAddonInfo('profile'), 'picons', the_file)
               else:
                  piconx = os.path.join(addon.getAddonInfo('path'), 'defaultpicon.png')

               li = xbmcgui.ListItem(label=ChanName, iconImage=piconx, thumbnailImage=piconx, path=StreamURL)
               li.setInfo(type='Video', infoLabels={ 'Title': ChanName})
               li.setProperty('IsPlayable', 'true')
               xbmc.Player().play(item=StreamURL, listitem=li)

            except Exception, e:
               IsOkXBMC=0

            if IsOkXBMC==1:
               IsPlayRetry=0
               while True:
                  time.sleep(2)
                  IsPlayRetry = IsPlayRetry + 1
                  if xbmc.Player().isPlaying()==True or IsPlayRetry==10:
                     break

               xbmc.executebuiltin('Dialog.Close(busydialog)')
         
               if xbmc.Player().isPlaying()==True:
                  print 'XBMC should now play the channel !'
                  while True:
                     time.sleep(2)
                     if xbmc.Player().isPlaying()==False:
                        break

                  print 'Video Has Stopped !'    

                  try:
                     if xbmc.Player().isPlaying()==False:
                        url = 'http://'+str(IP)+':'+str(WebPort)+'/CMD.php?FNC=SETTV&PASSWORD='+str(Password)+'&OS=TVOFF'
                        print 'Stop video stream with URL = ' + str(url)
                        response = urllib2.urlopen(url)
                  except:
                     pass
            else:
               try:
                  url = 'http://'+str(IP)+':'+str(WebPort)+'/CMD.php?FNC=SETTV&PASSWORD='+str(Password)+'&OS=TVOFF'
                  print 'Stop video stream with URL = ' + str(url)
                  response = urllib2.urlopen(url)
               except:
                  pass

               xbmc.executebuiltin('Dialog.Close(busydialog)')
               print 'Error playing the Stream in XBMC Media Player !'
               xbmcgui.Dialog().ok(Error20,Error21)

         else:
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            print 'Error connecting to the Stream (cannot play) !'
            xbmcgui.Dialog().ok(Error30,Error31)

   else:
      xbmc.executebuiltin('Dialog.Close(busydialog)')
      print 'Error sending SETTV command ...'
      xbmcgui.Dialog().ok(Error40,Error41)


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0: len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

#Need to make a sleep of 1 sec, this not to reload the XML from the URL ...
time.sleep(1)

if len(sys.argv) >= 2:

   if sys.argv[2] != '':
      params = get_params()
      print 'My Vars = ', params
      mode = params['mode']
      print 'My Mode = ' + str(mode)

      if mode == 'GetChannels':
         ProvID = params['ProvID']
         print 'Calling Channels = ', ProvID
         createChanList(ProvID)
         end_of_directory(OK)
  
      if mode == 'SetChannels':
         ProvID = params['ProvID']
         ChanID = params['ChanID']
         ChanName = params['ChanName']
         ChanEPG = params['ChanEPG']
         ChanEPGNEXT = params['ChanEPGNEXT']
         ChanPicon = params['ChanPicon']
         ChanDescription = params['ChanDescription']
         print 'Setting Channel = ProvID:' + str(ProvID) + ', ChanID:' + str(ChanID) + ', ChanName:' + str(ChanName) + ', ChanEPG:' + str(ChanEPG) + ', ChanPicon:' + str(ChanPicon) + ', ChanDescription:' + str(ChanDescription)
         SetChannel(ProvID, ChanID, ChanName, ChanEPG, ChanEPGNEXT, ChanPicon, ChanDescription)
         end_of_directory(OK)


   else:
      print 'Loading XML from URL'
      createProvList(GetURL)




