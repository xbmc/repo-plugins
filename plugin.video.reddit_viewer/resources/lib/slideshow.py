import xbmc
import json
import xbmcvfs
import random
import sys

from xbmcgui import ControlImage, WindowDialog, WindowXMLDialog, Window, ControlTextBox, ControlLabel

#autoSlideshow

from default import addon, addon_path, addonID
from utils import log, translation
from reddit import reddit_request
from domains import sitesBase, parse_reddit_link
from actions import listAlbum

from utils import unescape, post_excluded_from, remove_duplicates, remove_dict_duplicates

import threading
from Queue import Queue

ADDON_NAME = addonID      #addon.getAddonInfo('name')  <--changed to id
ADDON_PATH = addon_path   #addon.getAddonInfo('path')

random_post_order = addon.getSetting("random_post_order") == "true"
random_image_order= addon.getSetting("random_image_order") == "true"

q=Queue()

def slideshowAlbum(dictlist, name):
    log("slideshowAlbum")

    #introduce a duplicate
#     dictlist.append(  {'li_label': 'aaa1',
#                         'li_label2': 'descrip',
#                         'DirectoryItem_url': 'http://i.imgur.com/K5uhHZF.jpg',
#                         'li_thumbnailImage': 'media_thumb_url',
#                         'width': 12,
#                         'height': 123,
#                                 }  )
#
#     dictlist.append(  {'li_label': 'aaa2',
#                         'li_label2': 'descrip',
#                         'DirectoryItem_url': 'http://i.imgur.com/2C3G23c.jpg',
#                         'li_thumbnailImage': 'media_thumb_url',
#                         'width': 12,
#                         'height': 123,
#                                 }  )
#
#     dictlist.append(  {'li_label': 'aaa3',
#                         'li_label2': 'descrip',
#                         'DirectoryItem_url': 'http://i.imgur.com/DXsb037.jpg',
#                         'li_thumbnailImage': 'media_thumb_url',
#                         'width': 12,
#                         'height': 123,
#                                 }  )
#
#     for d in dictlist:
#         media_url=d.get('DirectoryItem_url')
#         title    =d.get('li_label') if d.get('li_label') else ''
#         width    =d.get('width')
#         height   =d.get('height')
#         description=d.get('description')
#         log( "  %s... %s " %(title.ljust(15)[:15] ,media_url )  )

    nl = remove_dict_duplicates( dictlist, 'DirectoryItem_url')

#    log("***after***")
#     for d in nl:
#         media_url=d.get('DirectoryItem_url')
#         title    =d.get('li_label') if d.get('li_label') else ''
#         width    =d.get('width')
#         height   =d.get('height')
#         description=d.get('description')
#         log( "  %s... %s " %(title.ljust(15)[:15] ,media_url )  )


    for e in nl:
        q.put(e)

    ev=threading.Event()

    #s= HorizontalSlideScreensaver2(ev,q)
    s= ScreensaverManager(ev,q)

    try:
        s.start_loop()
    except Exception as ex:
        log("  EXCEPTION slideshowAlbum:="+ str( sys.exc_info()[0]) + "  " + str(ex) )

    return


def autoSlideshow(url, name, type_):

    log('starting slideshow '+ url)
    ev=threading.Event()

    entries = []
    #watchdog_counter=0
    preview_w=0
    preview_h=0
    image=''

    #content = opener.open(url).read()
    content = reddit_request(url)
    if not content: return
    #log( str(content) )
    #content = json.loads(content.replace('\\"', '\''))
    content = json.loads(content)

    log("slideshow %s:Parsing %d items: %s" %( type_, len(content['data']['children']), 'random' if random_post_order else 'normal order' )    )

    data_children = content['data']['children']

    if random_post_order:
        random.shuffle(data_children)

    for j_entry in data_children:
        try:
            title = unescape(j_entry['data']['title'].encode('utf-8'))
            log("  TITLE:%s [r/%s]"  %( title, j_entry.get('data').get('subreddit') )  )

            try:    description = unescape(j_entry['data']['media']['oembed']['description'].encode('utf-8'))
            except: description = ''
            #log('    description  [%s]' %description)
            try:    post_selftext=unescape(j_entry['data']['selftext'].encode('utf-8'))
            except: post_selftext=''
            #log('    post_selftext[%s]' %post_selftext)

            description=post_selftext+'[CR]'+description if post_selftext else description

            try:
                media_url = j_entry['data']['url']
            except:
                media_url = j_entry['data']['media']['oembed']['url']

            try:
                preview=j_entry['data']['preview']['images'][0]['source']['url'].encode('utf-8').replace('&amp;','&')
                try:
                    preview_h = float( j_entry['data']['preview']['images'][0]['source']['height'] )
                    preview_w = float( j_entry['data']['preview']['images'][0]['source']['width'] )
                except:
                    preview_w=0
                    preview_h=0

            except Exception as e:
                #log("   getting preview image EXCEPTION:="+ str( sys.exc_info()[0]) + "  " + str(e) )
                preview=""


            ld=parse_reddit_link(link_url=media_url, assume_is_video=False, needs_preview=True, get_playable_url=True )
            if ld:
                if not preview:
                    preview = ld.poster

                if (addon.getSetting('include_albums')=='true') and (ld.media_type==sitesBase.TYPE_ALBUM) :
                    dictlist = listAlbum( media_url, title, 'return_dictlist')
                    for d in dictlist:
                        #log('    (S) adding items from album ' + title  +' ' + d.get('DirectoryItem_url') )
                        t2=d.get('li_label') if d.get('li_label') else title
                        #entries.append([ t2, d.get('DirectoryItem_url'), d.get('width'), d.get('height'), len(entries)])

                        d['li_label']=t2
                        entries.append( d )
                        #title=''  #only put the title in once.
                else:
                    if addon.getSetting('use_reddit_preview')=='true':
                        if preview: image=preview
                        elif ld.poster: image=ld.poster
                        #if preview: entries.append([title,preview,preview_w, preview_h,len(entries)]) #log('      (N)added preview:%s %s' %( title,preview) )
                        #elif ld.poster: entries.append([title,ld.poster,preview_w, preview_h,len(entries)])    #log('      (N)added poster:%s %s' % ( title,ld.poster) )
                    else:
                        if ld.poster:  image=ld.poster #entries.append([title,ld.poster,preview_w, preview_h,len(entries)])
                        elif preview: image=preview  #entries.append([title,preview,preview_w, preview_h,len(entries)])
                        #if ld.poster: entries.append([title,ld.poster,preview_w, preview_h,len(entries)])
                        #elif preview: entries.append([title,preview,preview_w, preview_h,len(entries)])

                    append_entry( entries, title,image,preview_w, preview_h, description )
            else:
                append_entry( entries, title,preview,preview_w, preview_h, description )
                #log('      (N)added preview:%s' % title )

        except Exception as e:
            log( '  autoPlay exception:' + str(e) )

    #log( repr(entries))

    entries = remove_dict_duplicates( entries, 'DirectoryItem_url')

#     #for i,e in enumerate(entries): log('  e1-%d %s' %(i, e[1]) )
#     def k2(x): return x[1]
#     entries=remove_duplicates(entries, k2)
#     #for i,e in enumerate(entries): log('  e2-%d %s' %(i, e[1]) )

    for i, e in enumerate(entries):
        log('  possible playable items({0}) {1}...{2}x{3}  {4}'.format( i, e['li_label'].ljust(15)[:15], repr(e.get('width')),repr(e.get('height')),  e.get('DirectoryItem_url')) )

    if len(entries)==0:
        log('  Play All: no playable items' )
        xbmc.executebuiltin('XBMC.Notification("%s","%s")' %(translation(32054), translation(32055)  ) )  #Play All     No playable items
        return

    #if type.endswith("_RANDOM"):
    #    random.shuffle(entries)

    #for title, url in entries:
    #    log("  added to playlist:"+ title + "  " + url )

    log("**********playing slideshow*************")

    for e in entries:
        q.put(e)

    #s= HorizontalSlideScreensaver(ev,q)
    s= ScreensaverManager(ev,q)

    try:
        s.start_loop()
    except Exception as e:
        log("  EXCEPTION slideshowAlbum:="+ str( sys.exc_info()[0]) + "  " + str(e) )


    return

def make_dictlist_entry(title,preview,width, height, description ):
    return {'li_label'         : title,
            'li_label2'        : '',
            'DirectoryItem_url': preview,
            'width'            : width,
            'height'           : height,
            'description'      : description,
            }
def append_entry( e, title,preview,width, height, description ):
    if preview:
        e.append( make_dictlist_entry(title,preview,width, height, description ) )


### credit to https://github.com/dersphere/script.screensaver.multi_slideshow for this code
#
#
CHUNK_WAIT_TIME = 250
ACTION_IDS_EXIT = [9, 10, 13, 92]
ACTION_IDS_PAUSE = [12,68,79,229]   #ACTION_PAUSE = 12  ACTION_PLAY = 68  ACTION_PLAYER_PLAY = 79   ACTION_PLAYER_PLAYPAUSE = 229


class ScreensaverWindow(WindowDialog):
    def __init__(self, exit_callback):
        self.exit_callback = exit_callback
        #log('  #####%d ' %  self.getResolution())

    def onAction(self, action):
        action_id = action.getId()
        if action_id in ACTION_IDS_EXIT:
            self.exit_callback()

class ScreensaverXMLWindow(WindowXMLDialog):

        #WindowXMLDialog.__init__(xmlfilename, scriptPath)
        #self.exit_callback = exit_callback
        #WindowXMLDialog.__init__( "xmlfilename", "scriptPath" )

        #log('  #####%d ' %  self.getResolution())

    def __init__(self, *args, **kwargs):
        WindowXMLDialog.__init__(self, *args, **kwargs)
        #xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.exit_callback = kwargs.get("exit_callback")
        #self.subreddits_file = kwargs.get("exit_callback")

    def onAction(self, action):
        action_id = action.getId()
        self.exit_callback(action_id) #pass the action id to the calling class

#screensaver code original by : Tristan Fischer (sphere@dersphere.de)
#  http://forum.kodi.tv/showthread.php?tid=173734
class ScreensaverBase(object):

    MODE = None
    IMAGE_CONTROL_COUNT = 10
    FAST_IMAGE_COUNT = 0
    NEXT_IMAGE_TIME = 2000
    BACKGROUND_IMAGE = 'srr_blackbg.jpg'

    pause_requested=False
    info_requested=False

    def __init__(self, thread_event, image_queue):
        #self.log('__init__ start')
        self.exit_requested = False
        self.toggle_info_display_requested=False
        self.background_control = None
        self.preload_control = None
        self.image_count = 0
        #self.image_controls = []
        self.tni_controls = []
        self.global_controls = []
        self.exit_monitor = ExitMonitor(self.stop)

        self.init_xbmc_window()
#         self.xbmc_window = ScreensaverWindow(self.stop)
#         self.xbmc_window.show()

        self.init_global_controls()
        self.load_settings()
        self.init_cycle_controls()
        self.stack_cycle_controls()
        #self.log('__init__ end')

    def init_xbmc_window(self):
        self.xbmc_window = ScreensaverXMLWindow( "slideshow02.xml", addon_path, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.show()


    def init_global_controls(self):
        #self.log('  init_global_controls start')

        loading_img = xbmc.validatePath('/'.join((ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'srr_busy.gif' )))

        self.loading_control = ControlImage(576, 296, 128, 128, loading_img)
        self.preload_control = ControlImage(-1, -1, 1, 1, '')
        self.background_control = ControlImage(0, 0, 1280, 720, '')
        self.global_controls = [
            self.preload_control, self.background_control, self.loading_control
        ]
        self.xbmc_window.addControls(self.global_controls)
        #self.log('  init_global_controls end')

    def load_settings(self):
        pass

    def init_cycle_controls(self):
        #self.log('  init_cycle_controls start')
        for _ in xrange(self.IMAGE_CONTROL_COUNT):
            img_control = ControlImage(0, 0, 0, 0, '', aspectRatio=2)  #(values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
            txt_control = ControlTextBox(0, 0, 0, 0, font='font16')
#                     xbfont_left = 0x00000000
#                     xbfont_right = 0x00000001
#                     xbfont_center_x = 0x00000002
#                     xbfont_center_y = 0x00000004
#                     xbfont_truncated = 0x00000008
            #ControlLabel(x, y, width, height, label, font=None, textColor=None, disabledColor=None, alignment=0, hasPath=False, angle=0)
            #txt_control = ControlLabel(0, 0, 0, 0, '', font='font30', textColor='', disabledColor='', alignment=6, hasPath=False, angle=0)

            #self.image_controls.append(img_control)
            self.tni_controls.append([txt_control,img_control])
        #self.log('  init_cycle_controls end')

    def stack_cycle_controls(self):
        #self.log('stack_cycle_controls start')
        # add controls to the window in same order as image_controls list
        # so any new image will be in front of all previous images
        #self.xbmc_window.addControls(self.image_controls)
        #self.xbmc_window.addControls(self.text_controls)

        self.xbmc_window.addControls(self.tni_controls[1])
        self.xbmc_window.addControls(self.tni_controls[0])

        #self.log('stack_cycle_controls end')

    def start_loop(self):
        self.log('start_loop start')

        #images = self.get_images('q')
        desc_and_images = self.get_description_and_images('q')

        if random_image_order:    #addon.getSetting('random_image_order') == 'true':
            random.shuffle(desc_and_images)
        desc_and_images_cycle=cycle(desc_and_images)

        #image_url_cycle = cycle(images)
        #image_controls_cycle = cycle(self.image_controls)
        tni_controls_cycle= cycle(self.tni_controls)

        #self.log('  image_url_cycle %s' % image_url_cycle)


        self.hide_loading_indicator()

        #pops the first one
        #image_url = image_url_cycle.next()
        desc_and_image=desc_and_images_cycle.next()
        #self.log('  image_url_cycle.next %s' % image_url)

        #get the current screen saver value
        #saver_mode = json.loads(  xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettingValue", "params": {"setting":"screensaver.mode" } }')  )
        #saver_mode = saver_mode.get('result').get('value')
        #log('****screensavermode=' + repr(saver_mode) )
        #set the screensaver to none
        #xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method":"Settings.setSettingValue", "params": {"setting":"screensaver.mode", "value":""} } ' )

        while not self.exit_requested:
            self.log('  using image: %s ' % ( repr(desc_and_image ) ) )


            if not self.pause_requested:
                #pops an image control
                #image_control = image_controls_cycle.next()
                tni_control = tni_controls_cycle.next()

                #process_image done by subclass( assign animation and stuff to image control )
                #self.process_image(image_control, image_url)
                #self.process_image(image_control, desc_and_image)
                self.process_image(tni_control, desc_and_image)

                #image_url = image_url_cycle.next()
                desc_and_image=desc_and_images_cycle.next()


            #self.wait()
            if self.image_count < self.FAST_IMAGE_COUNT:
                self.image_count += 1
            else:
                #self.preload_image(image_url)
                self.preload_image(desc_and_image[1])
                self.wait()

        self.log('start_loop end')

        #return the screensaver back
        #xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method":"Settings.setSettingValue", "params": {"setting":"screensaver.mode", "value" : "%s"} }' % saver_mode )


    def get_description_and_images(self, source):
        #self.log('get_images2')
        self.image_aspect_ratio = 16.0 / 9.0

        images = []

        if source == 'image_folder':
            #image folder source not used
            path = '' #SlideshowCacheFolder  #addon.getSetting('image_path')
            if path:
                images = self._get_folder_images(path)
        elif source == 'q':
            #implement width & height extract here.
            #images=[[item[0], item[1],item[2], item[3], ] for item in q.queue]

            #[title,media_url, width, height, len(entries), description])
            images=[  [i.get('li_label'), i.get('DirectoryItem_url'),i.get('width'), i.get('height'), i.get('description') ] for i in q.queue]

            log( "queue size:%d" %q.qsize() )
            #texts=[item[0] for item in q.queue]
            #for i in images: self.log('   image: %s' %i)
            #self.log('    %d images' % len(images))

        return images


    #for movie, audio or tv shows

    def _get_folder_images(self, path):
        self.log('_get_folder_images started with path: %s' % repr(path))
        _, files = xbmcvfs.listdir(path)
        images = [
            xbmc.validatePath(path + f) for f in files
            if f.lower()[-3:] in ('jpg', 'png')
        ]
        #if addon.getSetting('recursive') == 'true':
        #    for directory in dirs:
        #        if directory.startswith('.'):
        #            continue
        #        images.extend(
        #            self._get_folder_images(
        #                xbmc.validatePath('/'.join((path, directory, '')))
        #            )
        #        )
        self.log('_get_folder_images ends')
        return images

    def hide_loading_indicator(self):
        bg_img = xbmc.validatePath('/'.join(( ADDON_PATH, 'resources', 'skins', 'Default', 'media', self.BACKGROUND_IMAGE )))
        #bg_img = self.BACKGROUND_IMAGE
        self.loading_control.setAnimations([(
            'conditional',
            'effect=fade start=100 end=0 time=500 condition=true'
        )])
        self.background_control.setAnimations([(
            'conditional',
            'effect=fade start=0 end=100 time=500 delay=500 condition=true'
        )])
        self.background_control.setImage(bg_img)

    def process_image(self, image_control, desc_and_image):
        # Needs to be implemented in sub class
        raise NotImplementedError

    def preload_image(self, image_url):
        # set the next image to an unvisible image-control for caching
        #self.log('preloading image: %s' % repr(image_url))
        self.preload_control.setImage(image_url)
        #self.log('preloading done')

    def wait(self):
        # wait in chunks of 500ms to react earlier on exit request
        chunk_wait_time = int(CHUNK_WAIT_TIME)
        remaining_wait_time = int(self.NEXT_IMAGE_TIME)
        while remaining_wait_time > 0:
            if self.exit_requested:
                self.log('wait aborted')
                return
            if self.toggle_info_display_requested:  #this value is set on specific keypress in action_id_handler
                #self.log('toggle_info_display_requested')
                self.toggle_info_display_requested=False
                self.toggle_info_display_handler()
            if remaining_wait_time < chunk_wait_time:
                chunk_wait_time = remaining_wait_time
            remaining_wait_time -= chunk_wait_time
            xbmc.sleep(chunk_wait_time)

    def action_id_handler(self,action_id):
        #log('  action ID:' + str(action_id) )
        if action_id in ACTION_IDS_EXIT:
            #self.exit_callback()
            self.stop()
        if action_id in ACTION_IDS_PAUSE:
            self.pause()

        if action_id == 11: #xbmcgui.ACTION_SHOW_INFO:
            self.toggle_info_display_requested=True  #not self.info_requested

    def toggle_info_display_handler(self):
        pass

    def stop(self,action_id=0):
        self.log('stop')
        self.exit_requested = True
        self.exit_monitor = None

    def pause(self):
        #pause disabled. too complicated(not possible?) to stop animation
        #self.pause_requested = not self.pause_requested
        #self.log('pause %s' %self.pause_requested )
        pass

    def close(self):
        self.del_controls()

    def del_controls(self):
        #self.log('del_controls start')
        #self.xbmc_window.removeControls(self.img_controls)
        try: self.xbmc_window.removeControls(self.tni_controls[0]) #imageControls
        except: pass
        try: self.xbmc_window.removeControls(self.tni_controls[1]) #textBoxes
        except: pass

        self.xbmc_window.removeControls(self.global_controls)
        self.preload_control = None
        self.background_control = None
        self.loading_control = None
        self.tni_controls = []
        self.global_controls = []
        self.xbmc_window.close()
        self.xbmc_window = None
        #self.log('del_controls end')

    def log(self, msg):
        log(u'slideshow: %s' % msg)



class HorizontalSlide2(ScreensaverBase):

    MODE = 'slideLeft'
    BACKGROUND_IMAGE = '' #'srr_blackbg.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 0
    DISTANCE_RATIO = 0.7
    SPEED = 1.0
    CONCURRENCY = 1.0
    #SCREEN = 0
    image_control_ids=[101,102,103,104,105]   #control id's defined in ScreensaverXMLWindow xml file

    def init_xbmc_window(self):
        #self.xbmc_window = ScreensaverWindow(  exit_callback=self.stop )
        self.xbmc_window = ScreensaverXMLWindow( "slideshow02.xml", addon_path, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.setCoordinateResolution(5)
        self.xbmc_window.show()

    def load_settings(self):
        self.SPEED = float(addon.getSetting('slideshow_speed'))
        self.SHOW_TITLE = addon.getSetting('show_title') == 'true'
        self.toggle_info_display_requested = False
        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))

        self.MAX_TIME = int(8000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(12000.0 / self.SPEED)

        self.TEXT_ANIMATIONS= [
                 ('conditional', 'condition=true effect=fade delay=0 time=500 start=0 end=100  ' ) ,
                 ('conditional', 'condition=true effect=fade delay=%s time=500 start=100 end=0 tween=circle easing=in' %(1.45*self.MAX_TIME)  ) ]

    def init_cycle_controls(self):
        pass

    def stack_cycle_controls(self):

        #self.txt_background=ControlImage(720, 0, 560, 720, 'srr_dialog-bg.png', aspectRatio=1)
        #self.xbmc_window.addControl( self.txt_background  )
        self.txt_group_control=self.xbmc_window.getControl(200)
        self.title_control=self.xbmc_window.getControl(201)
        self.desc_control=self.xbmc_window.getControl(202)


    def start_loop(self):
        self.log('start_loop start')

        desc_and_images = self.get_description_and_images('q')

        if random_image_order:    #addon.getSetting('random_image_order') == 'true':
            random.shuffle(desc_and_images)
        desc_and_images_cycle=cycle(desc_and_images)

        image_controls_cycle= cycle(self.image_control_ids)

        self.hide_loading_indicator()

        #pops the first one
        #desc_and_image=desc_and_images_cycle.next()
        self.next_desc_and_image=desc_and_images_cycle.next()
        #self.log('  image_url_cycle.next %s' % image_url)


        while not self.exit_requested:
            self.log('  using image: %s ' % ( repr(self.next_desc_and_image ) ) )


            image_control_id = image_controls_cycle.next()

            #process_image done by subclass( assign animation and stuff to image control )
            self.toggle_info_display()

            self.process_image(image_control_id)

            self.current_desc_and_image=self.next_desc_and_image
            #image_url = image_url_cycle.next()
            self.next_desc_and_image=desc_and_images_cycle.next()

            #self.wait()
            if self.image_count < self.FAST_IMAGE_COUNT:
                self.image_count += 1
            else:
                #self.preload_image(image_url)
                self.preload_image(self.next_desc_and_image[1])
                self.wait()

        self.log('start_loop end')

    def ret_image_ar(self,desc_and_image):
        width =desc_and_image[2] if desc_and_image[2] else 0
        height=desc_and_image[3] if desc_and_image[3] else 0
        if width>0 and height>0:
            ar=float(float(width)/height)
        else:
            ar=1.0

        return width,height,ar

    def toggle_info_display_handler(self):
        self.SHOW_TITLE=not self.SHOW_TITLE
        self.toggle_info_display_requested=False
        self.toggle_info_display(show_next=False)

    def toggle_info_display(self,show_next=True):
        if show_next:
            desc_and_image=self.next_desc_and_image
        else:
            desc_and_image=self.current_desc_and_image

        title      =desc_and_image[0]
        description=desc_and_image[4] if desc_and_image[4] else ''

        if self.SHOW_TITLE:
#             #set the animation on the group instead of the individual controls
#             if self.title_control.getText() == title:  #avoid animating the same text label if previous one is the same
#                 self.txt_group_control.setAnimations( [ ('conditional', 'condition=true effect=fade delay=0 time=0 start=100 end=100  ' ) ]  )
#                 #self.title_control.setAnimations( [ ('conditional', 'condition=true effect=fade delay=0 time=0 start=100 end=100  ' ) ]  )
#                 #self.desc_control.setAnimations( [ ('conditional', 'condition=true effect=fade delay=0 time=0 start=100 end=100  ' ) ]  )
#             else:
#                 self.txt_group_control.setAnimations( self.TEXT_ANIMATIONS )
#                 #self.title_control.setAnimations( self.TEXT_ANIMATIONS )
#                 #self.desc_control.setAnimations( self.TEXT_ANIMATIONS )
#                 pass

            #hide the title control if missing (this is done in skin but can also be done in python)
            #if desc_and_image[0]:
            self.title_control.setText(title)
            #    self.title_control.setVisible(True)
            #else:
            #    self.title_control.setVisible(False)
            self.txt_group_control.setAnimations( self.TEXT_ANIMATIONS )

            self.desc_control.setText(description.replace('\n\n','\n'))
            self.txt_group_control.setVisible(True)
        else:
            self.txt_group_control.setVisible(False)

    def process_image(self, image_control_id):

        #width,height,ar = self.ret_image_ar(desc_and_image)
        #log('  %dx%d %f' %(width,height,ar ) )

        direction=random.choice([1,0])
        sx=1280;ex=-1280

        if direction:
            sx,ex=ex,sx

        t=self.MAX_TIME

        self.IMAGE_ANIMATIONS = [
                ('conditional', 'effect=slide start=%d,0   end=0,0    time=%s tween=cubic  easing=out delay=0  condition=true' %(sx, t) ),
                ('conditional', 'effect=fade  start=0      end=100    time=%s tween=circle easing=out delay=0  condition=true' % (0.8*t) ),
                ('conditional', 'effect=slide start=0,0    end=%d,0   time=%s tween=cubic  easing=in  delay=%s condition=true' %(ex, t, (0.8*t)) ),
                ('conditional', 'effect=fade  start=100    end=0      time=%s tween=circle easing=in  delay=%s condition=true' %(t, (t)) ),
            ]

        #the image will align 'top' of the image control if there is a description. but will look unbalanced if there is no description.
        #  I couldn't find a way to programatically 'center' the image in the image control.
        #  so, instead, i made 5 more image controls with id +50 in the slideshow xml that had the images centered.
        #  and use those controlid if there is no description
        description=self.next_desc_and_image[4]
        if description and self.SHOW_TITLE:
            image_control=self.xbmc_window.getControl(image_control_id)
        else:
            image_control=self.xbmc_window.getControl( image_control_id + 50 )


        image_control.setVisible(False)
        image_control.setImage('')

        image_control.setImage(self.next_desc_and_image[1])
        image_control.setPosition(0, 0)
        image_control.setWidth(1280)   #16:9
        #image_control.setWidth(1680)    #21:9
        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)
        # show the image
        image_control.setVisible(True)



class HorizontalSlideScreensaver(ScreensaverBase):

    MODE = 'slideLeftx'
    BACKGROUND_IMAGE = 'srr_blackbg.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 0
    DISTANCE_RATIO = 0.7
    SPEED = 1.0
    CONCURRENCY = 1.0
    #SCREEN = 0
    IMAGE_ANIMATIONS = [ ]

    TEXT_ANIMATIONS= [ ]

    def load_settings(self):
        self.SPEED = float(addon.getSetting('slideshow_speed'))
        self.SHOW_TITLE = addon.getSetting('show_title') == 'true'

        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))
        self.MAX_TIME = int(8000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(12000.0 / self.SPEED)

        self.TEXT_ANIMATIONS= [
                ('conditional', 'condition=true effect=fade delay=0 time=500 start=0 end=100  ' ),
                ('conditional', 'condition=true effect=fade delay=%s time=500 start=100 end=0 tween=circle easing=in' % self.NEXT_IMAGE_TIME  ) ]


    #using WindowXMLDialog(ScreensaverXMLWindow) instead of WindowDialog. the image used in text background does not load when using WindowDialog (???)  some images load, most don't
    def init_xbmc_window(self):
        #self.xbmc_window = ScreensaverWindow(  exit_callback=self.stop )
        self.xbmc_window = ScreensaverXMLWindow( "slideshow01.xml", addon_path, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.setCoordinateResolution(5)
        self.xbmc_window.show()


    def stack_cycle_controls(self):

        for txt_ctl, img_ctl in self.tni_controls:
            self.xbmc_window.addControl(img_ctl)

        if self.SHOW_TITLE:
            self.txt_background=ControlImage(0, 685, 1280, 40, 'srr_dialog-bg.png', aspectRatio=1)
            self.xbmc_window.addControl( self.txt_background  )

            #ControlLabel(x, y, width, height, label, font=None, textColor=None, disabledColor=None, alignment=0, hasPath=False, angle=0)
            self.image_label=ControlLabel(10,688,1280,30,'',font='font16', textColor='', disabledColor='', alignment=6, hasPath=False, angle=0)
            self.xbmc_window.addControl( self.image_label  )
        #for txt_ctl, img_ctl in self.tni_controls:
        #    self.xbmc_window.addControl(txt_ctl)

    def process_image(self, tni_control, desc_and_image):
        image_control=tni_control[1]
        text_control=tni_control[0]

        image_control.setVisible(False)
        image_control.setImage('')
        text_control.setVisible(False)
        text_control.setText('')

        direction=random.choice([1,0])
        sx=1280;ex=-1280

        if direction:
            sx,ex=ex,sx

        t=self.MAX_TIME

        self.IMAGE_ANIMATIONS = [
                ('conditional', 'effect=slide start=%d,0   end=0,0     center=auto time=%s tween=cubic easing=out delay=0  condition=true' %(sx, t) ),
                ('conditional', 'effect=fade  start=0      end=100                 time=%s tween=cubic easing=out delay=0  condition=true' % t ),
                ('conditional', 'effect=slide start=0,0    end=%d,0    center=auto time=%s tween=cubic easing=in  delay=%s condition=true' %(ex, t, (0.8*t)) ),
                ('conditional', 'effect=fade  start=100    end=0                   time=%s tween=cubic easing=in  delay=%s condition=true' %(t, (0.8*t)) ),
            ]


        #self.image_label.setVisible(False)
        #self.image_label.setLabel('')
        if self.SHOW_TITLE:
            self.txt_background.setVisible(False)
            self.txt_background.setImage('')

        #time = self.MAX_TIME #/ zoom * self.DISTANCE_RATIO * 100   #30000

        # set all parameters and properties

        #labels can have text centered but can't have multiline
        #textbox can have multiline but not centered text... what to do...
        #setLabel(self, label='', font=None, textColor=None, disabledColor=None, shadowColor=None, focusedColor=None, label2=''):

        if self.SHOW_TITLE:

            if self.image_label.getLabel() == desc_and_image[0]:  #avoid animating the same text label if previous one is the same
                self.image_label.setAnimations( [ ('conditional', 'condition=true effect=fade delay=0 time=0 start=100 end=100  ' ) ]  )
            else:
                self.image_label.setAnimations( self.TEXT_ANIMATIONS )

            if desc_and_image[0]:
                self.image_label.setLabel(desc_and_image[0])
                self.image_label.setVisible(True)

                self.txt_background.setImage('srr_dlg-bg.png')
                self.txt_background.setVisible(True)
            else:   #don't show text and text_background if no text
                self.image_label.setVisible(False)
                self.txt_background.setVisible(False)

        image_control.setImage(desc_and_image[1])
        image_control.setPosition(0, 0)
        image_control.setWidth(1280)   #16:9
        #image_control.setWidth(1680)    #21:9
        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)
        # show the image
        image_control.setVisible(True)

class FadeScreensaver( HorizontalSlide2, ScreensaverBase):
    MODE = 'Fade'

    def load_settings(self):
        self.SPEED = float(addon.getSetting('slideshow_speed'))
        self.SHOW_TITLE = addon.getSetting('show_title') == 'true'

        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))
        self.MAX_TIME = int(30000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(6000.0 / self.SPEED)

        self.IMAGE_ANIMATIONS = [
                ('conditional', 'effect=fade start=0 end=100 center=auto time=%s  tween=back  easing=out delay=0  condition=true' % self.NEXT_IMAGE_TIME),
                ('conditional', 'effect=fade start=100 end=0 center=auto time=500 tween=back  easing=in  delay=%s condition=true' %(self.NEXT_IMAGE_TIME+1000) ),
            ]

        self.TEXT_ANIMATIONS= [
                ('conditional', 'condition=true effect=fade delay=0 time=500 start=0 end=100  ' ),
                ('conditional', 'condition=true effect=fade delay=%s time=500 start=100 end=0 tween=circle easing=in' % self.NEXT_IMAGE_TIME  ) ]

    def process_image(self, image_control_id):

        description=self.next_desc_and_image[4]
        if description and self.SHOW_TITLE:
            image_control=self.xbmc_window.getControl(image_control_id)
        else:
            image_control=self.xbmc_window.getControl( image_control_id + 50 )


        image_control.setVisible(False)
        image_control.setImage('')

        image_control.setImage(self.next_desc_and_image[1])
        image_control.setPosition(0, 0)
        image_control.setWidth(1280)   #16:9
        #image_control.setWidth(1680)    #21:9
        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)
        # show the image
        image_control.setVisible(True)

class AdaptiveSlideScreensaver( HorizontalSlideScreensaver, ScreensaverBase):
    MODE = 'SlideUDLR'

    def load_settings(self):
        self.SPEED = float(addon.getSetting('slideshow_speed'))
        self.SHOW_TITLE = addon.getSetting('show_title') == 'true'

        self.CONCURRENCY = 1.0 #float(addon.getSetting('appletvlike_concurrency'))
        self.MAX_TIME = int(36000 / self.SPEED)  #int(15000 / self.SPEED)
        self.NEXT_IMAGE_TIME =  int(12000.0 / self.SPEED)

    def process_image(self, tni_control, desc_and_image):
        image_control=tni_control[1]
        text_control=tni_control[0]

        width =desc_and_image[2] if desc_and_image[2] else 0
        height=desc_and_image[3] if desc_and_image[3] else 0
        if width>0 and height>0:
            ar=float(float(width)/height)
        else:
            ar=1.0

        image_control.setVisible(False)
        image_control.setImage('')
        text_control.setVisible(False)
        text_control.setText('')

        direction=random.choice([1,0])
        if ar < 0.85:
            up_down=True
        else:
            up_down=False

        #log('  %d  %dx%d %f' %(direction, width,height,ar ) )

        #default dimension of the image control
        ctl_width=1680
        ctl_height=720
        ctl_x=0

        if up_down:
            #with tall images, the image control dimension has to be tall
            sx=0;ex=0
            sy=-1680;ey=720
            #prevent some tall images from being zoomed in too much
            if ar > 0.6:
                ctl_width=940
                ctl_x=random.randint(0, 340)

            else:
                ctl_width=1280

            ctl_height=1680
        else:
            sx=1280;ex=-1680
            sy=0;ey=0

        if direction:
            sx,ex=ex,sx
            sy,ey=ey,sy

        slide_animation=[
            ('conditional', 'effect=slide start=%d,%d end=%d,%d center=auto time=%s '
                            'tween=cubic easing=out delay=0 condition=true' % ( sx,sy,ex,ey, self.MAX_TIME)),
        ]

        if self.SHOW_TITLE:
            self.txt_background.setVisible(False)
            self.txt_background.setImage('')

        if self.SHOW_TITLE:
#             if self.info_requested:
#                 self.txt_background.setPosition(0, 498)
#                 self.image_label.setPosition(10, 500)
#                 self.txt_background.setHeight(220)
#                 self.image_label.setHeight(220)
#             else:
#                 self.txt_background.setPosition(0, 685)
#                 self.image_label.setPosition(10, 683)
#                 self.txt_background.setHeight(40)
#                 self.image_label.setHeight(40)

            if self.image_label.getLabel() == desc_and_image[0]:  #avoid animating the same text label if previous one is the same
                self.image_label.setAnimations( [ ('conditional', 'condition=true effect=fade delay=0 time=0 start=100 end=100  ' ) ]  )
            else:
                self.image_label.setAnimations( self.TEXT_ANIMATIONS )

            if desc_and_image[0]:
                self.image_label.setLabel(desc_and_image[0])
                self.image_label.setVisible(True)

                self.txt_background.setImage('srr_dlg-bg.png')
                self.txt_background.setVisible(True)
            else:   #don't show text and text_background if no text
                self.image_label.setVisible(False)
                self.txt_background.setVisible(False)

        image_control.setImage(desc_and_image[1])
        image_control.setPosition(ctl_x, 0)
        image_control.setWidth(ctl_width)
        image_control.setHeight(ctl_height)
        image_control.setAnimations(slide_animation)
        # show the image
        image_control.setVisible(True)

class ExitMonitor(xbmc.Monitor):

    def __init__(self, exit_callback):
        self.exit_callback = exit_callback

    def onScreensaverDeactivated(self):
        self.exit_callback()


MODES = (
    'slideLeft',
    'Fade',
    'SlideUDLR',
    'Random',
)
class ScreensaverManager(object):

    def __new__(cls, ev, q):
        mode = MODES[int(addon.getSetting('slideshow_mode'))]
        if mode == 'Random':
            subcls = random.choice(ScreensaverBase.__subclasses__( ))
            return subcls( ev, q)
        for subcls in ScreensaverBase.__subclasses__():
            #log('  mode:%s subclass:%s' %( mode, subcls.__name__ ))
            if subcls.MODE == mode:
                return subcls( ev, q)

        raise ValueError('Not a valid ScreensaverBase subclass: %s' % mode)


def cycle(iterable):
    saved = []
    for element in iterable:
        yield element
        saved.append(element)
    while saved:
        for element in saved:
            yield element

if __name__ == '__main__':

     pass
#save for later:  https://mblaszczak.artstation.com/