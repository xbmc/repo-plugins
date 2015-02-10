import urllib,urllib2,re,xbmcplugin,xbmcgui
from elementtree import ElementTree as ET

# Photography podcasts - by Petr Kovar 2011.


def CATEGORIES():
        addDir('Camera Position','http://www.cameraposition.com/',1,'')
        addDir('The Candid Frame','http://www.thecandidframe.com/',2,'')
        addDir('Digital Photo Experience','http://dpexperience.com/',3,'')
        addDir('Martin Bailey Photography','http://www.martinbaileyphotography.com/podcasts.php',4,'')
        addDir('Meet the Gimp','http://blog.meetthegimp.org/',5,'gimp.png','Video tutorials for GIMP and other free graphics programs')
        addDir('Photo Walkthrough','http://www.photowalkthrough.com/',6,'')
        addDir('Thoughts on Photography','http://www.thoughtsonphotography.com/',7,'')
        addDir('Tips From The Top Floor','http://www.tipsfromthetopfloor.com/',8,'')
                       


def get_url(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()

        return link



def get_feeds(url,path):
        page = get_url(url)
        tree = ET.fromstring(page);
        feeds = tree.findall(path);
        return feeds



def strip_html(page):
        html = re.sub('<.*?>','',page)
        html = re.sub('&#[^;]+;', entity_to_s,html)
        html = re.sub('&nbsp;',' ',html)
        html = re.sub('^\s*','',html)
        html = re.sub('\s*$','',html)
        return html



#def meetthegimp(url):
#        link = get_url(url)
#        articles = re.compile('<article[^>]*>(.*?)</article>',re.MULTILINE|re.DOTALL).split(link)
#        for article in articles:
#                res=re.compile('>(Episode \d+:[^<]*)</a></h1>').search(article)
#                if not res:
#                        continue
#                name=res.group(1)
#                meetId=re.compile('Episode (\d+):').search(name).group(1)
#                url='http://dl.meetthegimp.org/meetthegimp'+meetId+'.mp4'
#                img=''
#                res=re.compile('(<img.*?class="alignright[^"]*".*?>)').search(article)
#                if res:
#                        img = re.compile('src="([^"]+)"').search(res.group(1)).group(1)
#                description=''
#                res=re.compile('Download.*?</p>(.*)<footer',re.MULTILINE|re.DOTALL).search(article)
#                if res:
#                        description = strip_html(res.group(1))
#
#                date=re.compile('<time(.*?)</time>',re.MULTILINE|re.DOTALL).search(article).group(1)
#                res=re.compile('Download the Video! \((\d+:\d+)\s+(.*?)MB\)').search(article)
#                duration=''
#                size=''
#                if res:
#                        duration = res.group(1)
#                        size = res.group(2)
#                addLink('Video', name,url,img,description,date,duration,size)
#


def feeds(url, type='Video'):
        fs = get_feeds(url, 'channel/item')
        for feed in fs:
                name = feed.find('title').text
                enclosure = feed.find('enclosure')
                if enclosure == None:
                        continue
                url = enclosure.get('url')
                img = ''
                description = strip_html(feed.find('description').text)
                date = feed.find('pubDate').text
                duration = ''
                size = enclosure.get('length')
                if (size == None) or (not re.compile('^\d+$').match(size)):
                        size = 0
                addLink(type, name, url, img, description, date, duration, size)



def entity_to_s(e):
#       return ""+unichr(int(e[3:-1],16))
        return ""

                

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




def addLink(type,name,url,iconimage,description,date,duration,size):
        ok=True
        if iconimage=='':
                iconimage = "DefaultVideo.png"
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type=type, infoLabels={ "Title": name, "Plot": description, "Date": date, "Genre": "Podcast", "Duration": duration, "Size": float(size) } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok



def addDir(name,url,mode,iconimage,description=''):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        if iconimage=='':
                iconimage = "DefaultVideo.png"
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
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
        CATEGORIES()
elif mode==1:
        feeds("http://feeds.feedburner.com/cameraposition?format=xml")
elif mode==2:
        feeds("http://feeds.feedburner.com/TheCandidFrame?format=xml")
elif mode==3:
        feeds("http://feeds.feedburner.com/dpexperience?format=xml")
elif mode==4:
        feeds("http://feeds.feedburner.com/MartinBaileyPhotographyPodcast?format=xml")
elif mode==5:
        feeds("http://feeds.feedburner.com/meetthegimp")
elif mode==6:
        feeds("http://www.photowalkthrough.com/photowalkthrough/rss.xml")
elif mode==7:
        feeds("http://thoughtsonphotography.com/rss")
elif mode==8:
        feeds("http://feeds.tipsfromthetopfloor.com/tftf?format=xml")

xbmcplugin.endOfDirectory(int(sys.argv[1]))
