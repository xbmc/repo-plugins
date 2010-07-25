import urllib,urllib2,re,xbmcplugin,xbmcgui

#Fox News Video- by Redeyed

                       
def INDEX(url):
        addDir('01. Latest Video','87249',20,'')
        addDir('02. Hot Topics','http://video.foxnews.com/',2,'')
        addDir('03. News','http://video.foxnews.com/',3,'')
        addDir('04. Entertainment','http://video.foxnews.com/',4,'')
        addDir('05. Business','http://video.foxnews.com/',5,'')
        addDir('06. Health','http://video.foxnews.com/',6,'')
        addDir('07. Shows','http://video.foxnews.com/',7,'')
        addDir('08. Opinion','http://video.foxnews.com/',8,'')
        addDir('09. Sports','http://video.foxnews.com/',9,'')
        addDir('10. Leisure','http://video.foxnews.com/',10,'')
        addDir('11. Howcast','http://video.foxnews.com/',11,'')
        addDir('12. Strategy Room','http://video.foxnews.com/',12,'')
        addDir('13. Web Originals','86994',20,'')
        addDir('14. FNC iMag','http://video.foxnews.com/',13,'')
        addDir('15. FOX News Radio','http://video.foxnews.com/',14,'')
        addDir('16. FOX Fan','http://video.foxnews.com/',15,'')
                       
#Hot Topics                                                     
def INDEX2(url):
        addDir('01. 2009 in Review','87281',20,'') 
        addDir('02. On the Job Hunt','87282',20,'')
        addDir('03. Afghanistan','87283',20,'')
        addDir('04. Health Care','87284',20,'')
        addDir('05. Global Warming','87285',20,'')
        addDir('06. H1N1','87286',20,'')
        addDir('07. Caught on Tape','87287',20,'')                                                     

#News
def INDEX3(url):
        addDir('01. US','86856',20,'')
        addDir('02. World','86857',20,'')
        addDir('03. Polotics','86858',20,'')
        addDir('04. Health','86859',20,'')
        addDir('05. Faith','86860',20,'')
        addDir('06. SciTech','86861',20,'')
        addDir('07. Law','86862',20,'')
        addDir('08. Caught on Tape','86864',20,'')
        addDir('09. FOX News Blast','86865',20,'')
        addDir('10. FOX News Flash','86866',20,'')
        addDir('11. Weather Flash','86867',20,'')
        addDir('12. Mobile Video','86868',20,'')
        addDir('13. FNCU','86870',20,'')

#Entertainment
def INDEX4(url):
        addDir('01. Latest Video','86871',20,'')
        addDir('02. Exclusive','86872',20,'')
        addDir('03. Movies','86873',20,'')#
        addDir('04. Music','86874',20,'')
        addDir('05. TV','86875',20,'')
        addDir('06. Gossip','86876',20,'')
        addDir('07. Fox411','86877',20,'')
        addDir('08. Hollywood Nation','86878',20,'')#
        addDir('09. Movietone','86881',20,'')

#Business
def INDEX5(url):
        addDir('01. News','86883',20,'')
        addDir('02. FOX Biz Flash','86884',20,'')
        addDir('03. Road to Retirement','86888',20,'')#
        addDir('04. Small Biz Block','86889',20,'')
        addDir('05. Small Biz Now','86890',20,'')

#Health
def INDEX6(url):
        addDir('01. Health News','86892',20,'')
        addDir('02. Q&A with Dr. Manny','86893',20,'')
        addDir('03. Health Talk','86894',20,'')
        addDir('04. Sunday Housecall','86895',20,'')
        addDir('05. Dr. Coomer','86897',20,'')
        addDir("06. Dr. Siegel's Take",'86896',20,'')       
        addDir('07. Health Storm Center','86898',20,'')
        addDir('08. Medicine','86899',20,'')#
        addDir('09. Surgery','86900',20,'')#
        addDir('10. Sexual Health and Reproduction','86901',20,'')
        addDir('11. Beauty & Skin','86902',20,'')#
        addDir('12. Nutrition & Fitness','86903',20,'')#
        addDir('13. Pediatrics','86904',20,'')#
        addDir('14. Vision','86905',20,'')#
        addDir("15. Men's Health",'86906',20,'')
        addDir("16. Women's Health",'86907',20,'')
        addDir('17. Ask Dr Manny Show','86908',20,'')#

#Shows
def INDEX7(url):
        addDir("01. America's Newsroom",'86909',20,'')
        addDir("02. America's New HQ",'86910',20,'')#
        addDir('03. Cost of Freedom','86911',20,'')
        addDir('04. FOX & Friends','86912',20,'')
        addDir('05. FOX News Sunday','86913',20,'')
        addDir('06. FOX News Watch','86914',20,'')
        addDir('07. Fox Report','86915',20,'')
        addDir('08. Geraldo at Large','86916',20,'')
        addDir('09. Glenn Beck','86917',20,'')
        addDir('10. Happening Now','86919',20,'')
        addDir('11. Huckabee','86920',20,'')
        addDir('12. Journal Editorial Report','86921',20,'')
        addDir('13. Live Desk','86922',20,'')
        addDir("14. O'Reilly Factor",'86923',20,'')
        addDir('15. Hannity','86924',20,'')
        addDir('16. On The Record','86925',20,'')
        addDir('17. Red Eye','86926',20,'')
        addDir('18. Special Report','86927',20,'')
        addDir('19. Studio B','86928',20,'')
        addDir('20. Your World','86929',20,'')
        addDir('21. The Daily Shep','86930',20,'')
        addDir('22. Behind the Scenes','86931',20,'')
        
#Opinion
def INDEX8(url):
        addDir('01. Neil Cavuto','86933',20,'')
        addDir("02. Bill O'Reilly",'86934',20,'')
        addDir('03. Sean Hannity','86935',20,'')        
        addDir('04. Grapevine','86936',20,'')
        addDir('05. Glenn Beck','86937',20,'')
        addDir('06. Brian Kilmeade','86938',20,'')        
        addDir('07. Greg Gutfeld','86939',20,'')
        addDir('08. Dennis Miller','86940',20,'')
        addDir('09. Mike Huckabee','86941',20,'')
        addDir('10. Defcon 3 by KT','86942',20,'')
        addDir('11. Napolitano','86943',20,'')#

#Sports
def INDEX9(url):
        addDir('01. Wide Write','86944',20,'')
        addDir("01. Kilmeade's SportsBlog",'86945',20,'')#
        addDir('01. Straka MMa','86946',20,'')

#Leisure
def INDEX10(url):
        addDir('01. FOX Car Report','86965',20,'')
        addDir('02. Around the House','86967',20,'')
        addDir('03. Travel','86968',20,'')
        addDir('04. Food','86969',20,'')

#Howcast
def INDEX11(url):
        addDir('01. Food and Drink','86970',20,'')
        addDir('02. Fun and Games','86971',20,'')
        addDir('03. Health and Beauty','86972',20,'')
        addDir('04. Health and Family','86973',20,'')
        addDir('05. Hot How To','86974',20,'')
        addDir('06. Sex and Dating','86975',20,'')
        addDir('07. Tech and Gadgets','86976',20,'')

#Strategy Room
def INDEX12(url):
        addDir('01. Morning Click','86978',20,'')
        addDir('02. Breaking News','86980',20,'')
        addDir('03. Cops and Cases','86981',20,'')
        addDir('04. Freedom Watch','86982',20,'')
        addDir('05. FOX Entertainment Hour','86983',20,'')
        addDir('06. Alan Colmes','86984',20,'')
        addDir('07. Powers Hour','86985',20,'')
        addDir('08. The Biz Hour','86986',20,'')
        addDir('09. Last Call','86987',20,'')
        addDir('10. Clubhouse Report','86988',20,'')
        addDir('11. News With A View','86989',20,'')
        addDir('12. Gadgets and Games','86990',20,'')               
        addDir('13. Specials','86991',20,'')
        addDir('14. Strategy Room Email','86992',20,'')
        addDir('15. SR Best','86993',20,'')  
        
#FNC iMag
def INDEX13(url):
        addDir('01. Love & Marrige','86947',20,'')#
        addDir('02. The Style Guide','8694',20,'')#
        addDir('03. Food','8694',20,'')
        addDir('04. Fitness','86950',20,'')
        addDir('05. Beauty','86951',20,'')
        addDir('06. Career','86952',20,'')
        addDir('07. At Home','86953',20,'')
        addDir('08. The Guy Guide','86954',20,'')
        addDir('09. Getaway Guide','86955',20,'')
        addDir('10. Travel','86956',20,'')
        addDir('11. Wellness','86957',20,'')              
        addDir('12. Go Green','86958',20,'')       
        addDir('13. Small Business','86961',20,'')

#FOX News Radio
def INDEX14(url):
        addDir('01. Brian & Judge','86995',20,'')
        addDir('02. Spencer Hughes','86996',20,'')
        addDir('03. Tom Sullivan','86997',20,'')
        addDir('04. John Gibson','86998',20,'')
        addDir('05. Alan Colmes','86999',20,'')
        addDir('06. All Radio','87000',20,'')

#FOX Fan
def INDEX15(url):
        addDir('01. Exclusives','87001',20,'')
                                       
def VIDEOLINKS(url,name):
        req = urllib2.Request('http://video.foxnews.com/v/feed/playlist/'+url+'.xml')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        clean=re.sub('&amp;','&',link)
        clean1=re.sub('&apos;',"'",clean)
        clean2=re.sub('&quot;','"',clean1)
        clean3=re.sub('&#39;','',clean2)
        a=re.compile('<title>(.+?)</title>\n.+?<media:content url="(.+?)">\n.+?<media:description>(.+?)</media:description>\n.+?<media:thumbnail>(.+?)</media:thumbnail>\n.+?\n.+?\n.+?\n.+?\n.+?\n.+?<mvn:airDate>(.+?)-(.+?)-(.+?)T.+?Z</mvn:airDate>')
        match=a.findall(clean3)     
        for name,url,desc,thumbnail,Year,Month,Day in match:
                addLink(name,url,thumbnail,Month+'/'+Day+'/'+Year,desc)
        
                
                
                                
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
                                
        return param




def addLink(name,url,iconimage,date,desc):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        description = desc + "\n \n Date aired:     " + date
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Date": date ,"Plot":description} )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
   
        
              
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print ""
        INDEX(url)
elif mode==2:
        print ""+url
        INDEX2(url)
elif mode==3:
        print ""+url
        INDEX3(url)
elif mode==4:
        print ""+url
        INDEX4(url)
elif mode==5:
        print ""+url
        INDEX5(url)
elif mode==6:
        print ""+url
        INDEX6(url)
elif mode==7:
        print ""+url
        INDEX7(url)
elif mode==8:
        print ""+url
        INDEX8(url)
elif mode==9:
        print ""+url
        INDEX9(url)
elif mode==10:
        print ""+url
        INDEX10(url)
elif mode==11:
        print ""+url
        INDEX11(url)                 
elif mode==12:
        print ""+url
        INDEX12(url)                 
elif mode==13:
        print ""+url
        INDEX13(url)                 
elif mode==14:
        print ""+url
        INDEX14(url)                 
elif mode==15:
        print ""+url
        INDEX15(url)                                         
elif mode==20:
        print ""+url
        VIDEOLINKS(url,name)                



xbmcplugin.endOfDirectory(int(sys.argv[1]))
