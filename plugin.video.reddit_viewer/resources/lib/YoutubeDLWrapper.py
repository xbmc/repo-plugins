# -*- coding: utf-8 -*-
#################################################################################
#
#   This file is part of the awesome youtube-dl addon by ruuk
#
#################################################################################
import sys
import time
import datetime
import xbmc
#from yd_private_libs import util, updater
#import YDStreamUtils as StreamUtils

#updater.updateCore()

#updater.set_youtube_dl_importPath()


from youtube_dl.utils import std_headers#, DownloadError  # noqa E402

#DownloadError  # Hides IDE warnings


###############################################################################
# FIX: xbmcout instance in sys.stderr does not have isatty(), so we add it
###############################################################################
class replacement_stderr(sys.stderr.__class__):
    def isatty(self): return False

#sys.stderr.__class__ = replacement_stderr
###############################################################################

try:
    import youtube_dl
except:
    #util.ERROR('Failed to import youtube-dl')
    youtube_dl = None

coreVersion = youtube_dl.version.__version__
#updater.saveVersion(coreVersion)
#util.LOG('youtube_dl core version: {0}'.format(coreVersion))

###############################################################################
# FIXES: datetime.datetime.strptime evaluating as None?
###############################################################################
try:
    datetime.datetime.strptime('0', '%H')
except TypeError:
    # Fix for datetime issues with XBMC/Kodi
    class new_datetime(datetime.datetime):
        @classmethod
        def strptime(cls, dstring, dformat):
            return datetime.datetime(*(time.strptime(dstring, dformat)[0:6]))

    datetime.datetime = new_datetime

###############################################################################

_YTDL = None
_DISABLE_DASH_VIDEO = True #util.getSetting('disable_dash_video', True)
#_CALLBACK = None
# BLACKLIST = ['youtube:playlist', 'youtube:toplist', 'youtube:channel', 'youtube:user', 'youtube:search', 'youtube:show', 'youtube:favorites', 'youtube:truncated_url','vimeo:channel', 'vimeo:user', 'vimeo:album', 'vimeo:group', 'vimeo:review','dailymotion:playlist', 'dailymotion:user','generic'] # noqa E501
_BLACKLIST = []
_OVERRIDE_PARAMS = {}
_DOWNLOAD_CANCEL = False
_DOWNLOAD_START = None
_DOWNLOAD_DURATION = None


class VideoInfo:
    """
    Represents resolved site video
    Has the properties title, description, thumbnail and webpage
    The info property contains the original youtube-dl info
    """

    def __init__(self, ID=None):
        self.ID = ID
        self.title = ''
        self.description = ''
        self.thumbnail = ''
        self.webpage = ''
        self._streams = None
        self.sourceName = ''
        self.info = None
        self._selection = None
        self.downloadID = str(time.time())

    def __len__(self):
        return len(self._streams)

    def streamURL(self):
        """
        Returns the resolved xbmc ready url of the selected stream
        """
        return self.selectedStream()['xbmc_url']

    def streams(self):
        """
        Returns a list of dicts of stream data:
            {'xbmc_url':<xbmc ready resolved stream url>,
            'url':<base resolved stream url>,
            'title':<stream specific title>,
            'thumbnail':<stream specific thumbnail>,
            'formatID':<chosen format id>}
        """
        return self._streams

    def hasMultipleStreams(self):
        """
        Return True if there is more than one stream
        """
        if not self._streams:
            return False
        if len(self._streams) > 1:
            return True
        return False

    def selectStream(self, idx):
        """
        Select the default stream by index or by passing the stream dict
        """
        if isinstance(idx, dict):
            self._selection = idx['idx']
        else:
            self._selection = idx

    def selectedStream(self):
        """
        Returns the info of the currently selected stream
        """
        if self._selection is None:
            return self._streams[0]
        return self._streams[self._selection]


class DownloadCanceledException(Exception):
    pass


class CallbackMessage(str):
    """
    A callback message. Subclass of string so can be displayed/printed as is.
    Has the following extra properties:
        percent        <- Integer download progress or 0 if not available
        etaStr        <- ETA string ex: 3m 25s
        speedStr    <- Speed string ex: 35 KBs
        info        <- dict of the youtube-dl progress info
    """

    def __new__(self, value, pct=0, eta_str='', speed_str='', info=None):
        return str.__new__(self, value)

    def __init__(self, value, pct=0, eta_str='', speed_str='', info=None):
        self.percent = pct
        self.etaStr = eta_str
        self.speedStr = speed_str
        self.info = info


class YoutubeDLWrapper(youtube_dl.YoutubeDL):
    """
    A wrapper for youtube_dl.YoutubeDL providing message handling and
    progress callback.
    It also overrides XBMC environment error causing methods.
    """

    def __init__(self, *args, **kwargs):
        self._lastDownloadedFilePath = ''
        self._overrideParams = {}

        youtube_dl.YoutubeDL.__init__(self, *args, **kwargs)

    def showMessage(self, msg):
        #global _CALLBACK
        #if _CALLBACK:
        #    try:
        #        return _CALLBACK(msg)
        #    except:
                #util.ERROR('Error in callback. Removing.')
        #        _CALLBACK = None
        #else:
        #    if xbmc.abortRequested:
        #        raise Exception('abortRequested')
            # print msg.encode('ascii','replace')
        return True

    def progressCallback(self, info):
        global _DOWNLOAD_CANCEL
        if xbmc.abortRequested or _DOWNLOAD_CANCEL:
            _DOWNLOAD_CANCEL = False
            raise DownloadCanceledException('abortRequested')
        if _DOWNLOAD_DURATION:
            if time.time() - _DOWNLOAD_START > _DOWNLOAD_DURATION:
                raise DownloadCanceledException('duration_reached')
        #if not _CALLBACK:
        #    return
        # 'downloaded_bytes': byte_counter,
        # 'total_bytes': data_len,
        # 'tmpfilename': tmpfilename,
        # 'filename': filename,
        # 'status': 'downloading',
        # 'eta': eta,
        # 'speed': speed
        sofar = info.get('downloaded_bytes')
        total = info.get('total_bytes')
        if info.get('filename'):
            self._lastDownloadedFilePath = info.get('filename')
        pct = ''
        pct_val = 0
        eta = None
        if sofar is not None and total:
            pct_val = int((float(sofar) / total) * 100)
            pct = ' (%s%%)' % pct_val
        elif _DOWNLOAD_DURATION:
            sofar = time.time() - _DOWNLOAD_START
            eta = _DOWNLOAD_DURATION - sofar
            pct_val = int((float(sofar) / _DOWNLOAD_DURATION) * 100)
        eta = eta or info.get('eta') or ''
        eta_str = ''
        if eta:
            eta_str = durationToShortText(eta)
            eta = '  ETA: ' + eta_str
        speed = info.get('speed') or ''
        speed_str = ''
        if speed:
            speed_str = simpleSize(speed) + 's'
            speed = '  ' + speed_str
        status = '%s%s:' % (info.get('status', '?').title(), pct)
        text = CallbackMessage(status + eta + speed, pct_val, eta_str, speed_str, info)
        ok = self.showMessage(text)
        if not ok:
            #util.LOG('Download canceled')
            raise DownloadCanceledException()

    def clearDownloadParams(self):
        self.params['quiet'] = False
        self.params['format'] = None
        self.params['matchtitle'] = None
        self.params.update(_OVERRIDE_PARAMS)

    def clear_progress_hooks(self):
        self._progress_hooks = []

    def add_info_extractor(self, ie):
        if ie.IE_NAME in _BLACKLIST:
            return
        # Fix ##################################################################
#        module = sys.modules.get(ie.__module__)
#        if module:
#            if hasattr(module, 'unified_strdate'):
#                module.unified_strdate = _unified_strdate_wrap
#            if hasattr(module, 'date_from_str'):
#                module.date_from_str = _date_from_str_wrap
        ########################################################################
        youtube_dl.YoutubeDL.add_info_extractor(self, ie)

    def to_stdout(self, message, skip_eol=False, check_quiet=False):
        """Print message to stdout if not in quiet mode."""
        if self.params.get('logger'):
            self.params['logger'].debug(message)
        elif not check_quiet or not self.params.get('quiet', False):
            message = self._bidi_workaround(message)
            terminator = ['\n', ''][skip_eol]
            output = message + terminator
            self.showMessage(output)

    def to_stderr(self, message):
        """Print message to stderr."""
        assert isinstance(message, basestring)
        if self.params.get('logger'):
            self.params['logger'].error(message)
        else:
            message = self._bidi_workaround(message)
            output = message + '\n'
            self.showMessage(output)

    def report_warning(self, message):
        # overidden to get around error on missing stderr.isatty attribute
        _msg_header = 'WARNING:'
        warning_message = '%s %s' % (_msg_header, message)
        self.to_stderr(warning_message)

    def report_error(self, message, tb=None):
        # overidden to get around error on missing stderr.isatty attribute
        _msg_header = 'ERROR:'
        error_message = '%s %s' % (_msg_header, message)
        self.trouble(error_message, tb)


def _getYTDL():
    global _YTDL
    if _YTDL:
        return _YTDL
    #if util.DEBUG and util.getSetting('ytdl_debug', False):
    #    _YTDL = YoutubeDLWrapper({'verbose': True})
    #else:

    _YTDL = YoutubeDLWrapper({'verbose': True})

    _YTDL.add_progress_hook(_YTDL.progressCallback)
    _YTDL.add_default_info_extractors()
    return _YTDL


def download(info):
    from youtube_dl import downloader
    ytdl = _getYTDL()
    name = ytdl.prepare_filename(info)
    if 'http_headers' not in info:
        info['http_headers'] = std_headers
    fd = downloader.get_suitable_downloader(info)(ytdl, ytdl.params)
    for ph in ytdl._progress_hooks:
        fd.add_progress_hook(ph)
    return fd.download(name, info)

def simpleSize(size):
    """
    Converts bytes to a short user friendly string
    Example: 12345 -> 12.06 KB
    """
    s = 0
    if size > 0:
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
    if (s > 0):
        return '%s %s' % (s, SIZE_NAMES[i])
    else:
        return '0B'


def durationToShortText(seconds):
    """
    Converts seconds to a short user friendly string
    Example: 143 -> 2m 23s
    """
    days = int(seconds / 86400)
    if days:
        return '%sd' % days
    left = seconds % 86400
    hours = int(left / 3600)
    if hours:
        return '%sh' % hours
    left = left % 3600
    mins = int(left / 60)
    if mins:
        return '%sm' % mins
    sec = int(left % 60)
    if sec:
        return '%ss' % sec
    return '0s'

def _getQualityLimits(quality):
    minHeight = 0
    maxHeight = 480
    if quality > 2:
        minHeight = 1081
        maxHeight = 999999
    elif quality > 1:
        minHeight = 721
        maxHeight = 1080
    elif quality > 0:
        minHeight = 481
        maxHeight = 720
    return minHeight, maxHeight

from utils import log
import pprint

def _selectVideoQuality(r, quality=1, disable_dash=True):
        import urllib
        import difflib
        #if quality is None:
        #    quality = util.getSetting('video_quality', 1)
        #disable_dash = util.getSetting('disable_dash_video', True)

        entries = r.get('entries') or [r]

        minHeight, maxHeight = _getQualityLimits(quality)

        #util.LOG('Quality: {0}'.format(quality), debug=True)
        urls = []
        idx = 0
        for entry in entries:
            defFormat = None
            defMax = 0
            defPref = -1000
            prefFormat = None
            prefMax = 0
            prefPref = -1000

            index = {}
            formats = entry.get('formats') or [entry]

            for i in range(len(formats)):
                index[formats[i]['format_id']] = i

            keys = sorted(index.keys())

            fallback = formats[index[keys[0]]]
            fallback_format_id=fallback.get('format_id','')
            fallback_protocol=fallback.get('protocol','')

            #log( repr(keys) )
            #log( "fallback format:"+repr(fallback_format_id) )
            #log( "fallback_protocol:"+repr(fallback_protocol) )

            #kodi can't play this protocol   from:https://www.zdf.de/familienfieber-100.html
            banned_protocols=['f4m']
            #no sound if this codec
            banned_acodec=['none']

            if fallback_protocol in banned_protocols:
                alternate_formats=difflib.get_close_matches(fallback_format_id, keys)

                for a in alternate_formats:
                    #log( "alternate_format:"+repr(a) )
                    #log( "        protocol:"+repr(formats[index[a]].get('protocol','')) )
                    alt_protocol=formats[index[a]].get('protocol','')
                    if alt_protocol not in banned_protocols:
                        fallback = formats[index[a]]
                        #log('picked alt format:' + a )
                        break

            for fmt in keys:
                fdata = formats[index[fmt]]
                #log( 'Available format:\n' + pprint.pformat(fdata, indent=1, depth=1) )
                if 'height' not in fdata:
                    continue
                if disable_dash and 'dash' in fdata.get('format_note', '').lower():
                    continue
                if 'protocol' in fdata and fdata.get('protocol') in banned_protocols:
                    #log('skipped format:' + pprint.pformat(fdata, indent=1, depth=1))
                    continue
                if 'acodec' in fdata and fdata.get('acodec') in banned_acodec:
                    #log('skipped format:' + pprint.pformat(fdata, indent=1, depth=1))
                    continue

                h = fdata['height']
                p = fdata.get('preference', 1)
                if h >= minHeight and h <= maxHeight:
                    if (h >= prefMax and p > prefPref) or (h > prefMax and p >= prefPref):
                        prefMax = h
                        prefPref = p
                        prefFormat = fdata
                elif(h >= defMax and h <= maxHeight and p > defPref) or (h > defMax and h <= maxHeight and p >= defPref):
                        defMax = h
                        defFormat = fdata
                        defPref = p
            formatID = None
            if prefFormat:
                info = prefFormat
                logBase = '[{3}] Using Preferred Format: {0} ({1}x{2})'
            elif defFormat:
                info = defFormat
                logBase = '[{3}] Using Default Format: {0} ({1}x{2})'
            else:
                info = fallback
                logBase = '[{3}] Using Fallback Format: {0} ({1}x{2})'

            url = info['url']
            formatID = info['format_id']
            format_desc=info['format']
            #log(logBase.format(format_desc, info.get('width', '?'), info.get('height', '?'), entry.get('title', '').encode('ascii', 'replace')))
            #log( 'Selected format:\n' + pprint.pformat(info, indent=1, depth=1) )
            #log('********************************************************************************************')
            if url.find("rtmp") == -1:
                url += '|' + urllib.urlencode({'User-Agent': entry.get('user_agent') or std_headers['User-Agent']})
            else:
                url += ' playpath='+fdata['play_path']
            new_info = dict(entry)
            new_info.update(info)
            urls.append(
                {
                    'xbmc_url': url,
                    'url': info['url'],
                    'title': entry.get('title', ''),
                    'thumbnail': entry.get('thumbnail', ''),
                    'formatID': formatID,
                    'idx': idx,
                    'ytdl_format': new_info
                }
            )
            idx += 1
        return urls

if __name__ == '__main__':
    pass