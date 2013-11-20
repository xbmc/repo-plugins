import xbmc, xbmcgui, xbmcplugin, xbmcaddon, sys, urllib2, time, urlparse, os
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

Settings = xbmcaddon.Addon('plugin.video.enigmatv')
cache_dir = os.path.join(xbmc.translatePath(Settings.getAddonInfo('profile')), 'cache')
if not os.path.isdir(cache_dir):

   os.makedirs(cache_dir)
XMLFile = os.path.join(cache_dir, 'data.xml')

print 'Cache Dir = ' + cache_dir

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

OK = True

def save_data(txt, temp):
   try:
      file(temp, 'w').write(repr(txt))
   except:
      print 'Error while saving data %s' % temp

def addItem(caption, link, icon=None, thumbnail=None, folder=False):
   ProviderItem = xbmcgui.ListItem(unicode(caption))
   ProviderItem.addContextMenuItems([('Context', 'XBMC.RunScript()',),])
   ProviderItem.setInfo(type='Video', infoLabels={ 'Title': caption })
   ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=link, listitem=ProviderItem, isFolder=folder)
   return ok

def end_of_directory(OK):

   xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=OK)

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

def createProvList(url):
   print 'Creating Providers list'
   try:
      response = urllib2.urlopen(url)
      if response and response.getcode() == 200:
         xml = response.read()
         save_data(xml,XMLFile)
         print xml
         xmlstr = minidom.parseString(xml)

      createArrays(xmlstr)

      for index in range(len(PIDs)):
         addItem(PNames[index], 'plugin://plugin.video.enigmatv/?mode=GetChannels&ProvID='+PIDs[index], '', '', True)

      end_of_directory(OK)

   except Exception, e:
      print 'Error connecting to the Server : ' + str(e)
      xbmcgui.Dialog().ok(Error10,Error11,Error12,Error13)

def createChanList(ProvID):
   print 'Creating Channels list with ProvID = ' + str(ProvID)
   xml = eval(file(XMLFile, 'r').read())
   xmlstr = minidom.parseString(xml)
   createArrays(xmlstr)
   for index in range(len(PCIDs)):
      if int(PCIDs[index]) == int(ProvID):
         addItem(CNames[index], 'plugin://plugin.video.enigmatv/?mode=SetChannels&ProvID='+str(PCIDs[index])+'&ChanID='+str(CIDs[index])+'&ChanName='+str(CNames[index]), '', '', False)
         print CNames[index]

def SetChannel(ProvID, ChanID, ChanName):

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

   print 'SID = ' + str(SID)

   url = 'http://'+str(IP)+':'+str(WebPort)+'/CMD.php?FNC=SETTV&PID='+str(ProvID)+'&CID='+str(ChanID)+'&TV=1&PASSWORD='+str(Password)+'&SID='+str(SID)+'&VTYPE=1&OS=XBMC&VB='+str(VB)+'&VS='+str(VS)+'&AB='+str(AB)+'&AC='+str(AC)
   print 'URL = ' + str(url)

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
               icon = addon.getAddonInfo('icon')
               li = xbmcgui.ListItem(label=ChanName, iconImage=icon, thumbnailImage=icon, path=StreamURL)
               li.setInfo(type='Video', infoLabels={ 'Title': ChanName })
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
         print 'Setting Channel = ProvID:' + str(ProvID) + ', ChanID:' + str(ChanID) + ', ChanName:' + str(ChanName)
         SetChannel(ProvID, ChanID, ChanName)
         end_of_directory(OK)

   else:
      print 'Loading XML from URL'
      createProvList(GetURL)

         
