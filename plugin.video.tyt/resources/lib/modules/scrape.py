import httplib, logon, re, xbmcgui

from urllib2 import unquote

show = {}
shows = "/shows"

def popup(text):
  xbmcgui.Dialog().ok('plugin.video.tyt', text)

def Get_Show_Episodes(page):
  hosts = {}
  episodes = re.compile('class=""><!----><!----><!----><!----><!----><!----><tyt-feed-tag.+?id="tag">(.+?)</div></tyt-feed-tag><!----><!.+?data-image-id="(.+?)".+?underbox"><.+?Hosts:(.+?)</span></span>.+?id="items"(.+?)</tyt-production-view>',re.DOTALL).findall(page)
  i = 0
  for date, image_id, allhosts, items in episodes:
    hosts_decoded = re.compile('href="(.+?)">(.+?)<',re.DOTALL).findall(allhosts)
    try:
      image = re.search('data-image-id="%s".+?url\((.+?)\)' % image_id, page, re.MULTILINE | re.DOTALL).group(1)
    except:
      image = ''
    x = 0
    for host_info, host in hosts_decoded:
      hosts[x] = {"host": host,
                  "info": host_info
                  }
      x+=1
    item = re.compile('"btn-play" href="(.+?)">.+?href=".+?"> (.+?)</a>.+?tyt-plus-tag.+?<li.+?"">(.+?)</li',re.DOTALL).findall(items)
    for link, description, length in item:
      show[i] = {"date" : date_convert(date),
                 "title": date + ' - ' + length,
                 "image": image,
                 "link": link,
                 "description": description,
                 "hosts" : hosts
                }
      i+=1
  return show

def date_convert(date):
  month = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12"
  }
  return date.split(' ')[1][:-1] + '.' + month.get(date.split(' ')[0]) + '.' + date.split(' ')[2]

def Watch_Episode(page, show):
  try:
    hd = re.search('tytapp-state.+?%s\\\&q;,\\\&q;title.+?hd_video_download_url.+?:\\\&q;(.+?)\\\&q' % show, page, re.MULTILINE | re.DOTALL).group(1) #This works Too, Faster, but tyt.com always screws up
  except:
    hd = None
  try:
    jw = re.search('tytapp-state.+?%s\\\&q;,\\\&q;title.+?\\[JW\\].+?url\\\&q;:\\\&q;(.+?)\\\&q' % show, page, re.MULTILINE | re.DOTALL).group(1)
  except:
    jw = None
  return hd, jw

def List_Shows(page):

  shows = re.compile('class="show responsive-background" aria-label="(.+?)".+?href="(.+?)".+?"(.+?)".+?summary.+?"">(.+?)<',re.DOTALL).findall(page)
  i = 0
  for showname, link, image_id, description in shows:
    #need to find banner, then web_header_image
    banner =  re.search('data-image-id="%s".+?url\((.+?)\)' % image_id, page, re.MULTILINE | re.DOTALL).group(1)
    background = re.search('background-image:url\((.+?)\?w=', page, re.MULTILINE | re.DOTALL).group(1)
    image2 = re.search('href="%s".+?data-image-id="(.+?)"' % link, page, re.MULTILINE | re.DOTALL).group(1)
    avatar =  re.search('data-image-id="%s".+?url\((.+?)\)' % image2, page, re.MULTILINE | re.DOTALL).group(1)
    show[i] = {"show" : showname,
               "background": background,
               "description": description,
               "link" : link,
               "banner" : banner,
               "avatar" : avatar}
    i+=1
  return show

