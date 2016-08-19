import re

def get_video(html_page):
    match = re.search("<div id='premium-video'", html_page)
    match2 = re.search("<source src='", html_page[match.end():len(html_page)])
    match3 = re.search("' type=", html_page[match.end()+match2.end():len(html_page)])
    return html_page[match.end()+match2.end():match3.start()+match.end()+match2.end()]
    
def get_links(html_page):
    videos = []
    for self in re.finditer("""<header class="entry-header">""", html_page):
        e = self.end()+1
        match = re.search("""<a href=""", html_page[e:len(html_page)])        
        match2 = re.search("""" title="Permalink""", html_page[match.end()+e+1:len(html_page)])
        link = html_page[match.end()+e+1: e+1+match.end()+match2.start()]
        #print link
        e = e + 1 + match.end() + match2.start()
        match = re.search(">", html_page[e:len(html_page)])        
        match2 = re.search("</a>", html_page[match.end()+e+1:len(html_page)])
        title = html_page[match.end()+e: e+1+match.end()+match2.start()]
        #print title
        e = e + 1 + match.end() + match2.start()
        match = re.search("<p>", html_page[e:len(html_page)])        
        match2 = re.search("</p>", html_page[match.end()+e+1:len(html_page)])
        des = html_page[match.end()+e: e+1+match.end()+match2.start()]        
        ##print des
        #import HTMLParser
        #des = HTMLParser.HTMLParser().unescape(des.encode('utf-8))     
        videos.append({'name': title, 'description' : des, 'thumb': 'thethumb', 'video': link, 'genre': 'News', 'plot': des, 'mediatype': 'tvshow'})
    return videos
        
def page_info(html_page):
    #<div class="x-pagination">
    #<div title="buyer-name">Carson Busses</div>
    #buyers = tree.xpath('//div[@title="buyer-name"]/text()')
    match = re.search('<div class="x-pagination">', html_page)        
    match2 = re.search('<a href="', html_page[match.end():len(html_page)])
    match3 = re.search('" class=', html_page[match2.end()+match.end():len(html_page)])
    link = html_page[match.end()+match2.end(): match3.start()+match.end()+match2.end()]
    return link

