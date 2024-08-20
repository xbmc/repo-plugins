import os
import io
import xbmcvfs
import colorsys
import hashlib
from xbmc import getCacheThumbName, skinHasImage, Monitor, sleep
from tmdbhelper.lib.addon.plugin import get_infolabel, get_setting, get_condvisibility, ADDONDATA
from tmdbhelper.lib.monitor.propertysetter import PropertySetter
from jurialmunkey.parser import try_int, try_float
from tmdbhelper.lib.files.futils import make_path
from threading import Thread
import urllib.request as urllib
from tmdbhelper.lib.addon.logger import kodi_log

CROPIMAGE_SOURCE = "Art(artist.clearlogo)|Art(tvshow.clearlogo)|Art(clearlogo)"

ARTWORK_LOOKUP_TABLE = {
    'poster': ['Art(tvshow.poster)', 'Art(poster)', 'Art(thumb)'],
    'fanart': ['Art(fanart)', 'Art(thumb)'],
    'landscape': ['Art(landscape)', 'Art(fanart)', 'Art(thumb)'],
    'thumb': ['Art(thumb)']}

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


def md5hash(value):
    value = str(value).encode(errors='surrogatepass')  # Use surrogatepass to avoid emoji in filenames raising exceptions for utf-8
    return hashlib.md5(value).hexdigest()


def _imageopen(image):
    global Image
    if Image is None:
        from PIL import Image
    with xbmcvfs.File(image, 'rb') as f:
        image_bytes = f.readBytes()
    return Image.open(io.BytesIO(image_bytes))


def _closeimage(image, targetfile=None):
    image.close()
    if not targetfile:
        return
    xbmcvfs.delete(targetfile)


def _openimage(image, targetpath, filename):
    """ Open image helper with thanks to sualfred """
    # some paths require unquoting to get a valid cached thumb hash
    cached_image_path = urllib.unquote(image.replace('image://', ''))
    if cached_image_path.endswith('/'):
        cached_image_path = cached_image_path[:-1]

    cached_files = []
    for path in [getCacheThumbName(cached_image_path), getCacheThumbName(image)]:
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
                        return (img, None)

                    except Exception as error:
                        kodi_log('Image error: Could not open cached image --> %s' % error, 2)

            ''' Skin images will be tried to be accessed directly. For all other ones
                the source will be copied to the addon_data folder to get access.
            '''
            if skinHasImage(image):
                if not image.startswith('special://skin'):
                    image = os.path.join('special://skin/media/', image)

                try:  # in case image is packed in textures.xbt
                    img = _imageopen(xbmcvfs.translatePath(image))
                    return (img, None)

                except Exception:
                    return ('', None)

            else:
                targetfile = os.path.join(targetpath, f'temp_{filename}')  # Use temp file to avoid Kodi writing early
                if not xbmcvfs.exists(targetfile):
                    xbmcvfs.copy(image, targetfile)

                img = _imageopen(targetfile)
                return (img, targetfile)

        except Exception as error:
            kodi_log('Image error: Could not get image for %s (try %d) -> %s' % (image, i, error), 2)
            sleep(500)
            pass

    return ('', None)


def _saveimage(image, targetfile):
    """ Save image object to disk
    Uses flush() and os.fsync() to ensure file is written to disk before continuing
    Used to prevent Kodi from attempting to cache the image before writing is complete
    """
    with xbmcvfs.File(targetfile, 'wb') as f:
        image.save(f, 'PNG')
        # f.flush()
        # os.fsync(f)


class ImageFunctions(Thread, PropertySetter):
    save_path = f"{get_setting('image_location', 'str') or ADDONDATA}{{}}/"
    blur_size = try_int(get_infolabel('Skin.String(TMDbHelper.Blur.Size)')) or 480
    crop_size = (800, 310)
    radius = try_int(get_infolabel('Skin.String(TMDbHelper.Blur.Radius)')) or 40

    def __init__(self, method=None, artwork=None, is_thread=True, prefix='ListItem'):
        if is_thread:
            Thread.__init__(self)
        self.image = artwork
        self.func = None
        self.save_orig = False
        self.save_prop = None
        if method == 'blur':
            self.func = self.blur
            self.save_path = make_path(self.save_path.format('blur_v2'))
            self.save_prop = f'{prefix}.BlurImage'
            self.save_orig = True
        elif method == 'crop':
            self.func = self.crop
            self.save_path = make_path(self.save_path.format('crop_v2'))
            self.save_prop = f'{prefix}.CropImage'
            self.save_orig = True
        elif method == 'desaturate':
            self.func = self.desaturate
            self.save_path = make_path(self.save_path.format('desaturate_v2'))
            self.save_prop = f'{prefix}.DesaturateImage'
            self.save_orig = True
        elif method == 'colors':
            self.func = self.colors
            self.save_path = make_path(self.save_path.format('colors_v2'))
            self.save_prop = f'{prefix}.Colors'

    def run(self):
        if not self.save_prop or not self.func:
            return
        output = self.func(self.image) if self.image else None
        self.set_properties(output)

    def set_properties(self, output):
        if not output:
            self.get_property(self.save_prop, clear_property=True)
            self.get_property(f'{self.save_prop}.Original', clear_property=True) if self.save_orig else None
            return
        self.get_property(self.save_prop, output)
        self.get_property(f'{self.save_prop}.Original', self.image) if self.save_orig else None

    def clamp(self, x):
        return max(0, min(x, 255))

    @lazyimport_pil
    def crop(self, source):
        if not source:
            return ''
        filename = f'cropped-{md5hash(source)}.png'
        destination = os.path.join(self.save_path, filename)
        try:
            if not xbmcvfs.exists(destination):  # Used to do os.utime(destination, None) on existing here
                img, targetfile = _openimage(source, self.save_path, filename)
                try:
                    # Errors with single channel L conversion to RGBa so catch exceptions
                    img_rgba = img.convert('RGBa')
                    img = img.crop(img_rgba.getbbox())
                except Exception:
                    # If we get a conversion error just try getting bounding box with current channel
                    # We'll probably be okay with single channel texture since Kodi now handles these better
                    img = img.crop(img.getbbox())
                img.thumbnail(self.crop_size)
                _saveimage(img, destination)
                _closeimage(img, targetfile)

            return destination

        except Exception as exc:
            kodi_log(f'Crop Error:\n{source}\n{destination}\n{exc}', 2)
            return ''

    @lazyimport_pil
    def blur(self, source):
        filename = f'{md5hash(source)}-{self.radius}-{self.blur_size}.jpg'
        destination = os.path.join(self.save_path, filename)
        try:
            if not xbmcvfs.exists(destination):  # os.utime(destination, None)
                img, targetfile = _openimage(source, self.save_path, filename)
                img.thumbnail((self.blur_size, self.blur_size))
                img = img.convert('RGB')
                img = img.filter(ImageFilter.GaussianBlur(self.radius))
                _saveimage(img, destination)
                _closeimage(img, targetfile)

            return destination

        except Exception:
            return ''

    @lazyimport_pil
    def desaturate(self, source):
        filename = f'{md5hash(source)}.png'
        destination = os.path.join(self.save_path, filename)
        try:
            if not xbmcvfs.exists(destination):  # os.utime(destination, None)
                img, targetfile = _openimage(source, self.save_path, filename)
                img = img.convert('LA')
                _saveimage(img, destination)
                _closeimage(img, targetfile)

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
        lum = try_float(get_infolabel('Skin.String(TMDbHelper.Colors.Luminance)')) or hls_tuple[1]
        sat = try_float(get_infolabel('Skin.String(TMDbHelper.Colors.Saturation)')) or hls_tuple[2]
        return self.rgb_to_int(*colorsys.hls_to_rgb(hue, lum, sat))

    def rgb_to_int(self, r, g, b):
        return [try_int(self.clamp(i * 255)) for i in [r, g, b]]

    def rgb_to_hex(self, r, g, b):
        return f'FF{r:02x}{g:02x}{b:02x}'

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
            if self.get_property(checkprop) != start_hex:
                return
            hex_value = self.rgb_to_hex(val_r, val_g, val_b)
            self.get_property(propname, set_property=hex_value)
            val_r = val_r + inc_r
            val_g = val_g + inc_g
            val_b = val_b + inc_b
            Monitor().waitForAbort(0.05)

        self.get_property(propname, set_property=end_hex)
        return end_hex

    @lazyimport_pil
    def colors(self, source):
        filename = f'{md5hash(source)}.png'
        destination = self.save_path + filename
        targetfile = None

        try:
            if xbmcvfs.exists(destination):  # os.utime(destination, None)
                img = _imageopen(xbmcvfs.translatePath(destination))
            else:
                img, targetfile = _openimage(source, self.save_path, filename)
                img.thumbnail((128, 128))
                img = img.convert('RGB')
                _saveimage(img, destination)

            maincolor_rgb = self.get_maincolor(img)
            maincolor_hex = self.rgb_to_hex(*self.get_color_lumsat(*maincolor_rgb))
            compcolor_rgb = self.get_compcolor(*maincolor_rgb)
            compcolor_hex = self.rgb_to_hex(*self.get_color_lumsat(*compcolor_rgb))

            maincolor_propname = self.save_prop + '.Main'
            maincolor_propchek = self.save_prop + '.MainCheck'
            maincolor_propvalu = self.get_property(maincolor_propname)
            if not maincolor_propvalu:
                self.get_property(maincolor_propname, set_property=maincolor_hex)
            else:
                self.get_property(maincolor_propchek, set_property=maincolor_propvalu)
                thread_maincolor = Thread(target=self.set_prop_colorgradient, args=[
                    maincolor_propname, maincolor_propvalu, maincolor_hex, maincolor_propchek])
                thread_maincolor.start()

            compcolor_propname = self.save_prop + '.Comp'
            compcolor_propchek = self.save_prop + '.CompCheck'
            compcolor_propvalu = self.get_property(compcolor_propname)
            if not compcolor_propvalu:
                self.get_property(compcolor_propname, set_property=compcolor_hex)
            else:
                self.get_property(compcolor_propchek, set_property=compcolor_propvalu)
                thread_compcolor = Thread(target=self.set_prop_colorgradient, args=[
                    compcolor_propname, compcolor_propvalu, compcolor_hex, compcolor_propchek])
                thread_compcolor.start()

            _closeimage(img, targetfile)
            return maincolor_hex

        except Exception as exc:
            kodi_log(exc, 1)
            return ''


class ImageManipulations(PropertySetter):
    def get_infolabel(self, info):
        return get_infolabel(f'ListItem.{info}')

    def get_builtartwork(self):
        return

    def get_artwork(self, source='', build_fallback=False, built_artwork=None):
        source = source or ''
        source = source.lower()

        def _get_artwork_infolabel(_infolabels):
            for i in _infolabels:
                artwork = self.get_infolabel(i)
                if not artwork:
                    continue
                return artwork

        def _get_artwork_fallback(_infolabels, _built_artwork):
            for i in _infolabels:
                if not i.startswith('art('):
                    continue
                artwork = _built_artwork.get(i[4:-1])
                if not artwork:
                    continue
                return artwork

        def _get_artwork(_source):
            if _source:
                _infolabels = ARTWORK_LOOKUP_TABLE.get(_source, _source.split("|"))
            else:
                _infolabels = ARTWORK_LOOKUP_TABLE.get('thumb')

            artwork = _get_artwork_infolabel(_infolabels)

            if artwork or not build_fallback:
                return artwork

            nonlocal built_artwork

            built_artwork = built_artwork or self.get_builtartwork()
            if not built_artwork:
                return

            return _get_artwork_fallback(_infolabels, built_artwork)

        for _source in source.split("||"):
            artwork = _get_artwork(_source)
            if not artwork:
                continue
            return artwork

    def get_image_manipulations(self, use_winprops=False, built_artwork=None):
        images = {}

        _manipulations = (
            {'method': 'crop',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableCrop)"),
                'images': lambda: self.get_artwork(
                    source=CROPIMAGE_SOURCE,
                    build_fallback=True,
                    built_artwork=built_artwork)},
            {'method': 'blur',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableBlur)"),
                'images': lambda: self.get_artwork(
                    source=self.get_property('Blur.SourceImage'),
                    build_fallback=True,
                    built_artwork=built_artwork)
                or self.get_property('Blur.Fallback')},
            {'method': 'desaturate',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableDesaturate)"),
                'images': lambda: self.get_artwork(
                    source=self.get_property('Desaturate.SourceImage'),
                    build_fallback=True,
                    built_artwork=built_artwork)
                or self.get_property('Desaturate.Fallback')},
            {'method': 'colors',
                'active': lambda: get_condvisibility("Skin.HasSetting(TMDbHelper.EnableColors)"),
                'images': lambda: self.get_artwork(
                    source=self.get_property('Colors.SourceImage'),
                    build_fallback=True,
                    built_artwork=built_artwork)
                or self.get_property('Colors.Fallback')},)

        for i in _manipulations:
            if not i['active']():
                continue
            imgfunc = ImageFunctions(method=i['method'], is_thread=False, artwork=i['images']())

            output = imgfunc.func(imgfunc.image)
            images[f'{i["method"]}image'] = output
            images[f'{i["method"]}image.original'] = imgfunc.image

            if use_winprops:
                imgfunc.set_properties(output)

        return images
