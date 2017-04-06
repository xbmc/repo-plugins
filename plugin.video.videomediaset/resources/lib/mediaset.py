from phate89lib import rutils
import re
import math

class Mediaset(rutils.RUtils):

    USERAGENT="VideoMediaset Kodi Addon"
    
    def get_prog_root(self):
        self.log('Trying to get the program list', 4)
        url = "http://www.video.mediaset.it/programma/progr_archivio.json"
        data = self.getJson(url)
        return data["programmi"]["group"]

    def get_url_groupList(self,url):
        self.log('Trying to get the groups from program url ' + url, 4)
        if not url.startswith("http"):
            url="http://www.video.mediaset.it"+url
        url=url.replace("archivio-news.shtml","archivio-video.shtml")
        soup=self.getSoup(url)
        container=soup.find("div", class_="main-container")
        subparts=container.find_all('section')
        elements = []
        for subpart in subparts:
            name = subpart.find('h2')
            if name and name.text.strip():
                data=subpart.find('div')
                if data:
                    elements.append({'title': name.text.strip(), 
                                     'url': "http://www.video.mediaset.it/{type}/{area}/{box}.shtml".format(type=data['data-type'],area=data['data-area'],box=data['data-box'])})
        return elements

    def get_prog_epList(self,url):
        self.log('Trying to get the episodes from group url ' + url, 4)
        totres = 0
        count = 0
        page = 1
        arrdata=[]
        maxpage = 200
        while (page < maxpage):
            nurl = "{url}?page={page}".format(url=url,page=page)
            soup = self.getSoup(nurl)
            videos = soup.find_all('div',class_='box')
            if videos:
                for video in videos:
                    if totres == 0 and video.has_attr('data-maxitem'):
                        totres = float(video['data-maxitem'])
                        maxpage = totres
                        totpage = math.ceil(totres / 2)
                    img = video.find('img')
                    p = video.find('p')
                    arrdata.append({'id': video['data-id'],'title':img['alt'].encode('utf-8'),'thumbs':img['data-src'].replace("176x99","640x360"),'plot':p.text.strip().encode('utf-8')});
            page = page + 1

        return arrdata

    def get_prog_seasonList(self,url):
        self.log('Trying to get the seasons from program url ' + url, 4)
        if not url.startswith("http"):
            url="http://www.video.mediaset.it"+url
        url=url.replace("archivio-news.shtml","archivio-video.shtml")
        soup = self.getSoup(url)
        arrdata = []
        container=soup.find("li", class_="season clearfix")
        if container:
            links = container.find_all("a")
            if links:
                for link in links:
                    if not link.has_attr("class"):
                        arrdata.append({"title": link.text.strip().encode('utf-8'), "url": link['href']})
        return arrdata

    def get_global_epList(self,mode,range=0):
        self.log('Trying to get episodes with mode ' + str(mode), 4)
        if mode == 0: 
            url = "http://www.video.mediaset.it/bacino/bacinostrip_1.shtml?page=all"
        elif mode == 1:
            url = "http://www.video.mediaset.it/piu_visti/piuvisti-{range}.shtml?page=all".format(range=range)
        elif mode == 2:
            url = "http://www.video.mediaset.it/bacino/bacinostrip_5.shtml?page=all"

        soup = self.getSoup(url)
        arrdata=[]
        videos = soup.find_all('div',class_='box')
        if videos:
            for video in videos:
                a = video.find('a', {'data-type': 'video'})
                img = a.find('img')
                imgurl = img['data-src']
                res = re.search("([0-9][0-9][0-9][0-9][0-9]+)",imgurl)
                if res:
                    idv = res.group(1)
                else:
                    idv = re.search("([0-9][0-9][0-9][0-9][0-9]+)",a['href']).group(1)
                p = video.find('p', class_='descr')
                arrdata.append({'id': idv,'url':a['href'],'title':img['alt'].encode("utf-8"),'tipo':video['class'],'thumbs':imgurl.replace("176x99","640x360"),'plot':p.text.strip().encode("utf-8")})
        return arrdata

    def get_canali_live(self):
        self.log('Getting the list of live channels', 4)
        
        url = "http://live1.msf.ticdn.it/Content/HLS/Live/Channel(CH{ch}HA)/Stream(04)/index.m3u8"

        arrdata = []

        arrdata.append({'title':"Canale 5", 'url':url.format(ch='01'),'thumbs': "Canale_5.png"})
        arrdata.append({'title':"Italia 1", 'url':url.format(ch='02'),'thumbs': "Italia_1.png"})
        arrdata.append({'title':"Rete 4", 'url':url.format(ch='03'),'thumbs': "Rete_4.png"})
        arrdata.append({'title':"La 5", 'url':url.format(ch='04'),'thumbs': "La_5.png"})
        arrdata.append({'title':"Italia 2", 'url':url.format(ch='05'),'thumbs': "Italia_2.png"})
        arrdata.append({'title':"Iris", 'url':url.format(ch='06'),'thumbs': "Iris.png"})
        arrdata.append({'title':"Top Crime", 'url':url.format(ch='07'),'thumbs': "Top_Crime.png"})
        arrdata.append({'title':"Mediaset Extra", 'url':url.format(ch='09'),'thumbs': "Mediaset_Extra.png"})
        arrdata.append({'title':"TGCOM24", 'url':url.format(ch='10'),'thumbs': "TGCOM24.png"})
        return arrdata

    def get_stream(self, id):
        self.log('Trying to get the stream with id ' + str(id), 4)

        url = "http://cdnsel01.mediaset.net/GetCdn.aspx?streamid={id}&format=json".format(id=id)

        jsn = self.getJson(url)

        if jsn and jsn["state"]=="OK":

            stream = {}
            for vlist in jsn["videoList"]:
                self.log( "videomediaset: streams {url}".format(url=vlist))
                if ( vlist.find(".wmv") > 0): stream["wmv"] = vlist
                if ( vlist.find(".mp4") > 0): stream["mp4"] = vlist
                if ( vlist.find(".f4v") > 0): stream["f4v"] = vlist
                if ( vlist.find(".ism") > 0): stream["smoothstream"] = vlist
            return stream
        return False