#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, locale, sys, urllib, urllib2, re, os

addonID = "plugin.program.akinator_com"
settings = xbmcaddon.Addon(id=addonID)
translation = settings.getLocalizedString

languages=['en','de','fr','it','es','ru','il','pt','ar','jp','tr']
language=""
nick=settings.getSetting("nick")
age=settings.getSetting("age")
if settings.getSetting("language")!="":
  language=languages[int(settings.getSetting("language"))]
if language=="" or nick=="" or age=="":
  settings.openSettings()
  language=languages[int(settings.getSetting("language"))]
  nick=settings.getSetting("nick")
  age=settings.getSetting("age")

def akinatorMain():
        content=getUrl("http://"+language+".akinator.com/new_session.php?prio=0&joueur="+nick+"&partner_id=0&age="+age+"&sexe=&email=&ms=0&remember=0&engine=0")
        match=re.compile('<br>(.+?)<', re.DOTALL).findall(content)
        question=match[0]
        match=re.compile('&partie=(.+?)&', re.DOTALL).findall(content)
        partie=match[0]
        match=re.compile('&signature=(.+?)&', re.DOTALL).findall(content)
        signature=match[0]
        dialog = xbmcgui.Dialog()
        modes=[translation(30001),translation(30002),translation(30003),translation(30004),translation(30005)]
        nr=dialog.select(question, modes)
        if nr>=0:
          mode = modes[nr]
          if mode==translation(30001):
            nextQuestion(partie, signature, "0", 0)
          elif mode==translation(30002):
            nextQuestion(partie, signature, "3", 0)
          elif mode==translation(30003):
            nextQuestion(partie, signature, "2", 0)
          elif mode==translation(30004):
            nextQuestion(partie, signature, "4", 0)
          elif mode==translation(30005):
            nextQuestion(partie, signature, "1", 0)

def nextQuestion(partie, signature, answer, qNr, continued=False):
        if continued==False:
          content=getUrl("http://"+language+".akinator.com/repondre_propose.php?prio=0&partie="+partie+"&signature="+signature+"&nqp="+str(qNr)+"&trouvitude=0&reponse="+answer+"&step_prop=-1&fq=&engine=0")
        elif continued==True:
          content=getUrl("http://"+language+".akinator.com/continue_partie.php?prio=0&partie="+partie+"&signature="+signature+"&nqp="+str(qNr)+"&age="+age+"&engine=0")
        if content.find("</center>")>=0:
          match=re.compile('</center>(.+?)\n<', re.DOTALL).findall(content)
          question=match[0]
          if question.find("<")>=0:
            question=question[:question.find("<")]
          qNr+=1
          dialog = xbmcgui.Dialog()
          modes=[translation(30001),translation(30002),translation(30003),translation(30004),translation(30005)]
          nr=dialog.select(question, modes)
          if nr>=0:
            mode = modes[nr]
            if mode==translation(30001):
              nextQuestion(partie, signature, "0", qNr)
            elif mode==translation(30002):
              nextQuestion(partie, signature, "3", qNr)
            elif mode==translation(30003):
              nextQuestion(partie, signature, "2", qNr)
            elif mode==translation(30004):
              nextQuestion(partie, signature, "4", qNr)
            elif mode==translation(30005):
              nextQuestion(partie, signature, "1", qNr)
        elif content.find("ouvre_photo(")>=0:
          match=re.compile('ouvre_photo\\("(.+?)",(.+?),"(.+?)"', re.DOTALL).findall(content)
          photo="http://"+language+".akinator.com/"+match[0][0]
          name=match[0][2]
          match=re.compile("id='contenu'>\n\n      (.+?)\n", re.DOTALL).findall(content)
          message=match[0]
          xbmc.executebuiltin('XBMC.Notification(Akinator: '+message+', '+name+' ?, 15000, '+photo+')')
          dialog = xbmcgui.Dialog()
          yesNo=dialog.yesno("Akinator: "+message, name+" ?")
          if yesNo==True:
            dialog = xbmcgui.Dialog()
            yesNo=dialog.yesno("Akinator:", translation(30006)+" ?")
            if yesNo==True:
              akinatorMain()
          elif yesNo==False:
            qNr+=1
            nextQuestion(partie, signature, "", qNr, True)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

akinatorMain()