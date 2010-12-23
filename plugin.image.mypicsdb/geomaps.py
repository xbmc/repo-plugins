import xbmcgui
from urllib2 import Request, urlopen
from urllib import urlencode
#import urllib2,urllib
from os.path import join,isfile,basename
from traceback import print_exc
from xbmcaddon import Addon
addon = Addon(id='plugin.image.mypicsdb')
__language__ = addon.getLocalizedString

ACTION_CONTEXT_MENU = [117]
ACTION_MENU = [122]
ACTION_PREVIOUS_MENU = [9]
ACTION_SHOW_INFO = [11]
ACTION_EXIT_SCRIPT = [10, 13]
ACTION_DOWN = [4]
ACTION_UP = [3]

class main(xbmcgui.Window):

    def __init__(self,*args,**kwargs):
        self.zoomlevel = 12
        self.ZMAX = 21
        self.ZMIN = 0
        
        self.DATA_PATH = kwargs["datapath"]
        self.place = kwargs["place"]
        self.picfile = kwargs["picfile"]
        self.draw()
        self.load_map()
        

    def draw(self):
        width = self.getWidth()
        height = self.getHeight()
        self.ctrl_map = xbmcgui.ControlImage(0,0,width,height,"",aspectRatio=2)
        self.ctrl_pic = xbmcgui.ControlImage(50, 50, 200, 200,"", aspectRatio=2)
        self.lbl_info = xbmcgui.ControlLabel(20,20,width-40,20,"info",'font13',alignment=2)
        self.addControl(self.ctrl_map)
        self.addControl(self.ctrl_pic)
        self.addControl(self.lbl_info)
        self.lbl_info.setLabel(__language__(30223))#Use UP and DOWN arrow to zoom in / out

    def zoom(self,way,step=1):
        if way=="+":
            self.zoomlevel = self.zoomlevel + step
        elif way=="-":
            self.zoomlevel = self.zoomlevel - step
        else:
            self.zoomlevel = step
        if self.zoomlevel > self.ZMAX: self.zoomlevel = self.ZMAX
        elif self.zoomlevel < self.ZMIN: self.zoomlevel = self.ZMIN
        self.load_map()

    def load_map(self):
        #google geolocalisation 
        static_url = "http://maps.google.com/maps/api/staticmap?"
        param_dic = {#location parameters (http://gmaps-samples.googlecode.com/svn/trunk/geocoder/singlegeocode.html)
                     "center":"",       #(required if markers not present)
                     "zoom":self.zoomlevel,         # 0 to 21+ (req if no markers
                     #map parameters
                     "size":"640x640",  #widthxheight (required)
                     "format":"jpg",    #"png8","png","png32","gif","jpg","jpg-baseline" (opt)
                     "maptype":"hybrid",      #"roadmap","satellite","hybrid","terrain" (opt)             
                     "language":"",
                     #Feature Parameters:
                     "markers" :"color:red|label:P|%s",#(opt)
                                        #markers=color:red|label:P|lyon|12%20rue%20madiraa|marseille|Lille
                                        #&markers=color:blue|label:P|Australie
                     "path" : "",       #(opt)
                     "visible" : "",    #(opt)
                     #Reporting Parameters:
                     "sensor" : "false" #is there a gps on system ? (req)
                     }

        param_dic["markers"]=param_dic["markers"]%self.place
        
        request_headers = { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10' }
        request = Request(static_url+urlencode(param_dic), None, request_headers)
        urlfile = urlopen(request)

        extension = urlfile.info().getheader("Content-Type","").split("/")[1]
        filesize = int(urlfile.info().getheader("Content-Length",""))

        mapfile = join(self.DATA_PATH,basename(self.picfile).split(".")[0]+"_maps%s."%self.zoomlevel+extension)
        #print mapfile
        if not isfile(mapfile):
            #mapfile is not downloaded yet, download it now...
            try:
                f=open(mapfile,"wb")
            except:
                print_exc()
            for i in range(1+(filesize/10)):
                f.write(urlfile.read(10))
                self.lbl_info.setLabel(__language__(30221)%(100*(float(i*10)/filesize)))#getting map... (%0.2f%%)
            urlfile.close()
            #pDialog.close()
            try:
                f.close()
            except:
                print_exc()
                pass
        self.set_pic(self.picfile)
        self.set_map(mapfile)
        self.lbl_info.setLabel(__language__(30222)%int(100*(float(self.zoomlevel)/self.ZMAX)))#Zoom level %s
        
    def set_map(self,mapfile):
        self.ctrl_map.setImage(mapfile)

    def set_pic(self,picfile):
        self.ctrl_pic.setImage(picfile)
    
    def onAction(self,action):
        if action in ACTION_PREVIOUS_MENU:
            self.close()
        elif action in ACTION_EXIT_SCRIPT:
            self.close()
        elif action in ACTION_UP:
            self.zoom("+")
        elif action in ACTION_DOWN:
            self.zoom("-")
        else:
            pass
            
