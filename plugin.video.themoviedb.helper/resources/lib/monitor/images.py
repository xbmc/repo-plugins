import os
import xbmc
import xbmcvfs
import colorsys
from resources.lib.addon.window import get_property
from resources.lib.addon.plugin import kodi_log, md5hash
from resources.lib.addon.parser import try_int, try_float
from resources.lib.files.utils import make_path
from threading import Thread
import urllib.request as urllib

# PIL causes issues (via numpy) on Linux systems using python versions higher than 3.8.5
# Lazy import PIL to avoid using it unless user requires ImageFunctions
ImageFilter, Image = None, None


def lazyimport_pil(func):
    def wrapper(*args, **kwargs):
        global ImageFilter
        if ImageFilter is None:
            from PIL import ImageFilter
        return func(*args, **kwargs)
    return wrapper


def _imageopen(image):
    global Image
    if Image is None:
        from PIL import Image
    return Image.open(image)


def _openimage(image, targetpath, filename):
    """ Open image helper with thanks to sualfred """
    # some paths require unquoting to get a valid cached thumb hash
    cached_image_path = urllib.unquote(image.replace('image://', ''))
    if cached_image_path.endswith('/'):
        cached_image_path = cached_image_path[:-1]

    cached_files = []
    for path in [xbmc.getCacheThumbName(cached_image_path), xbmc.getCacheThumbName(image)]:
        cached_files.append(os.path.join('special://profile/Thumbnails/', path[0], path[:-4] + '.jpg'))
        cached_files.append(os.path.join('special://profile/Thumbnails/', path[0], path[:-4] + '.png'))
        cached_files.append(os.path.join('special://profile/Thumbnails/Video/', path[0], path))

    for i in range(1, 4):
        try:
            ''' Try to get cached image at first
            '''
            for cache in cached_files:
                if xbmcvfs.exists(cache):
                    try:
                        img = _imageopen(xbmcvfs.translatePath(cache))
                        return img

                    except Exception as error:
                        kodi_log('Image error: Could not open cached image --> %s' % error, 2)

            ''' Skin images will be tried to be accessed directly. For all other ones
                the source will be copied to the addon_data folder to get access.
            '''
            if xbmc.skinHasImage(image):
                if not image.startswith('special://skin'):
                    image = os.path.join('special://skin/media/', image)

                try:  # in case image is packed in textures.xbt
                    img = _imageopen(xbmcvfs.translatePath(image))
                    return img

                except Exception:
                    return ''

            else:
                targetfile = os.path.join(targetpath, filename)
                if not xbmcvfs.exists(targetfile):
                    xbmcvfs.copy(image, targetfile)

                img = _imageopen(targetfile)
                return img

        except Exception as error:
            kodi_log('Image error: Could not get image for %s (try %d) -> %s' % (image, i, error), 2)
            xbmc.sleep(500)
            pass

    return ''


class ImageFunctions(Thread):
    def __init__(self, method=None, artwork=None):
        Thread.__init__(self)
        self.image = artwork
        self.func = None
        self.save_prop = None
        self.save_path = 'special://profile/addon_data/plugin.video.themoviedb.helper/{}/'
        if method == 'blur':
            self.func = self.blur
            self.save_path = make_path(self.save_path.format('blur'))
            self.save_prop = 'ListItem.BlurImage'
        elif method == 'crop':
            self.func = self.crop
            self.save_path = make_path(self.save_path.format('crop'))
            self.save_prop = 'ListItem.CropImage'
        elif method == 'desaturate':
            self.func = self.desaturate
            self.save_path = make_path(self.save_path.format('desaturate'))
            self.save_prop = 'ListItem.DesaturateImage'
        elif method == 'colors':
            self.func = self.colors
            self.save_path = make_path(self.save_path.format('colors'))
            self.save_prop = 'ListItem.Colors'

    def run(self):
        if not self.save_prop or not self.func:
            return
        if not self.image:
            get_property(self.save_prop, clear_property=True)
            return
        get_property(self.save_prop, self.func(self.image))

    def clamp(self, x):
        return max(0, min(x, 255))

    def crop(self, source):
        filename = u'cropped-{}.png'.format(md5hash(source))
        destination = self.save_path + filename
        try:
            if xbmcvfs.exists(destination):
                os.utime(destination, None)
            else:
                img = _openimage(source, self.save_path, filename)
                img = img.crop(img.convert('RGBa').getbbox())
                img.save(destination)
                img.close()

            return destination

        except Exception:
            return ''

    @lazyimport_pil
    def blur(self, source, radius=20):
        filename = u'{}{}.png'.format(md5hash(source), radius)
        destination = self.save_path + filename
        try:
            if xbmcvfs.exists(destination):
                os.utime(destination, None)
            else:
                img = _openimage(source, self.save_path, filename)
                img.thumbnail((256, 256))
                img = img.convert('RGB')
                img = img.filter(ImageFilter.GaussianBlur(radius))
                img.save(destination)
                img.close()

            return destination

        except Exception:
            return ''

    def desaturate(self, source):
        filename = u'{}.png'.format(md5hash(source))
        destination = self.save_path + filename
        try:
            if xbmcvfs.exists(destination):
                os.utime(destination, None)
            else:
                img = _openimage(source, self.save_path, filename)
                img = img.convert('LA')
                img.save(destination)
                img.close()

            return destination

        except Exception:
            return ''

    def get_maincolor(self, img):
        """Returns main color of image as list of rgb values 0:255"""
        rgb_list = [None, None, None]
        for channel in range(3):
            pixels = img.getdata(band=channel)
            values = [pixel for pixel in pixels]
            rgb_list[channel] = self.clamp(sum(values) / len(values))
        return rgb_list

    def get_compcolor(self, r, g, b, shift=0.33):
        """
        Changes hue of color by shift value (percentage float)
        Takes RGB as 0:255 values and returns RGB as 0:255 values
        """
        hls_tuple = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        rgb_tuple = colorsys.hls_to_rgb(abs(hls_tuple[0] - shift), hls_tuple[1], hls_tuple[2])
        return self.rgb_to_int(*rgb_tuple)

    def get_color_lumsat(self, r, g, b):
        hls_tuple = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        hue = hls_tuple[0]
        lum = try_float(xbmc.getInfoLabel('Skin.String(TMDbHelper.Colors.Luminance)')) or hls_tuple[1]
        sat = try_float(xbmc.getInfoLabel('Skin.String(TMDbHelper.Colors.Saturation)')) or hls_tuple[2]
        return self.rgb_to_int(*colorsys.hls_to_rgb(hue, lum, sat))

    def rgb_to_int(self, r, g, b):
        return [try_int(self.clamp(i * 255)) for i in [r, g, b]]

    def rgb_to_hex(self, r, g, b):
        return u'FF{:02x}{:02x}{:02x}'.format(r, g, b)

    def hex_to_rgb(self, colorhex):
        r = try_int(colorhex[2:4], 16)
        g = try_int(colorhex[4:6], 16)
        b = try_int(colorhex[6:8], 16)
        return [r, g, b]

    def set_prop_colorgradient(self, propname, start_hex, end_hex, checkprop):
        if not start_hex or not end_hex:
            return

        steps = 20

        rgb_a = self.hex_to_rgb(start_hex)
        rgb_z = self.hex_to_rgb(end_hex)

        inc_r = (rgb_z[0] - rgb_a[0]) // steps
        inc_g = (rgb_z[1] - rgb_a[1]) // steps
        inc_b = (rgb_z[2] - rgb_a[2]) // steps

        val_r = rgb_a[0]
        val_g = rgb_a[1]
        val_b = rgb_a[2]

        for i in range(steps):
            if get_property(checkprop) != start_hex:
                return
            hex_value = self.rgb_to_hex(val_r, val_g, val_b)
            get_property(propname, set_property=hex_value)
            val_r = val_r + inc_r
            val_g = val_g + inc_g
            val_b = val_b + inc_b
            xbmc.Monitor().waitForAbort(0.05)

        get_property(propname, set_property=end_hex)
        return end_hex

    @lazyimport_pil
    def colors(self, source):
        filename = u'{}.png'.format(md5hash(source))
        destination = self.save_path + filename

        try:
            if xbmcvfs.exists(destination):
                os.utime(destination, None)
                img = _imageopen(xbmcvfs.translatePath(destination))
            else:
                img = _openimage(source, self.save_path, filename)
                img.thumbnail((256, 256))
                img = img.convert('RGB')
                img.save(destination)

            maincolor_rgb = self.get_maincolor(img)
            maincolor_hex = self.rgb_to_hex(*self.get_color_lumsat(*maincolor_rgb))
            compcolor_rgb = self.get_compcolor(*maincolor_rgb)
            compcolor_hex = self.rgb_to_hex(*self.get_color_lumsat(*compcolor_rgb))

            maincolor_propname = self.save_prop + '.Main'
            maincolor_propchek = self.save_prop + '.MainCheck'
            maincolor_propvalu = get_property(maincolor_propname)
            if not maincolor_propvalu:
                get_property(maincolor_propname, set_property=maincolor_hex)
            else:
                get_property(maincolor_propchek, set_property=maincolor_propvalu)
                thread_maincolor = Thread(target=self.set_prop_colorgradient, args=[
                    maincolor_propname, maincolor_propvalu, maincolor_hex, maincolor_propchek])
                thread_maincolor.start()

            compcolor_propname = self.save_prop + '.Comp'
            compcolor_propchek = self.save_prop + '.CompCheck'
            compcolor_propvalu = get_property(compcolor_propname)
            if not compcolor_propvalu:
                get_property(compcolor_propname, set_property=compcolor_hex)
            else:
                get_property(compcolor_propchek, set_property=compcolor_propvalu)
                thread_compcolor = Thread(target=self.set_prop_colorgradient, args=[
                    compcolor_propname, compcolor_propvalu, compcolor_hex, compcolor_propchek])
                thread_compcolor.start()

            img.close()
            return maincolor_hex

        except Exception as exc:
            kodi_log(exc, 1)
            return ''
