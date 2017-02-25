import re, xbmcgui

def popup(text):
  xbmcgui.Dialog().ok('plugin.video.tyt', text)

def get_video(html_page):
  match = re.compile("<div id='premium-video'.+?src='(.+?)' type", re.DOTALL).findall(html_page)
  if not match:
    match = re.compile('<div id="premium-video".+?src="(.+?)" type', re.DOTALL).findall(html_page)
  if not match:
    match = re.compile('<script src="(.+?)"></script', re.DOTALL).findall(html_page)      
  for link in match: return link 
    
def get_jw(html_page):
  match = re.compile('406p.+?"file": "(.+?)",\n          "height": 720', re.DOTALL).findall(html_page)  
  for link in match: return "http:" + link

def get_links(html_page):
  videos = []
  info = re.compile('<header class="entry-header.+?href="(.+?)".+?title="Permalink to: "(.+?)".+?datetime="(.+?)T.+?<p>(.+?)<',re.DOTALL).findall(html_page)
  for link,title,date,des in info:
    
    videos.append({'name': title, 'description' : des, 'thumb': 'thethumb', 'aired':date, 'video': link, 'genre': 'News', 'plot': des, 'mediatype': 'tvshow'})
  return videos

def get_live(html_page):
  match = re.compile('class="x-video embed.+?embed/(.+?)" frameborder=',re.DOTALL).findall(html_page)
  for link in match:
    return link
        
def get_members_live(html_page):
  match = re.compile('entry-content content.+?x-video-inner"><iframe width.+?youtube.com/embed/(.+?)"',re.DOTALL).findall(html_page)
  for link in match:
    return link

def page_info(html_page):
  match = re.compile('<div class="x-pagination.+?Last Page".+?href="(.+?)" class=',re.DOTALL).findall(html_page)
  for link in match: 
    link = link.split("https://tytnetwork.com",1)[1]
    return link
