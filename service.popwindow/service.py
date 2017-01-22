#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, sys, os, urlparse
import xbmc ,xbmcgui, xbmcaddon,xbmcvfs
import urllib2,urllib,json
import re,md5,shutil
import socket, cookielib
from datetime import datetime



__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addondir__    = xbmc.translatePath( __addon__.getAddonInfo('path') )
background = os.path.join(__addondir__,"bg.png")

profile    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
translation = __addon__.getLocalizedString
  
wid = xbmcgui.getCurrentWindowId()
window=xbmcgui.Window(wid)
window.show()

try:
  if xbmcvfs.exists(temp):
    shutil.rmtree(temp)
  xbmcvfs.mkdirs(temp)
except:
  pass
       
# Einlesen von Parametern, Notwendig für Reset der Twitter API
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def geturl(url):
   req = urllib2.Request(url)
   inhalt = urllib2.urlopen(req).read()   
   return inhalt   
   
def showMessage(Message,image1="",image2="",greyout="true",lesezeit=10,xmessage=110,ymessage=5,breitemessage=1170,hoehemessage=100,startxbild1=-1,startybild1=-1,breitebild1=100,hoehebild1=100,startxbild2=-1,startybild2=-1,breitebild2=100,hoehebild2=100,fontname="font14",fontcolor="FFFFFFFF"):
    global alles_anzeige
    global urlfilter
    global background
    global window
    #tw=unicode(Message).encode('utf-8')  
    debug("image1 "+ image1)
    debug("image2 "+ image2)
    debug("breitebild2 "+ breitebild2)
    if int(startxbild1)==-1:
        startxbild1=int(xmessage)
    if int(startybild1)==-1:
        startybild1=int(ymessage)
    if int(startxbild2)==-1:
        startxbild2=int(breitemessage)-int(breitebild2)
    if int(startybild2)==-1:
        startybild2=int(ymessage)
#    if  image1=="":
#        breitebild1=0
#    if  image2=="":
 #      breitebild2=0        
    tw=Message        
    tw=tw.replace("&amp;","&")    
    xbmc.log("showMessage")
    wid = xbmcgui.getCurrentWindowId()
    window=xbmcgui.Window(wid)
    res=window.getResolution()        
    if greyout=="true":
       bg=xbmcgui.ControlImage(0,int(ymessage),10000,int(hoehemessage),"")
       bg.setImage(background)
       window.addControl(bg)
    x=int(xmessage)+int(breitebild1 )
    debug("X : "+ str(xmessage))
    debug("Y : "+ ymessage)
    debug("Breite : "+breitemessage)
    debug("hoehe : "+hoehemessage)
    debug("BildBreite1 : "+str(breitebild1))
    debug("hoehebild1 : "+str(hoehebild1))
    debug("BildBreit2 : "+str(breitebild2))
    debug("hoehebild2 : "+str(hoehebild2))
    debug("Text : "+tw)    
    debug("Font : "+fontname) 
    fontcolor='0x'+fontcolor
    debug("FontColor : "+fontcolor)    
    twitterlabel1=xbmcgui.ControlTextBox (x, int(ymessage), int(breitemessage)- (x+int(breitebild2)), int(hoehemessage),textColor=fontcolor,font=fontname)        
    window.addControl(twitterlabel1)    
    twitterlabel1.setText(tw)
    debug("XYXYXY :"+ str(hoehebild1))
    avatar1=xbmcgui.ControlImage(int(startxbild1),int(startybild1),int(breitebild1),int(hoehebild1),"")
    avatar1.setImage(image1)
    avatar2=xbmcgui.ControlImage(int(startxbild2),int(startybild2),int(breitebild2),int(hoehebild2),"")
    avatar2.setImage(image2)
    window.addControl(avatar1)        
    window.addControl(avatar2)        
    debug("Lesezeit :"+ lesezeit)
    time.sleep(int(lesezeit))
        
    window.removeControl(twitterlabel1)
   
    window.removeControl(avatar1)
    window.removeControl(avatar2)
    if greyout=="true":
       window.removeControl(bg)
      
        
           
if __name__ == '__main__':
    temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
    monitor = xbmc.Monitor()       
    while not monitor.abortRequested():
      start=datetime.now()
      text=[]
      image=[]
      greyout=[]
      fileliste=[]
      datumliste=[]
      dirs, files = xbmcvfs.listdir(temp)      
      delete=0
      deletefile=""
      module=""
      for name in files:  
          pf=os.path.join( temp, name)     
          zeit=os.path.getctime(pf)
          fileliste.append(name)
          if "DELETE" in name:
             delete=1
             deletefile=name
             teile=deletefile.split("_")          
             module=teile[1]
          datumliste.append(zeit)              
      if len(datumliste) > 0:
        datumliste,fileliste = (list(x) for x in zip(*sorted(zip(datumliste,fileliste))))
        if delete==1:            
          ende=0      
          x=0          
          for file in fileliste :              
              if module in file  and ende==0:
                  fileliste.pop(x)
                  datumliste.pop(x)
                  xbmcvfs.delete(temp+"/"+file)                  
                  debug("Delete file :"+file)
                  if "DELETE" in file:
                     ende=1
                     debug("Delete ende")
                  x=x+1
        count=0                
        for name in fileliste:
          if count >4:
             break
          count=count+1                                  
          debug("File :" + name)
          try:
            f = open(temp+"/"+name, 'r')    
            for line in f:                       
                message,image1,grey,lesezeit,xmessage,ymessage,breitemessage,hoehemessage,startxbild1,startybild1,breitebild1,hoehebild1,image2,startxbild2,startybild2,breitebild2,hoehebild2,fontname,fontcolor=line.split("###")    
                message=message.replace("#n#","\n")                                 
                showMessage(message,image1=image1,image2=image2,greyout=grey,lesezeit=lesezeit,xmessage=xmessage,ymessage=ymessage,breitemessage=breitemessage,hoehemessage=hoehemessage,startxbild1=startxbild1,startybild1=startybild1,breitebild1=breitebild1,hoehebild1=hoehebild1,startxbild2=startxbild2,startybild2=startybild2,breitebild2=breitebild2,hoehebild2=hoehebild2,fontname=fontname,fontcolor=fontcolor)
            f.close()           
            xbmcvfs.delete(temp+"/"+name)                    
          except:
             pass
      xbmc.log("Hole Umgebung")        
      end=datetime.now()
      diff=int((end-start).seconds)
      warten=20-diff
      if warten < 1:
        warten=1
      debug("######  Warten : "+str(warten))
      if monitor.waitForAbort(warten):
        break            
           

