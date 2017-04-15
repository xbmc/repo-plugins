from phate89lib import rutils
import re
import math
import urllib

class Raiyoyo(rutils.RUtils):

    USERAGENT="RaiYoYo Kodi Addon"

    def get_url_groupList(self):
        elements = []
        url = "http://www.raiyoyo.rai.it/dl/PortaliRai/Multimedia/PublishingBlock-672f7b84-fa3b-4dcb-ab87-cac436b53f33.html";
        self.log('Trying to get the video list from url ' + url, 4)
        soup = self.getSoup(url)
        container = soup.find("div", class_="boxMultimedia")
        container = container.find('div', class_='mid')
        subparts = container.find_all('div', class_='inBox')
        for subpart in subparts:
          top_part = subpart.find('div', class_="top")
          mid_part = subpart.find('div', class_="mid")
          name = top_part.find('h3')
          if name and name.text.strip():
            self.log("TITLE : "+name.text.strip())
            vidcont = mid_part.find('div', class_='videoContainer')
            divid = vidcont.find('div')
            self.log("ID : "+divid['id'])
            elements.append({ 'title': name.text.strip().encode('utf-8') , 'id': divid['id']})
        return elements
    
    def get_url_punList(self,id):
        elements = []
        url = "http://www.raiyoyo.rai.it/dl/RaiTV/programmi/json/liste/"+id+"-json-V-0.html"
        data = self.getJson(url)
        for ep in data["list"]:
          if ep["masterImage"][0] == '/':
            ep["masterImage"] = "http://www.raiyoyo.rai.it"+ep["masterImage"]
          elements.append({ 'id': ep["itemId"], 'title': ep["name"], 'url': ep["h264"], 'thumbs': ep["masterImage"], 'plot': ep["desc"] })
        return elements
'''
        url = "http://www.raiyoyo.rai.it/dl/PortaliRai/Multimedia/PublishingBlock-672f7b84-fa3b-4dcb-ab87-cac436b53f33.html";
        self.log('Trying to get the video list from url ' + url, 4)
        soup = self.getSoup(url)
        container = soup.find("div", class_="boxMultimedia")
        container = container.find('div', class_='mid')
        subparts = container.find_all('div', class_='inBox')
        for subpart in subparts:
          top_part = subpart.find('div', class_="top")
          mid_part = subpart.find('div', class_="mid")
          name = top_part.find('h3')
          if name and name.text.strip():
            vidcont = mid_part.find('div', class_='videoContainer')
            divid = vidcont.find('div')
            divid_id = divid['id']
            if divid_id == id:
              ul = divid.find('ul')
              ullis = ul.find_all('li',class_='Video ')
              k = 0
              if ullis:
                for ulli in ullis:
                  self.log(ulli)
                  a = ulli.find('a')
                  info = ulli.find('div',class_='Info')
                  info_h2 = info.find('h2')
                  info_title = info_h2.find('a').text.strip().encode('utf-8')
                  url = 'http://www.raiyoyo.rai.it/'+a['href']
                  img = a.find('img')
                  img_url = img['src']
                  self.log("URL = "+url)   
                  self.log("ID = "+id)
                  # minicuccioli
                  if id == "ContentSet-c7b50daa-4e49-45cc-a9ac-f015d64eab35":
                    f0 = urllib.urlopen(url)
                    fc0 = f0.read()
                    self.log(fc0)
                    mini_url = fc0.split('videoURL_MP4',1)[1]
                    mini_url = mini_url.split('"',1)[1]
                    mini_url = mini_url.split('";',1)[0]
                    mini_url = "http:"+mini_url
                    self.log("URL = "+mini_url)
                    if mini_url:
                      elements.append({ 'id': 'ID'+str(k), 'title': info_title, 'url': mini_url.strip(), 'thumbs': '', 'plot': '' }) 
                      k += 1
                  # the rest                      
                  else:              
                    soup_vid = self.getSoup(url);
                    video = soup_vid.find('a')
                    red_url = 'http://www.raiyoyo.rai.it'+video['href']
                    sep = '%0A'
                    red_url = red_url.split(sep, 1)[0]
                    self.log("REDIRECT: "+red_url)
                    f = urllib.urlopen(red_url)
                    myfile = f.read()
                    self.log(myfile)
                    d0 = myfile.split('data-video-url="',1)[1]
                    d1 = d0.split('"',1)[0]
                    self.log("URL = "+d1)
                    if d1:
  #                    f1 = urllib.urlopen(d1)
  #                    myfile1 = f1.read()
  #                    self.log(myfile1)
  #                    d2 = myfile1.split("\n",2)[2];
  #                    self.log("URL(1) = "+d2)
  #                    if d2: 
                        elements.append({ 'id': 'ID'+str(k), 'title': info_title, 'url': d1.strip(), 'thumbs': '', 'plot': '' }) 
                        k += 1
        return elements
'''

# http://www.raiyoyo.rai.it/dl/RaiTV/programmi/json/liste/ContentSet-725a76fe-e793-4c6b-b98f-b35e974988a0-json-V-0.html

# http://www.raiyoyo.rai.it//dl/RaiTV/programmi/media/ContentItem-858070ba-73fe-4cc0-9ca7-e51deea55f78-raiyoyo.html
# blob:http://www.raiyoyo.rai.it/ed60c925-3a26-4179-98b7-b37673355022
# http://www.raiplay.it/video/2016/05/I-Racconti-di-Masha-01-del-15052016-858070ba-73fe-4cc0-9ca7-e51deea55f78.html