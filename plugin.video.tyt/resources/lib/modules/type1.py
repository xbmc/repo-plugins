import re
def get_video(html_page):
  try:
    match = re.compile("<div id='premium-video'.+?src='(.+?)' type", re.DOTALL).findall(html_page)
  except:
    match = re.compile('<div id="premium-video".+?src="(.+?)" type', re.DOTALL).findall(html_page)
    
  for link in match: return link 
    
def get_links(html_page):
  videos = []
  info = re.compile('<header class="entry-header.+?href="(.+?)".+?title="Permalink to: "(.+?)".+?<p>(.+?)<',re.DOTALL).findall(html_page)
  for link,title,des in info:
    videos.append({'name': title, 'description' : des, 'thumb': 'thethumb', 'video': link, 'genre': 'News', 'plot': des, 'mediatype': 'tvshow'})
  return videos
        
def page_info(html_page):
  match = re.compile('<div class="x-pagination.+?href="(.+?)" class=',re.DOTALL).findall(html_page)
  for link in match: return link
