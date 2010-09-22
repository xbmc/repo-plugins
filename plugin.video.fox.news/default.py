import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

#Fox News Video- by Redeyed

__settings__ = xbmcaddon.Addon(id='plugin.video.fox.news')
__language__ = __settings__.getLocalizedString

                       
def INDEX(url):
        addDir(__language__(30001),'87249',20,'')
        addDir(__language__(30002),'http://video.foxnews.com/',2,'')
        addDir(__language__(30003),'http://video.foxnews.com/',3,'')
        addDir(__language__(30004),'http://video.foxnews.com/',4,'')
        addDir(__language__(30005),'http://video.foxnews.com/',5,'')
        addDir(__language__(30006),'http://video.foxnews.com/',6,'')
        addDir(__language__(30007),'http://video.foxnews.com/',7,'')
        addDir(__language__(30008),'http://video.foxnews.com/',8,'')
        addDir(__language__(30009),'http://video.foxnews.com/',9,'')
        addDir(__language__(30010),'http://video.foxnews.com/',10,'')
        addDir(__language__(30011),'http://video.foxnews.com/',11,'')
        addDir(__language__(30012),'http://video.foxnews.com/',12,'')
        addDir(__language__(30013),'86994',20,'')
        addDir(__language__(30014),'http://video.foxnews.com/',13,'')
        addDir(__language__(30015),'http://video.foxnews.com/',14,'')
        addDir(__language__(30016),'http://video.foxnews.com/',15,'')
                       
#Hot Topics                                                     
def INDEX2(url):
        addDir(__language__(30017),'87281',20,'') 
        addDir(__language__(30018),'87282',20,'')
        addDir(__language__(30019),'87283',20,'')
        addDir(__language__(30020),'87284',20,'')
        addDir(__language__(30021),'87285',20,'')
        addDir(__language__(30022),'87286',20,'')
        addDir(__language__(30023),'87287',20,'')                                                     

#News
def INDEX3(url):
        addDir(__language__(30024),'86856',20,'')
        addDir(__language__(30025),'86857',20,'')
        addDir(__language__(30026),'86858',20,'')
        addDir(__language__(30027),'86859',20,'')
        addDir(__language__(30028),'86860',20,'')
        addDir(__language__(30029),'86861',20,'')
        addDir(__language__(30030),'86862',20,'')
        addDir(__language__(30031),'86864',20,'')
        addDir(__language__(30032),'86865',20,'')
        addDir(__language__(30033),'86866',20,'')
        addDir(__language__(30034),'86867',20,'')
        addDir(__language__(30035),'86868',20,'')
        addDir(__language__(30036),'86870',20,'')

#Entertainment
def INDEX4(url):
        addDir(__language__(30037),'86871',20,'')
        addDir(__language__(30038),'86872',20,'')
        addDir(__language__(30039),'86873',20,'')#
        addDir(__language__(30040),'86874',20,'')
        addDir(__language__(30041),'86875',20,'')
        addDir(__language__(30042),'86876',20,'')
        addDir(__language__(30043),'86877',20,'')
        addDir(__language__(30044),'86878',20,'')#
        addDir(__language__(30045),'86881',20,'')

#Business
def INDEX5(url):
        addDir(__language__(30046),'86883',20,'')
        addDir(__language__(30047),'86884',20,'')
        addDir(__language__(30048),'86888',20,'')#
        addDir(__language__(30049),'86889',20,'')
        addDir(__language__(30050),'86890',20,'')

#Health
def INDEX6(url):
        addDir(__language__(30051),'86892',20,'')
        addDir(__language__(30052),'86893',20,'')
        addDir(__language__(30053),'86894',20,'')
        addDir(__language__(30054),'86895',20,'')
        addDir(__language__(30055),'86897',20,'')
        addDir(__language__(30056),'86896',20,'')       
        addDir(__language__(30057),'86898',20,'')
        addDir(__language__(30058),'86899',20,'')#
        addDir(__language__(30059),'86900',20,'')#
        addDir(__language__(30060),'86901',20,'')
        addDir(__language__(30061),'86902',20,'')#
        addDir(__language__(30062),'86903',20,'')#
        addDir(__language__(30063),'86904',20,'')#
        addDir(__language__(30064),'86905',20,'')#
        addDir(__language__(30065),'86906',20,'')
        addDir(__language__(30066),'86907',20,'')
        addDir(__language__(30067),'86908',20,'')#

#Shows
def INDEX7(url):
        addDir(__language__(30068),'86909',20,'')
        addDir(__language__(30069),'86910',20,'')#
        addDir(__language__(30070),'86911',20,'')
        addDir(__language__(30071),'86912',20,'')
        addDir(__language__(30072),'86913',20,'')
        addDir(__language__(30073),'86914',20,'')
        addDir(__language__(30074),'86915',20,'')
        addDir(__language__(30075),'86916',20,'')
        addDir(__language__(30076),'86917',20,'')
        addDir(__language__(30077),'86919',20,'')
        addDir(__language__(30078),'86920',20,'')
        addDir(__language__(30079),'86921',20,'')
        addDir(__language__(30080),'86922',20,'')
        addDir(__language__(30081),'86923',20,'')
        addDir(__language__(30082),'86924',20,'')
        addDir(__language__(30083),'86925',20,'')
        addDir(__language__(30084),'86926',20,'')
        addDir(__language__(30085),'86927',20,'')
        addDir(__language__(30086),'86928',20,'')
        addDir(__language__(30087),'86929',20,'')
        addDir(__language__(30088),'86930',20,'')
        addDir(__language__(30089),'86931',20,'')
        
#Opinion
def INDEX8(url):
        addDir(__language__(30090),'86933',20,'')
        addDir(__language__(30091),'86934',20,'')
        addDir(__language__(30092),'86935',20,'')        
        addDir(__language__(30093),'86936',20,'')
        addDir(__language__(30094),'86937',20,'')
        addDir(__language__(30095),'86938',20,'')        
        addDir(__language__(30096),'86939',20,'')
        addDir(__language__(30097),'86940',20,'')
        addDir(__language__(30098),'86941',20,'')
        addDir(__language__(30099),'86942',20,'')
        addDir(__language__(30100),'86943',20,'')#

#Sports
def INDEX9(url):
        addDir(__language__(30101),'86944',20,'')
        addDir(__language__(30102),'86945',20,'')#
        addDir(__language__(30103),'86946',20,'')

#Leisure
def INDEX10(url):
        addDir(__language__(30104),'86965',20,'')
        addDir(__language__(30105),'86967',20,'')
        addDir(__language__(30106),'86968',20,'')
        addDir(__language__(30107),'86969',20,'')

#Howcast
def INDEX11(url):
        addDir(__language__(30108),'86970',20,'')
        addDir(__language__(30109),'86971',20,'')
        addDir(__language__(30110),'86972',20,'')
        addDir(__language__(30111),'86973',20,'')
        addDir(__language__(30112),'86974',20,'')
        addDir(__language__(30113),'86975',20,'')
        addDir(__language__(30114),'86976',20,'')

#Strategy Room
def INDEX12(url):
        addDir(__language__(30115),'86978',20,'')
        addDir(__language__(30116),'86980',20,'')
        addDir(__language__(30117),'86981',20,'')
        addDir(__language__(30118),'86982',20,'')
        addDir(__language__(30119),'86983',20,'')
        addDir(__language__(30120),'86984',20,'')
        addDir(__language__(30121),'86985',20,'')
        addDir(__language__(30122),'86986',20,'')
        addDir(__language__(30123),'86987',20,'')
        addDir(__language__(30124),'86988',20,'')
        addDir(__language__(30125),'86989',20,'')
        addDir(__language__(30126),'86990',20,'')               
        addDir(__language__(30127),'86991',20,'')
        addDir(__language__(30128),'86992',20,'')
        addDir(__language__(30129),'86993',20,'')  
        
#FNC iMag
def INDEX13(url):
        addDir(__language__(30130),'86947',20,'')#
        addDir(__language__(30131),'8694',20,'')#
        addDir(__language__(30132),'8694',20,'')
        addDir(__language__(30133),'86950',20,'')
        addDir(__language__(30134),'86951',20,'')
        addDir(__language__(30135),'86952',20,'')
        addDir(__language__(30136),'86953',20,'')
        addDir(__language__(30137),'86954',20,'')
        addDir(__language__(30138),'86955',20,'')
        addDir(__language__(30139),'86956',20,'')
        addDir(__language__(30140),'86957',20,'')              
        addDir(__language__(30141),'86958',20,'')       
        addDir(__language__(30142),'86961',20,'')

#FOX News Radio
def INDEX14(url):
        addDir(__language__(30143),'86995',20,'')
        addDir(__language__(30144),'86996',20,'')
        addDir(__language__(30145),'86997',20,'')
        addDir(__language__(30146),'86998',20,'')
        addDir(__language__(30147),'86999',20,'')
        addDir(__language__(30148),'87000',20,'')

#FOX Fan
def INDEX15(url):
        addDir(__language__(30149),'87001',20,'')
                                       
def VIDEOLINKS(url,name):
        req = urllib2.Request('http://video.foxnews.com/v/feed/playlist/'+url+'.xml')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        a=re.compile('<title>(.+?)</title>\n          <media:content url="(.+?)">\n            <media:player url=".+?" />\n            <media:description>(.+?)</media:description>\n            <media:thumbnail><!\[\CDATA\[(.+?)]\]\></media:thumbnail>\n            <media:keywords>.+?</media:keywords>\n            <media:credit role=".+?" scheme=".+?">.+?</media:credit>\n            <mvn:assetUUID>.+?</mvn:assetUUID>\n            <mvn:mavenId></mvn:mavenId>\n            <mvn:creationDate>.+?</mvn:creationDate>\n            <mvn:airDate>(.+?)-(.+?)-(.+?)T.+?</mvn:airDate>\n')
        match=a.findall(link)     
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
