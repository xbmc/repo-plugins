import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.nascar')


def main():
    url = 'http://i.cdn.turner.com/nascar/feeds/partners/embeded_player/latest.xml'
    req = urllib2.Request(url)
    req.addheaders = [('Referer', 'http://www.nascar.com/videos'),
           ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    match=re.compile('<CATEGORY>.+?</CATEGORY>\n<TITLE>(.+?)</TITLE>\n<DESCRIPTION>.+?</DESCRIPTION>\n<URL ID="(.+?)">\n<SITEURL>.+?</SITEURL>\n</URL>\n<IMAGE>(.+?)</IMAGE>').findall(link)
    for name,url,thumbnail in match:
        url = 'http://ht.cdn.turner.com/nascar/big/'+url+'.nascar_640x360.mp4'
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)

main()

xbmcplugin.endOfDirectory(int(sys.argv[1]))