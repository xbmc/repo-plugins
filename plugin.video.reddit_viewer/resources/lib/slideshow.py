import xbmc
import json
import xbmcvfs
import random
import sys

from xbmcgui import ControlImage, WindowDialog, WindowXMLDialog, Window, ControlTextBox, ControlLabel


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


    nl = remove_dict_duplicates( dictlist, 'DirectoryItem_url')



    for e in nl:
        q.put(e)

    ev=threading.Event()

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

    preview_w=0
    preview_h=0
    image=''

    content = reddit_request(url)
    if not content: return

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

            try:    post_selftext=unescape(j_entry['data']['selftext'].encode('utf-8'))
            except: post_selftext=''


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

                preview=""


            ld=parse_reddit_link(link_url=media_url, assume_is_video=False, needs_preview=True, get_playable_url=True )
            if ld:
                if not preview:
                    preview = ld.poster

                if (addon.getSetting('include_albums')=='true') and (ld.media_type==sitesBase.TYPE_ALBUM) :
                    dictlist = listAlbum( media_url, title, 'return_dictlist')
                    for d in dictlist:

                        t2=d.get('li_label') if d.get('li_label') else title


                        d['li_label']=t2
                        entries.append( d )

                else:
                    if addon.getSetting('use_reddit_preview')=='true':
                        if preview: image=preview
                        elif ld.poster: image=ld.poster

                    else:
                        if ld.poster:  image=ld.poster #entries.append([title,ld.poster,preview_w, preview_h,len(entries)])
                        elif preview: image=preview  #entries.append([title,preview,preview_w, preview_h,len(entries)])


                    append_entry( entries, title,image,preview_w, preview_h, description )
            else:
                append_entry( entries, title,preview,preview_w, preview_h, description )


        except Exception as e:
            log( '  autoPlay exception:' + str(e) )


    entries = remove_dict_duplicates( entries, 'DirectoryItem_url')


    for i, e in enumerate(entries):
        log('  possible playable items({0}) {1}...{2}x{3}  {4}'.format( i, e['li_label'].ljust(15)[:15], repr(e.get('width')),repr(e.get('height')),  e.get('DirectoryItem_url')) )

    if len(entries)==0:
        log('  Play All: no playable items' )
        xbmc.executebuiltin('XBMC.Notification("%s","%s")' %(translation(32054), translation(32055)  ) )  #Play All     No playable items
        return


    log("**********playing slideshow*************")

    for e in entries:
        q.put(e)

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

CHUNK_WAIT_TIME = 250
ACTION_IDS_EXIT = [9, 10, 13, 92]
ACTION_IDS_PAUSE = [12,68,79,229]   #ACTION_PAUSE = 12  ACTION_PLAY = 68  ACTION_PLAYER_PLAY = 79   ACTION_PLAYER_PLAYPAUSE = 229


class ScreensaverWindow(WindowDialog):
    def __init__(self, exit_callback):
        self.exit_callback = exit_callback


    def onAction(self, action):
        action_id = action.getId()
        if action_id in ACTION_IDS_EXIT:
            self.exit_callback()

class ScreensaverXMLWindow(WindowXMLDialog):


    def __init__(self, *args, **kwargs):
        WindowXMLDialog.__init__(self, *args, **kwargs)

        self.exit_callback = kwargs.get("exit_callback")


    def onAction(self, action):
        action_id = action.getId()
        self.exit_callback(action_id) #pass the action id to the calling class

class ScreensaverBase(object):

    MODE = None
    IMAGE_CONTROL_COUNT = 10
    FAST_IMAGE_COUNT = 0
    NEXT_IMAGE_TIME = 2000
    BACKGROUND_IMAGE = 'srr_blackbg.jpg'

    pause_requested=False
    info_requested=False

    def __init__(self, thread_event, image_queue):

        self.exit_requested = False
        self.toggle_info_display_requested=False
        self.background_control = None
        self.preload_control = None
        self.image_count = 0

        self.tni_controls = []
        self.global_controls = []
        self.exit_monitor = ExitMonitor(self.stop)

        self.init_xbmc_window()


        self.init_global_controls()
        self.load_settings()
        self.init_cycle_controls()
        self.stack_cycle_controls()


    def init_xbmc_window(self):
        self.xbmc_window = ScreensaverXMLWindow( "slideshow02.xml", addon_path, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.show()


    def init_global_controls(self):


        loading_img = xbmc.validatePath('/'.join((ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'srr_busy.gif' )))

        self.loading_control = ControlImage(576, 296, 128, 128, loading_img)
        self.preload_control = ControlImage(-1, -1, 1, 1, '')
        self.background_control = ControlImage(0, 0, 1280, 720, '')
        self.global_controls = [
            self.preload_control, self.background_control, self.loading_control
        ]
        self.xbmc_window.addControls(self.global_controls)


    def load_settings(self):
        pass

    def init_cycle_controls(self):

        for _ in xrange(self.IMAGE_CONTROL_COUNT):
            img_control = ControlImage(0, 0, 0, 0, '', aspectRatio=2)  #(values 0 = stretch (default), 1 = scale up (crops), 2 = scale down (black bars)
            txt_control = ControlTextBox(0, 0, 0, 0, font='font16')

            self.tni_controls.append([txt_control,img_control])


    def stack_cycle_controls(self):


        self.xbmc_window.addControls(self.tni_controls[1])
        self.xbmc_window.addControls(self.tni_controls[0])


    def start_loop(self):
        self.log('start_loop start')

        desc_and_images = self.get_description_and_images('q')

        if random_image_order:    #addon.getSetting('random_image_order') == 'true':
            random.shuffle(desc_and_images)
        desc_and_images_cycle=cycle(desc_and_images)

        tni_controls_cycle= cycle(self.tni_controls)



        self.hide_loading_indicator()

        desc_and_image=desc_and_images_cycle.next()


        while not self.exit_requested:
            self.log('  using image: %s ' % ( repr(desc_and_image ) ) )


            if not self.pause_requested:

                tni_control = tni_controls_cycle.next()

                self.process_image(tni_control, desc_and_image)

                desc_and_image=desc_and_images_cycle.next()

            if self.image_count < self.FAST_IMAGE_COUNT:
                self.image_count += 1
            else:

                self.preload_image(desc_and_image[1])
                self.wait()

        self.log('start_loop end')



    def get_description_and_images(self, source):

        self.image_aspect_ratio = 16.0 / 9.0

        images = []

        if source == 'image_folder':

            path = '' #SlideshowCacheFolder  #addon.getSetting('image_path')
            if path:
                images = self._get_folder_images(path)
        elif source == 'q':

            images=[  [i.get('li_label'), i.get('DirectoryItem_url'),i.get('width'), i.get('height'), i.get('description') ] for i in q.queue]

            log( "queue size:%d" %q.qsize() )


        return images


    def _get_folder_images(self, path):
        self.log('_get_folder_images started with path: %s' % repr(path))
        _, files = xbmcvfs.listdir(path)
        images = [
            xbmc.validatePath(path + f) for f in files
            if f.lower()[-3:] in ('jpg', 'png')
        ]

        self.log('_get_folder_images ends')
        return images

    def hide_loading_indicator(self):
        bg_img = xbmc.validatePath('/'.join(( ADDON_PATH, 'resources', 'skins', 'Default', 'media', self.BACKGROUND_IMAGE )))

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

        raise NotImplementedError

    def preload_image(self, image_url):

        self.preload_control.setImage(image_url)


    def wait(self):

        chunk_wait_time = int(CHUNK_WAIT_TIME)
        remaining_wait_time = int(self.NEXT_IMAGE_TIME)
        while remaining_wait_time > 0:
            if self.exit_requested:
                self.log('wait aborted')
                return
            if self.toggle_info_display_requested:  #this value is set on specific keypress in action_id_handler

                self.toggle_info_display_requested=False
                self.toggle_info_display_handler()
            if remaining_wait_time < chunk_wait_time:
                chunk_wait_time = remaining_wait_time
            remaining_wait_time -= chunk_wait_time
            xbmc.sleep(chunk_wait_time)

    def action_id_handler(self,action_id):

        if action_id in ACTION_IDS_EXIT:

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

        pass

    def close(self):
        self.del_controls()

    def del_controls(self):

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

    image_control_ids=[101,102,103,104,105]   #control id's defined in ScreensaverXMLWindow xml file

    def init_xbmc_window(self):

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

        self.next_desc_and_image=desc_and_images_cycle.next()



        while not self.exit_requested:
            self.log('  using image: %s ' % ( repr(self.next_desc_and_image ) ) )


            image_control_id = image_controls_cycle.next()

            self.toggle_info_display()

            self.process_image(image_control_id)

            self.current_desc_and_image=self.next_desc_and_image

            self.next_desc_and_image=desc_and_images_cycle.next()

            if self.image_count < self.FAST_IMAGE_COUNT:
                self.image_count += 1
            else:

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

            self.title_control.setText(title)

            self.txt_group_control.setAnimations( self.TEXT_ANIMATIONS )

            self.desc_control.setText(description.replace('\n\n','\n'))
            self.txt_group_control.setVisible(True)
        else:
            self.txt_group_control.setVisible(False)

    def process_image(self, image_control_id):


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

        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)

        image_control.setVisible(True)



class HorizontalSlideScreensaver(ScreensaverBase):

    MODE = 'slideLeftx'
    BACKGROUND_IMAGE = 'srr_blackbg.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 0
    DISTANCE_RATIO = 0.7
    SPEED = 1.0
    CONCURRENCY = 1.0

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

    def init_xbmc_window(self):

        self.xbmc_window = ScreensaverXMLWindow( "slideshow01.xml", addon_path, defaultSkin='Default', exit_callback=self.action_id_handler )
        self.xbmc_window.setCoordinateResolution(5)
        self.xbmc_window.show()


    def stack_cycle_controls(self):

        for txt_ctl, img_ctl in self.tni_controls:
            self.xbmc_window.addControl(img_ctl)

        if self.SHOW_TITLE:
            self.txt_background=ControlImage(0, 685, 1280, 40, 'srr_dialog-bg.png', aspectRatio=1)
            self.xbmc_window.addControl( self.txt_background  )

            self.image_label=ControlLabel(10,688,1280,30,'',font='font16', textColor='', disabledColor='', alignment=6, hasPath=False, angle=0)
            self.xbmc_window.addControl( self.image_label  )


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

        if self.SHOW_TITLE:
            self.txt_background.setVisible(False)
            self.txt_background.setImage('')


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

        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)

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

        image_control.setHeight(720)
        image_control.setAnimations(self.IMAGE_ANIMATIONS)

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

        ctl_width=1680
        ctl_height=720
        ctl_x=0

        if up_down:

            sx=0;ex=0
            sy=-1680;ey=720

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
