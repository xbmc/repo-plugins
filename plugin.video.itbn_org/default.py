import urllib,urllib2,re,xbmcplugin,xbmcgui,os,xbmcaddon,sys

settings = xbmcaddon.Addon( id = 'plugin.video.itbn_org' )
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'nextpage.png' )
previous_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'previouspage.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )
main_menu_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'main_menu.png' )
live_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'live.png' )
movies_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'movies.png' )

def MAIN():
        addDir('Recent','http://www.tbn.org/watch/mobile_app/v3/itbnapi.php?platform=android&request_path=%2Fapi%2Fv1.0%2Fvideos%2Flimit%2F250%2Fsortby%2Fairdate&device_name=GT-I9100&os_ver=2.3.4&screen_width=1600&screen_height=900&app_ver=3.0&UUID=1d5f5000-656a-4a16-847f-138937d4d0c4',6,'')
        addDir('Categories','http://www.itbn.org',3,'')
        addDir('Programs','http://www.itbn.org/programs',5,'')
        addDir('Movies','http://www.tbn.org/watch/mobile_app/v3/itbnapi.php?platform=android&request_path=%2Fapi%2Fv1.0%2Fvideos%2Flimit%2F250%2Fsortby%2Fairdate%2Fcategory%2F1723&device_name=GT-I9100&os_ver=2.3.4&screen_width=1600&screen_height=900&app_ver=3.0&UUID=1d5f5000-656a-4a16-847f-138937d4d0c4',10,movies_thumb)
        addDir('Live','http://www.tbn.org/watch/mobile_app/v3/getlivestreams.php?device_name=GT-I9100&os_ver=2.3.4&screen_width=1600&screen_height=900&app_ver=3.0&UUID=1d5f5000-656a-4a16-847f-138937d4d0c4',7,live_thumb)
        addDir('Search','http://itbn.org/',8,search_thumb)
	addDir('Air Date','http://itbn.org/',9,search_thumb)
	if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(50)')
def ADDLINKS(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('						<a href=".+?/ec/(.+?)"><img src=".+?" alt=".+?" title=".+?"').findall(link)
        title=re.compile('						<a href=".+?"><img src=".+?" alt=".+?" title="(.+?)"').findall(link)
        function=' '*len(match)
        leftparentheses='('*len(match)
        date=re.compile('<span class="air_date">(.+?)</span>').findall(link)
        description=re.compile('						<span class="description">(.+?)</span>').findall(link)
        rightparentheses=')'*len(match)
        name=zip((title),(function),(function),(leftparentheses),(date),(rightparentheses))
        thumbnail=re.compile('						<a href=".+?"><img src="(.+?)" alt=".+?" title=".+?"').findall(link)
        thumbnail = [w.replace('\\', '') for w in thumbnail]
        prefixcode='http://www.tbn.org/watch/mobile_app/v3/ooyala_strip_formats.php?method=GET&key=undefined&secret=undefined&expires=600&embedcode=',len(match)
        prefix=[prefixcode[0]]*prefixcode[1]
        suffixcode='&requestbody=&parameters=',len(match)
        suffix=[suffixcode[0]]*suffixcode[1]
        nextpage=re.compile('<div class=\'btn_container\'><a href=\'(.+?)\' class=\'btn_next\'>').findall(link)
	nextpagelabelurl=re.compile('<div class=\'btn_container\'><a href=\'.+?/page/(.+?.+?.+?)').findall(link)
        airdatepage=re.compile('.+?airDate=(.+?.+?.+?.+?.+?.+?.+?.+?.+?.+?)').findall(url)
        if nextpage:
                nextpagelabel=nextpagelabelurl[0]
                nextpagelabel=nextpagelabel.replace('%27','')
                if airdatepage:
                        nextpagelabel=nextpagelabel.replace(airdatepage[0],'')
                nextpagelabel=[w.replace('/', '') for w in nextpagelabel]
                nextpagelabel=" ".join(nextpagelabel)
                nextpagelabel=[int(s) for s in nextpagelabel.split() if s.isdigit()]
                nextpagelabel=''.join(str(e) for e in nextpagelabel)
        previouspage=re.compile('class=\'btn_first\'>&lt;&lt;</a></li><li><a href=\'(.+?)\' class=\'btn_prev\'>').findall(link)
	previouspagelabelurl=re.compile('class=\'btn_first\'>&lt;&lt;</a></li><li><a href=\'.+?/page/(.+?.+?.+?)').findall(link)
        if previouspage:
                previouspagelabel=previouspagelabelurl[0]
                previouspagelabel=previouspagelabel.replace('%27','')
                if airdatepage:
                        previouspagelabel=previouspagelabel.replace(airdatepage[0],'')
                previouspagelabel=[w.replace('/', '') for w in previouspagelabel]
                previouspagelabel=" ".join(previouspagelabel)
                previouspagelabel=[int(s) for s in previouspagelabel.split() if s.isdigit()]
                previouspagelabel=''.join(str(e) for e in previouspagelabel)
        source=zip((prefix),(match),(suffix))
        mylist=zip((source),(name),(thumbnail),(description))
        addDir('Main Menu','',None,main_menu_thumb)
        if previouspage:
                addDir('Page '+previouspagelabel,'http://www.itbn.org'+previouspage[0],1,previous_thumb)
        for url,name,thumbnail,description in mylist:
                description=description.replace("&quot;","\"")
                description=description.replace("&#039;","\'")
                description=description.replace("&hellip;","...")
                description=description.replace("&amp;","&")
                name=reduce(lambda rst, d: rst * 1 + d, (name))
                name=name.replace("&quot;","\"")
                name=name.replace("&#039;","\'")
                name=name.replace("&hellip;","...")
                name=name.replace("&amp;","&")
                url=reduce(lambda rst, d: rst * 1 + d, (url))
                addDir(name+' - '+description,url,2,thumbnail)
        if nextpage:
                addDir('Page '+nextpagelabel,'http://www.itbn.org'+nextpage[0],1,next_thumb)
        video_view = settings.getSetting("list_view") == "1"
        if 1==1:
            xbmc.executebuiltin("Container.SetViewMode(500)")
        
def GETSOURCE(url,name):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('"is_source":true,"file_size":.+?,"audio_codec":".+?","video_codec":".+?","average_video_bitrate":.+?,"stream_type":"single","url":"(.+?)"').findall(link)
        match = [w.replace('\\', '') for w in match]
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage='')
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        for url in match:
                xbmc.Player().play(url,liz)
		xbmc.sleep(2500)
		while xbmc.Player().isPlaying():
    			xbmc.sleep(250)
		xbmc.Player().stop()
	sys.exit()        

def CATEGORIES(url):
        addDir('Faith Issues','http://www.tbn.org/watch/mobile_app/v3/itbnapi.php',4,'')
        addDir('Classics','http://www.itbn.org/index/subview/lib/Programs/sublib/Classics',1,'')
        addDir('Educational','http://www.itbn.org/index/subview/lib/Programs/sublib/Educational',1,'')
        addDir('Health & Fitness','http://www.itbn.org/index/subview/lib/Programs/sublib/Health+%26+Fitness',1,'')
        addDir('Kids','http://www.itbn.org/index/subview/lib/Programs/sublib/Kids',1,'')
        addDir('Music','http://www.itbn.org/index/subview/lib/Programs/sublib/Music',1,'')
        addDir('Specials','http://www.itbn.org/index/subview/lib/Programs/sublib/Specials',1,'')
        addDir('Teens','http://www.itbn.org/index/subview/lib/Programs/sublib/Teens',1,'')
        addDir('Documentaries','http://www.itbn.org/index/subview/lib/Programs/sublib/Documentaries',1,'')
        addDir('Family & Variety','http://www.itbn.org/index/subview/lib/Programs/sublib/Family+%26+Variety',1,'')
        addDir('Holidays','http://www.itbn.org/index/subview/lib/Programs/sublib/Holidays',1,'')
        addDir('Reality','http://www.itbn.org/index/subview/lib/Programs/sublib/Holidays',1,'')
        if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(50)')

def FAITHISSUES(url):
        addDir('Angels','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Angels',1,'')
        addDir('Crisis','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Crisis',1,'')
        addDir('Depression','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Depression',1,'')
        addDir('End Times','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/End+Times',1,'')
        addDir('Faith','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Faith',1,'')
        addDir('Family','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Family',1,'')
        addDir('Finances','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Finances',1,'')
        addDir('Heaven','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Heaven',1,'')
        addDir('Hell','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Hell',1,'')
        addDir('Loss','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Loss',1,'')
        addDir('Marriage','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Marriage',1,'')
        addDir('Prayer','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Prayer',1,'')
        addDir('Purpose','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Purpose',1,'')
        addDir('Salvation','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Salvation',1,'')
        addDir('Satan','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Satan',1,'')
        addDir('Sexuality','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Sexuality',1,'')
        addDir('Suicide','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Suicide',1,'')
        addDir('Teen Issues','http://www.itbn.org/index/subview/lib/Faith+Issues/sublib/Teen+Issues',1,'')
        if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(50)')
def PROGRAMS(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('									<a href="(.+?)">(.+?)</a>').findall(link)
        for url,name in match:
                if url != '#\" class=\"btn_top':
                        name = name.replace("&hellip;","...")
                        name = name.replace("&#039;","\'")
                        name = name.replace("&amp;","&")
                        addDir(name,'http://www.itbn.org'+url,1,'')
        if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(50)')

def RECENT(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('"embedCode":"(.+?)"').findall(link)
        title=re.compile('"displayTitle":"(.+?)"').findall(link)
        function=' '*len(match)
        leftparentheses='('*len(match)
        date=re.compile('"airDate":"(.+?) 00:00:00"').findall(link)
        description=re.compile('\"description\":\"(.+?)\","air').findall(link)
        rightparentheses=')'*len(match)
        name=zip((title),(function),(function),(leftparentheses),(date),(rightparentheses))
        thumbnail=re.compile('"thumbnailUrl":"(.+?)"').findall(link)
        thumbnail = [w.replace('\\', '') for w in thumbnail]
        prefixcode='http://www.tbn.org/watch/mobile_app/v3/ooyala_strip_formats.php?method=GET&key=undefined&secret=undefined&expires=600&embedcode=',len(match)
        prefix=[prefixcode[0]]*prefixcode[1]
        suffixcode='&requestbody=&parameters=',len(match)
        suffix=[suffixcode[0]]*suffixcode[1]
        source=zip((prefix),(match),(suffix))
        mylist=zip((source),(name),(thumbnail),(description))
        for url,name,thumbnail,description in mylist:
                description=description.replace("\\","")
                description=description.replace("u2019","\'")
                addDir(reduce(lambda rst, d: rst * 1 + d, (name)),reduce(lambda rst, d: rst * 1 + d, (url)),2,thumbnail)
        if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(50)')
                
def LIVE(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
	match='rtmp://cp114430.live.edgefcs.net/live/ playpath=tbn_mbr_600@101613 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp114428.live.edgefcs.net/live/ playpath=churchch_mbr_600@101620 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp114432.live.edgefcs.net/live/ playpath=jctv_mbr_600@101615 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp114426.live.edgefcs.net/live/ playpath=soac_mbr_600@101622 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp114434.live.edgefcs.net/live/ playpath=enlace_mbr_600@101618 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp114436.live.edgefcs.net/live/ playpath=enlacejuvenil_800@102106 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp129063.live.edgefcs.net/live/ playpath=nejat_mbr_600@101623 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp129064.live.edgefcs.net/live/ playpath=healing_mbr_600@101624 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp129065.live.edgefcs.net/live/ playpath=tbnrussia-high@58776 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://cp129066.live.edgefcs.net/live/ playpath=soacrussia-high@58777 pageURL=http://www.tbn.org/watch-us swfUrl=http://players.edgesuite.net/flash/plugins/osmf/advanced-streaming-plugin/v2.11/osmf2.0/AkamaiAdvancedStreamingPlugin.swf swfVfy=true live=true','rtmp://mediaplatform2.trinetsolutions.com/tbn/ playpath=juce_super.sdp  live=true','rtmp://mediaplatform2.trinetsolutions.com/tbn_repeater/ playpath=tbnafrica.stream live=true'
        title=re.compile('\"name\":\"(.+?)\"').findall(link)
        thumbnail=re.compile('\"icon\":\"(.+?)\"').findall(link)
        mylist=zip((match),(title),(thumbnail))
        for url,name,thumbnail in mylist:
                addLink(name,url,thumbnail)
        if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(500)')

def SEARCH(url):
        keyboard = xbmc.Keyboard('', '')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
                search_string = keyboard.getText().replace(" ","+")
                content = 'http://www.itbn.org/search?search='+search_string+'&submit_search=search'
                req = urllib2.Request(content)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                response = urllib2.urlopen(req)
                link=response.read()
                response.close()
                match=re.compile('						<a href=".+?/ec/(.+?)"><img src=".+?" alt=".+?" title=".+?"').findall(link)
                title=re.compile('						<a href=".+?"><img src=".+?" alt=".+?" title="(.+?)"').findall(link)
                function=' '*len(match)
                leftparentheses='('*len(match)
                date=re.compile('<span class="air_date">(.+?)</span>').findall(link)
                description=re.compile('						<span class="description">(.+?)</span>').findall(link)
                rightparentheses=')'*len(match)
                name=zip((title),(function),(function),(leftparentheses),(date),(rightparentheses))
                thumbnail=re.compile('						<a href=".+?"><img src="(.+?)" alt=".+?" title=".+?"').findall(link)
                thumbnail = [w.replace('\\', '') for w in thumbnail]
                prefixcode='http://www.tbn.org/watch/mobile_app/v3/ooyala_strip_formats.php?method=GET&key=undefined&secret=undefined&expires=600&embedcode=',len(match)
                prefix=[prefixcode[0]]*prefixcode[1]
                suffixcode='&requestbody=&parameters=',len(match)
                suffix=[suffixcode[0]]*suffixcode[1]
                nextpage=re.compile('<div class=\'btn_container\'><a href=\'(.+?)\' class=\'btn_next\'>').findall(link)
		nextpagelabelurl=re.compile('<div class=\'btn_container\'><a href=\'.+?/page/(.+?.+?.+?)').findall(link)
                if nextpage:
                        nextpagelabel=nextpagelabelurl[0]
                        nextpagelabel=nextpagelabel.replace('%27','')
                        nextpagelabel=[w.replace('/', '') for w in nextpagelabel]
                        nextpagelabel=" ".join(nextpagelabel)
                        nextpagelabel=[int(s) for s in nextpagelabel.split() if s.isdigit()]
                        nextpagelabel=''.join(str(e) for e in nextpagelabel)
                previouspage=re.compile('class=\'btn_first\'>&lt;&lt;</a></li><li><a href=\'(.+?)\' class=\'btn_prev\'>').findall(link)
		previouspagelabelurl=re.compile('class=\'btn_first\'>&lt;&lt;</a></li><li><a href=\'.+?/page/(.+?)\' class=\'btn_prev\'>').findall(link)
                if previouspage:
                        previouspagelabel=previouspagelabelurl[0]
                        previouspagelabel=previouspagelabel.replace('%27','')
                        previouspagelabel=[w.replace('/', '') for w in previouspagelabel]
                        previouspagelabel=" ".join(previouspagelabel)
                        previouspagelabel=[int(s) for s in previouspagelabel.split() if s.isdigit()]
                        previouspagelabel=''.join(str(e) for e in previouspagelabel)
                source=zip((prefix),(match),(suffix))
                mylist=zip((source),(name),(thumbnail),(description))
                addDir('Main Menu','',None,main_menu_thumb)
                if previouspage:
                        addDir('Page '+previouspagelabel,'http://www.itbn.org'+previouspage[0],1,next_thumb)
                for url,name,thumbnail,description in mylist:
                        description=description.replace("&quot;","\"")
                        description=description.replace("&#039;","\'")
                        description=description.replace("&hellip;","...")
                        description=description.replace("&amp;","&")
                        name=reduce(lambda rst, d: rst * 1 + d, (name))
                        name=name.replace("&quot;","\"")
                        name=name.replace("&#039;","\'")
                        name=name.replace("&hellip;","...")
                        name=name.replace("&amp;","&")
                        url=reduce(lambda rst, d: rst * 1 + d, (url))
                        addDir(name+' - '+description,url,2,thumbnail)
                if nextpage:
                        addDir('Page '+nextpagelabel,'http://www.itbn.org'+nextpage[0],1,next_thumb)
                if 1==1:
                        xbmc.executebuiltin('Container.SetViewMode(500)')
        else:
                MAIN()

def AIRDATE(url):
        keyboard = xbmc.Keyboard('yyyy-mm-dd', '')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
                search_string = keyboard.getText().replace(" ","+")
                content = 'http://www.itbn.org/search?airDate='+search_string
                req = urllib2.Request(content)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
                response = urllib2.urlopen(req)
                link=response.read()
                response.close()
                match=re.compile('						<a href=".+?/ec/(.+?)"><img src=".+?" alt=".+?" title=".+?"').findall(link)
                title=re.compile('						<a href=".+?"><img src=".+?" alt=".+?" title="(.+?)"').findall(link)
                function=' '*len(match)
                leftparentheses='('*len(match)
                date=re.compile('<span class="air_date">(.+?)</span>').findall(link)
                description=re.compile('						<span class="description">(.+?)</span>').findall(link)
                rightparentheses=')'*len(match)
                name=zip((title),(function),(function),(leftparentheses),(date),(rightparentheses))
                thumbnail=re.compile('						<a href=".+?"><img src="(.+?)" alt=".+?" title=".+?"').findall(link)
                thumbnail = [w.replace('\\', '') for w in thumbnail]
                prefixcode='http://www.tbn.org/watch/mobile_app/v3/ooyala_strip_formats.php?method=GET&key=undefined&secret=undefined&expires=600&embedcode=',len(match)
                prefix=[prefixcode[0]]*prefixcode[1]
                suffixcode='&requestbody=&parameters=',len(match)
                suffix=[suffixcode[0]]*suffixcode[1]
                nextpage=re.compile('<div class=\'btn_container\'><a href=\'(.+?)\' class=\'btn_next\'>').findall(link)
                airdatepage=re.compile('.+?airDate=(.+?.+?.+?.+?.+?.+?.+?.+?.+?.+?)').findall(content)
                if nextpage:
                        nextpagelabel=nextpage[0]
                        nextpagelabel=nextpagelabel.replace('%27','')
                        nextpagelabel=nextpagelabel.replace(airdatepage[0],'')
                        nextpagelabel=[w.replace('/', '') for w in nextpagelabel]
                        nextpagelabel=" ".join(nextpagelabel)
                        nextpagelabel=[int(s) for s in nextpagelabel.split() if s.isdigit()]
                        nextpagelabel=''.join(str(e) for e in nextpagelabel)
                previouspage=re.compile('class=\'btn_first\'>&lt;&lt;</a></li><li><a href=\'(.+?)\' class=\'btn_prev\'>').findall(link)
                if previouspage:
                        previouspagelabel=previouspage[0]
                        previouspagelabel=previouspagelabel.replace('%27','')
                        previouspagelabel=previouspagelabel.replace(airdatepage[0],'')
                        previouspagelabel=[w.replace('/', '') for w in previouspagelabel]
                        previouspagelabel=" ".join(previouspagelabel)
                        previouspagelabel=[int(s) for s in previouspagelabel.split() if s.isdigit()]
                        previouspagelabel=''.join(str(e) for e in previouspagelabel)
                source=zip((prefix),(match),(suffix))
                mylist=zip((source),(name),(thumbnail),(description))
                xbmc.executebuiltin('Container.SetViewMode(500)')
                addDir('Main Menu','',None,main_menu_thumb)
                if previouspage:
                        addDir('Page '+previouspagelabel,'http://www.itbn.org'+previouspage[0],1,next_thumb)
                for url,name,thumbnail,description in mylist:
                        description=description.replace("&quot;","\"")
                        description=description.replace("&#039;","\'")
                        description=description.replace("&hellip;","...")
                        description=description.replace("&amp;","&")
                        name=reduce(lambda rst, d: rst * 1 + d, (name))
                        name=name.replace("&quot;","\"")
                        name=name.replace("&#039;","\'")
                        name=name.replace("&hellip;","...")
                        name=name.replace("&amp;","&")
                        url=reduce(lambda rst, d: rst * 1 + d, (url))
                        addDir(name+' - '+description,url,2,thumbnail)
                if nextpage:
                        addDir('Page '+nextpagelabel,'http://www.itbn.org'+nextpage[0],1,next_thumb)
                if 1==1:
                        xbmc.executebuiltin('Container.SetViewMode(500)')
        else:
                MAIN()

def MOVIES(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('"embedCode":"(.+?)"').findall(link)
        title=re.compile('"displayTitle":"(.+?)"').findall(link)
        function=' '*len(match)
        leftparentheses='('*len(match)
        date=re.compile('"airDate":"(.+?) 00:00:00"').findall(link)
        description=re.compile('\"description\":\"(.+?)\","air').findall(link)
        rightparentheses=')'*len(match)
        name=zip((title),(function),(function),(leftparentheses),(date),(rightparentheses))
        thumbnail=re.compile('"thumbnailUrl":"(.+?)"').findall(link)
        thumbnail = [w.replace('\\', '') for w in thumbnail]
        prefixcode='http://www.tbn.org/watch/mobile_app/v3/ooyala_strip_formats.php?method=GET&key=undefined&secret=undefined&expires=600&embedcode=',len(match)
        prefix=[prefixcode[0]]*prefixcode[1]
        suffixcode='&requestbody=&parameters=',len(match)
        suffix=[suffixcode[0]]*suffixcode[1]
        source=zip((prefix),(match),(suffix))
        mylist=zip((source),(name),(thumbnail),(description))
        for url,name,thumbnail,description in mylist:
                description=description.replace("\\","")
                description=description.replace("u2019","\'")
                addDir(reduce(lambda rst, d: rst * 1 + d, (name))+' - '+description,reduce(lambda rst, d: rst * 1 + d, (url)),2,thumbnail)
        if 1==1:
                xbmc.executebuiltin('Container.SetViewMode(500)')
               
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

def addLink(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
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
        MAIN()
       
elif mode==1:
        print ""+url
        ADDLINKS(url)
        
elif mode==2:
        print ""+url
        GETSOURCE(url,name)

elif mode==3:
        print ""+url
        CATEGORIES(url)

elif mode==4:
        print ""+url
        FAITHISSUES(url)

elif mode==5:
        print ""+url
        PROGRAMS(url)

elif mode==6:
        print ""+url
        RECENT(url)

elif mode==7:
        print ""+url
        LIVE(url)

elif mode==8:
        print ""+url
        SEARCH(url)

elif mode==9:
        print ""+url
        AIRDATE(url)

elif mode==10:
        print ""+url
        MOVIES(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
