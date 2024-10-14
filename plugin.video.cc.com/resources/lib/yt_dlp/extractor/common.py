# coding: utf-8
from __future__ import unicode_literals

import base64
import hashlib
import json
import os
import re
import sys
import time

from ..compat import (
    compat_etree_fromstring,
    compat_http_client,
    compat_os_name,
    compat_str,
    compat_urllib_error,
    compat_urllib_request,
    compat_urlparse,
    compat_xml_parse_error,
)

from ..utils import (
    compiled_regex_type,
    determine_ext,
    error_to_compat_str,
    ExtractorError,
    float_or_none,
    format_field,
    GeoRestrictedError,
    network_exceptions,
    NO_DEFAULT,
    parse_codecs,
    parse_m3u8_attributes,
    RegexNotFoundError,
    sanitize_filename,
    sanitized_Request,
    update_Request,
    update_url_query,
    variadic,
)


class InfoExtractor(object):
    _ready = False
    _downloader = None
    _x_forwarded_for_ip = None
    _GEO_BYPASS = True
    _GEO_COUNTRIES = None
    _GEO_IP_BLOCKS = None
    _WORKING = True

    _LOGIN_HINTS = {
        'any': 'Use --cookies, --username and --password or --netrc to provide account credentials',
        'cookies': (
            'Use --cookies for the authentication. '
            'See  https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl  for how to pass cookies'),
        'password': 'Use --username and --password or --netrc to provide account credentials',
    }

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self._x_forwarded_for_ip = None
        self._printed_messages = set()
        self.set_downloader(downloader)

    @classmethod
    def _match_valid_url(cls, url):
        # This does not use has/getattr intentionally - we want to know whether
        # we have cached the regexp for *this* class, whereas getattr would also
        # match the superclass
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        return cls._VALID_URL_RE.match(url)

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        # This function must import everything it needs (except other extractors),
        # so that lazy_extractors works correctly
        return cls._match_valid_url(url) is not None

    @classmethod
    def _match_id(cls, url):
        return cls._match_valid_url(url).group('id')

    @classmethod
    def get_temp_id(cls, url):
        try:
            return cls._match_id(url)
        except (IndexError, AttributeError):
            return None

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        self._printed_messages = set()
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    self.write_debug('Extracting URL: %s' % url)
                    ie_result = self._real_extract(url)
                    if ie_result is None:
                        return None
                    if self._x_forwarded_for_ip:
                        ie_result['__x_forwarded_for_ip'] = self._x_forwarded_for_ip
                    subtitles = ie_result.get('subtitles')
                    if (subtitles and 'live_chat' in subtitles
                            and 'no-live-chat' in self.get_param('compat_opts', [])):
                        del subtitles['live_chat']
                    return ie_result
                except GeoRestrictedError as e:
                    if self.__maybe_fake_ip_and_retry(e.countries):
                        continue
                    raise
        except ExtractorError as e:
            video_id = e.video_id or self.get_temp_id(url)
            raise ExtractorError(
                e.msg, video_id=video_id, ie=self.IE_NAME, tb=e.traceback, expected=e.expected, cause=e.cause)
        except compat_http_client.IncompleteRead as e:
            raise ExtractorError('A network error has occurred.', cause=e, expected=True, video_id=self.get_temp_id(url))
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e, video_id=self.get_temp_id(url))

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass

    @classmethod
    def ie_key(cls):
        """A string for getting the InfoExtractor with get_info_extractor"""
        return cls.__name__[:-2]

    @property
    def IE_NAME(self):
        return compat_str(type(self).__name__[:-2])

    @staticmethod
    def __can_accept_status_code(err, expected_status):
        assert isinstance(err, compat_urllib_error.HTTPError)
        if expected_status is None:
            return False
        elif callable(expected_status):
            return expected_status(err.code) is True
        else:
            return err.code in variadic(expected_status)

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None, headers={}, query={}, expected_status=None):
        """
        Return the response handle.

        See _download_webpage docstring for arguments specification.
        """
        if not self._downloader._first_webpage_request:
            sleep_interval = float_or_none(self.get_param('sleep_interval_requests')) or 0
            if sleep_interval > 0:
                self.to_screen('Sleeping %s seconds ...' % sleep_interval)
                time.sleep(sleep_interval)
        else:
            self._downloader._first_webpage_request = False

        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))

        # Some sites check X-Forwarded-For HTTP header in order to figure out
        # the origin of the client behind proxy. This allows bypassing geo
        # restriction by faking this header's value to IP that belongs to some
        # geo unrestricted country. We will do so once we encounter any
        # geo restriction error.
        if self._x_forwarded_for_ip:
            if 'X-Forwarded-For' not in headers:
                headers['X-Forwarded-For'] = self._x_forwarded_for_ip

        if isinstance(url_or_request, compat_urllib_request.Request):
            url_or_request = update_Request(
                url_or_request, data=data, headers=headers, query=query)
        else:
            if query:
                url_or_request = update_url_query(url_or_request, query)
            if data is not None or headers:
                url_or_request = sanitized_Request(url_or_request, data, headers)
        try:
            return self._downloader.urlopen(url_or_request)
        except network_exceptions as err:
            if isinstance(err, compat_urllib_error.HTTPError):
                if self.__can_accept_status_code(err, expected_status):
                    # Retain reference to error to prevent file object from
                    # being closed before it can be read. Works around the
                    # effects of <https://bugs.python.org/issue15002>
                    # introduced in Python 3.4.1.
                    err.fp._error = err
                    return err.fp

            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'

            errmsg = '%s: %s' % (errnote, error_to_compat_str(err))
            if fatal:
                raise ExtractorError(errmsg, sys.exc_info()[2], cause=err)
            else:
                self.report_warning(errmsg)
                return False

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None, fatal=True, encoding=None, data=None, headers={}, query={}, expected_status=None):
        """
        Return a tuple (page content as string, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        # Strip hashes from the URL (#1038)
        if isinstance(url_or_request, (compat_str, str)):
            url_or_request = url_or_request.partition('#')[0]

        urlh = self._request_webpage(url_or_request, video_id, note, errnote, fatal, data=data, headers=headers, query=query, expected_status=expected_status)
        if urlh is False:
            assert not fatal
            return False
        content = self._webpage_read_content(urlh, url_or_request, video_id, note, errnote, fatal, encoding=encoding)
        return (content, urlh)

    @staticmethod
    def _guess_encoding_from_content(content_type, webpage_bytes):
        m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
        if m:
            encoding = m.group(1)
        else:
            m = re.search(br'<meta[^>]+charset=[\'"]?([^\'")]+)[ /\'">]',
                          webpage_bytes[:1024])
            if m:
                encoding = m.group(1).decode('ascii')
            elif webpage_bytes.startswith(b'\xff\xfe'):
                encoding = 'utf-16'
            else:
                encoding = 'utf-8'

        return encoding

    def __check_blocked(self, content):
        first_block = content[:512]
        if ('<title>Access to this site is blocked</title>' in content
                and 'Websense' in first_block):
            msg = 'Access to this webpage has been blocked by Websense filtering software in your network.'
            blocked_iframe = self._html_search_regex(
                r'<iframe src="([^"]+)"', content,
                'Websense information URL', default=None)
            if blocked_iframe:
                msg += ' Visit %s for more details' % blocked_iframe
            raise ExtractorError(msg, expected=True)
        if '<title>The URL you requested has been blocked</title>' in first_block:
            msg = (
                'Access to this webpage has been blocked by Indian censorship. '
                'Use a VPN or proxy server (with --proxy) to route around it.')
            block_msg = self._html_search_regex(
                r'</h1><p>(.*?)</p>',
                content, 'block message', default=None)
            if block_msg:
                msg += ' (Message: "%s")' % block_msg.replace('\n', ' ')
            raise ExtractorError(msg, expected=True)
        if ('<title>TTK :: Доступ к ресурсу ограничен</title>' in content
                and 'blocklist.rkn.gov.ru' in content):
            raise ExtractorError(
                'Access to this webpage has been blocked by decision of the Russian government. '
                'Visit http://blocklist.rkn.gov.ru/ for a block reason.',
                expected=True)

    def _webpage_read_content(self, urlh, url_or_request, video_id, note=None, errnote=None, fatal=True, prefix=None, encoding=None):
        content_type = urlh.headers.get('Content-Type', '')
        webpage_bytes = urlh.read()
        if prefix is not None:
            webpage_bytes = prefix + webpage_bytes
        if not encoding:
            encoding = self._guess_encoding_from_content(content_type, webpage_bytes)
        if self.get_param('dump_intermediate_pages', False):
            self.to_screen('Dumping request to ' + urlh.geturl())
            dump = base64.b64encode(webpage_bytes).decode('ascii')
            self._downloader.to_screen(dump)
        if self.get_param('write_pages', False):
            basen = '%s_%s' % (video_id, urlh.geturl())
            trim_length = self.get_param('trim_file_name') or 240
            if len(basen) > trim_length:
                h = '___' + hashlib.md5(basen.encode('utf-8')).hexdigest()
                basen = basen[:trim_length - len(h)] + h
            raw_filename = basen + '.dump'
            filename = sanitize_filename(raw_filename, restricted=True)
            self.to_screen('Saving request to ' + filename)
            # Working around MAX_PATH limitation on Windows (see
            # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx)
            if compat_os_name == 'nt':
                absfilepath = os.path.abspath(filename)
                if len(absfilepath) > 259:
                    filename = '\\\\?\\' + absfilepath
            with open(filename, 'wb') as outf:
                outf.write(webpage_bytes)

        try:
            content = webpage_bytes.decode(encoding, 'replace')
        except LookupError:
            content = webpage_bytes.decode('utf-8', 'replace')

        self.__check_blocked(content)

        return content

    def _download_webpage(
            self, url_or_request, video_id, note=None, errnote=None,
            fatal=True, tries=1, timeout=5, encoding=None, data=None,
            headers={}, query={}, expected_status=None):
        """
        Return the data of the page as a string.

        Arguments:
        url_or_request -- plain text URL as a string or
            a compat_urllib_request.Requestobject
        video_id -- Video/playlist/item identifier (string)

        Keyword arguments:
        note -- note printed before downloading (string)
        errnote -- note printed in case of an error (string)
        fatal -- flag denoting whether error should be considered fatal,
            i.e. whether it should cause ExtractionError to be raised,
            otherwise a warning will be reported and extraction continued
        tries -- number of tries
        timeout -- sleep interval between tries
        encoding -- encoding for a page content decoding, guessed automatically
            when not explicitly specified
        data -- POST data (bytes)
        headers -- HTTP headers (dict)
        query -- URL query (dict)
        expected_status -- allows to accept failed HTTP requests (non 2xx
            status code) by explicitly specifying a set of accepted status
            codes. Can be any of the following entities:
                - an integer type specifying an exact failed status code to
                  accept
                - a list or a tuple of integer types specifying a list of
                  failed status codes to accept
                - a callable accepting an actual failed status code and
                  returning True if it should be accepted
            Note that this argument does not affect success status codes (2xx)
            which are always accepted.
        """

        success = False
        try_count = 0
        while success is False:
            try:
                res = self._download_webpage_handle(
                    url_or_request, video_id, note, errnote, fatal,
                    encoding=encoding, data=data, headers=headers, query=query,
                    expected_status=expected_status)
                success = True
            except compat_http_client.IncompleteRead as e:
                try_count += 1
                if try_count >= tries:
                    raise e
                self._sleep(timeout, video_id)
        if res is False:
            return res
        else:
            content, _ = res
            return content

    def _download_xml_handle(
            self, url_or_request, video_id, note='Downloading XML',
            errnote='Unable to download XML', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return a tuple (xml as an compat_etree_Element, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_webpage_handle(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query,
            expected_status=expected_status)
        if res is False:
            return res
        xml_string, urlh = res
        return self._parse_xml(
            xml_string, video_id, transform_source=transform_source,
            fatal=fatal), urlh

    def _download_xml(
            self, url_or_request, video_id,
            note='Downloading XML', errnote='Unable to download XML',
            transform_source=None, fatal=True, encoding=None,
            data=None, headers={}, query={}, expected_status=None):
        """
        Return the xml as an compat_etree_Element.

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_xml_handle(
            url_or_request, video_id, note=note, errnote=errnote,
            transform_source=transform_source, fatal=fatal, encoding=encoding,
            data=data, headers=headers, query=query,
            expected_status=expected_status)
        return res if res is False else res[0]

    def _parse_xml(self, xml_string, video_id, transform_source=None, fatal=True):
        if transform_source:
            xml_string = transform_source(xml_string)
        try:
            return compat_etree_fromstring(xml_string.encode('utf-8'))
        except compat_xml_parse_error as ve:
            errmsg = '%s: Failed to parse XML ' % video_id
            if fatal:
                raise ExtractorError(errmsg, cause=ve)
            else:
                self.report_warning(errmsg + str(ve))

    def _download_json_handle(
            self, url_or_request, video_id, note='Downloading JSON metadata',
            errnote='Unable to download JSON metadata', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return a tuple (JSON object, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_webpage_handle(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query,
            expected_status=expected_status)
        if res is False:
            return res
        json_string, urlh = res
        return self._parse_json(
            json_string, video_id, transform_source=transform_source,
            fatal=fatal), urlh

    def _download_json(
            self, url_or_request, video_id, note='Downloading JSON metadata',
            errnote='Unable to download JSON metadata', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return the JSON object as a dict.

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_json_handle(
            url_or_request, video_id, note=note, errnote=errnote,
            transform_source=transform_source, fatal=fatal, encoding=encoding,
            data=data, headers=headers, query=query,
            expected_status=expected_status)
        return res if res is False else res[0]

    def _parse_json(self, json_string, video_id, transform_source=None, fatal=True):
        if transform_source:
            json_string = transform_source(json_string)
        try:
            return json.loads(json_string)
        except ValueError as ve:
            errmsg = '%s: Failed to parse JSON ' % video_id
            if fatal:
                raise ExtractorError(errmsg, cause=ve)
            else:
                self.report_warning(errmsg + str(ve))

    def report_warning(self, msg, video_id=None, *args, only_once=False, **kwargs):
        idstr = format_field(video_id, template='%s: ')
        msg = f'[{self.IE_NAME}] {idstr}{msg}'
        if only_once:
            if f'WARNING: {msg}' in self._printed_messages:
                return
            self._printed_messages.add(f'WARNING: {msg}')
        self._downloader.report_warning(msg, *args, **kwargs)

    def to_screen(self, msg, *args, **kwargs):
        """Print msg to screen, prefixing it with '[ie_name]'"""
        self._downloader.to_screen('[%s] %s' % (self.IE_NAME, msg), *args, **kwargs)

    def write_debug(self, msg, *args, **kwargs):
        self._downloader.write_debug('[%s] %s' % (self.IE_NAME, msg), *args, **kwargs)

    def get_param(self, name, default=None, *args, **kwargs):
        if self._downloader:
            return self._downloader.params.get(name, default, *args, **kwargs)
        return default

    def report_drm(self, video_id, partial=False):
        self.raise_no_formats('This video is DRM protected', expected=True, video_id=video_id)

    def report_extraction(self, id_or_name):
        """Report information extraction."""
        self.to_screen('%s: Extracting information' % id_or_name)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self.to_screen('%s: Downloading webpage' % video_id)

    @staticmethod
    def playlist_result(entries, playlist_id=None, playlist_title=None, playlist_description=None, **kwargs):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        video_info.update(kwargs)
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        if playlist_description is not None:
            video_info['description'] = playlist_description
        return video_info

    def _search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        RegexNotFoundError, depending on fatal, specifying the field name.
        """
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj:
                    break

        _name = name

        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            elif isinstance(group, (list, tuple)):
                return tuple(mobj.group(g) for g in group)
            else:
                return mobj.group(group)
        elif default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract %s' % _name)
        else:
            return None

    class FormatSort:
        regex = r' *((?P<reverse>\+)?(?P<field>[a-zA-Z0-9_]+)((?P<separator>[~:])(?P<limit>.*?))?)? *$'

        default = ('hidden', 'aud_or_vid', 'hasvid', 'ie_pref', 'lang', 'quality',
                   'res', 'fps', 'hdr:12', 'codec:vp9.2', 'size', 'br', 'asr',
                   'proto', 'ext', 'hasaud', 'source', 'format_id')  # These must not be aliases
        ytdl_default = ('hasaud', 'lang', 'quality', 'tbr', 'filesize', 'vbr',
                        'height', 'width', 'proto', 'vext', 'abr', 'aext',
                        'fps', 'fs_approx', 'source', 'format_id')

        settings = {
            'vcodec': {'type': 'ordered', 'regex': True,
                       'order': ['av0?1', 'vp0?9.2', 'vp0?9', '[hx]265|he?vc?', '[hx]264|avc', 'vp0?8', 'mp4v|h263', 'theora', '', None, 'none']},
            'acodec': {'type': 'ordered', 'regex': True,
                       'order': ['opus', 'vorbis', 'aac', 'mp?4a?', 'mp3', 'e?a?c-?3', 'dts', '', None, 'none']},
            'hdr': {'type': 'ordered', 'regex': True, 'field': 'dynamic_range',
                    'order': ['dv', '(hdr)?12', r'(hdr)?10\+', '(hdr)?10', 'hlg', '', 'sdr', None]},
            'proto': {'type': 'ordered', 'regex': True, 'field': 'protocol',
                      'order': ['(ht|f)tps', '(ht|f)tp$', 'm3u8.+', '.*dash', 'ws|websocket', '', 'mms|rtsp', 'none', 'f4']},
            'vext': {'type': 'ordered', 'field': 'video_ext',
                     'order': ('mp4', 'webm', 'flv', '', 'none'),
                     'order_free': ('webm', 'mp4', 'flv', '', 'none')},
            'aext': {'type': 'ordered', 'field': 'audio_ext',
                     'order': ('m4a', 'aac', 'mp3', 'ogg', 'opus', 'webm', '', 'none'),
                     'order_free': ('opus', 'ogg', 'webm', 'm4a', 'mp3', 'aac', '', 'none')},
            'hidden': {'visible': False, 'forced': True, 'type': 'extractor', 'max': -1000},
            'aud_or_vid': {'visible': False, 'forced': True, 'type': 'multiple',
                           'field': ('vcodec', 'acodec'),
                           'function': lambda it: int(any(v != 'none' for v in it))},
            'ie_pref': {'priority': True, 'type': 'extractor'},
            'hasvid': {'priority': True, 'field': 'vcodec', 'type': 'boolean', 'not_in_list': ('none',)},
            'hasaud': {'field': 'acodec', 'type': 'boolean', 'not_in_list': ('none',)},
            'lang': {'convert': 'ignore', 'field': 'language_preference'},
            'quality': {'convert': 'float_none', 'default': -1},
            'filesize': {'convert': 'bytes'},
            'fs_approx': {'convert': 'bytes', 'field': 'filesize_approx'},
            'id': {'convert': 'string', 'field': 'format_id'},
            'height': {'convert': 'float_none'},
            'width': {'convert': 'float_none'},
            'fps': {'convert': 'float_none'},
            'tbr': {'convert': 'float_none'},
            'vbr': {'convert': 'float_none'},
            'abr': {'convert': 'float_none'},
            'asr': {'convert': 'float_none'},
            'source': {'convert': 'ignore', 'field': 'source_preference'},

            'codec': {'type': 'combined', 'field': ('vcodec', 'acodec')},
            'br': {'type': 'combined', 'field': ('tbr', 'vbr', 'abr'), 'same_limit': True},
            'size': {'type': 'combined', 'same_limit': True, 'field': ('filesize', 'fs_approx')},
            'ext': {'type': 'combined', 'field': ('vext', 'aext')},
            'res': {'type': 'multiple', 'field': ('height', 'width'),
                    'function': lambda it: (lambda l: min(l) if l else 0)(tuple(filter(None, it)))},

            # Most of these exist only for compatibility reasons
            'dimension': {'type': 'alias', 'field': 'res'},
            'resolution': {'type': 'alias', 'field': 'res'},
            'extension': {'type': 'alias', 'field': 'ext'},
            'bitrate': {'type': 'alias', 'field': 'br'},
            'total_bitrate': {'type': 'alias', 'field': 'tbr'},
            'video_bitrate': {'type': 'alias', 'field': 'vbr'},
            'audio_bitrate': {'type': 'alias', 'field': 'abr'},
            'framerate': {'type': 'alias', 'field': 'fps'},
            'language_preference': {'type': 'alias', 'field': 'lang'},  # not named as 'language' because such a field exists
            'protocol': {'type': 'alias', 'field': 'proto'},
            'source_preference': {'type': 'alias', 'field': 'source'},
            'filesize_approx': {'type': 'alias', 'field': 'fs_approx'},
            'filesize_estimate': {'type': 'alias', 'field': 'size'},
            'samplerate': {'type': 'alias', 'field': 'asr'},
            'video_ext': {'type': 'alias', 'field': 'vext'},
            'audio_ext': {'type': 'alias', 'field': 'aext'},
            'video_codec': {'type': 'alias', 'field': 'vcodec'},
            'audio_codec': {'type': 'alias', 'field': 'acodec'},
            'video': {'type': 'alias', 'field': 'hasvid'},
            'has_video': {'type': 'alias', 'field': 'hasvid'},
            'audio': {'type': 'alias', 'field': 'hasaud'},
            'has_audio': {'type': 'alias', 'field': 'hasaud'},
            'extractor': {'type': 'alias', 'field': 'ie_pref'},
            'preference': {'type': 'alias', 'field': 'ie_pref'},
            'extractor_preference': {'type': 'alias', 'field': 'ie_pref'},
            'format_id': {'type': 'alias', 'field': 'id'},
        }

        _order = []

        def _get_field_setting(self, field, key):
            if field not in self.settings:
                self.settings[field] = {}
            propObj = self.settings[field]
            if key not in propObj:
                type = propObj.get('type')
                if key == 'field':
                    default = 'preference' if type == 'extractor' else (field,) if type in ('combined', 'multiple') else field
                elif key == 'convert':
                    default = 'order' if type == 'ordered' else 'float_string' if field else 'ignore'
                else:
                    default = {'type': 'field', 'visible': True, 'order': [], 'not_in_list': (None,)}.get(key, None)
                propObj[key] = default
            return propObj[key]

        def _resolve_field_value(self, field, value, convertNone=False):
            if value is None:
                if not convertNone:
                    return None
            else:
                value = value.lower()
            conversion = self._get_field_setting(field, 'convert')
            if conversion == 'ignore':
                return None
            if conversion == 'string':
                return value
            elif conversion == 'float_none':
                return float_or_none(value)
            elif conversion == 'order':
                order_list = (self._use_free_order and self._get_field_setting(field, 'order_free')) or self._get_field_setting(field, 'order')
                use_regex = self._get_field_setting(field, 'regex')
                list_length = len(order_list)
                empty_pos = order_list.index('') if '' in order_list else list_length + 1
                if use_regex and value is not None:
                    for i, regex in enumerate(order_list):
                        if regex and re.match(regex, value):
                            return list_length - i
                    return list_length - empty_pos  # not in list
                else:  # not regex or  value = None
                    return list_length - (order_list.index(value) if value in order_list else empty_pos)
            else:
                if value.isnumeric():
                    return float(value)
                else:
                    self.settings[field]['convert'] = 'string'
                    return value

        def evaluate_params(self, params, sort_extractor):
            self._use_free_order = params.get('prefer_free_formats', False)
            self._sort_user = params.get('format_sort', [])
            self._sort_extractor = sort_extractor

            def add_item(field, reverse, closest, limit_text):
                field = field.lower()
                if field in self._order:
                    return
                self._order.append(field)
                limit = self._resolve_field_value(field, limit_text)
                data = {
                    'reverse': reverse,
                    'closest': False if limit is None else closest,
                    'limit_text': limit_text,
                    'limit': limit}
                if field in self.settings:
                    self.settings[field].update(data)
                else:
                    self.settings[field] = data

            sort_list = (
                tuple(field for field in self.default if self._get_field_setting(field, 'forced'))
                + (tuple() if params.get('format_sort_force', False)
                   else tuple(field for field in self.default if self._get_field_setting(field, 'priority')))
                + tuple(self._sort_user) + tuple(sort_extractor) + self.default)

            for item in sort_list:
                match = re.match(self.regex, item)
                if match is None:
                    raise ExtractorError('Invalid format sort string "%s" given by extractor' % item)
                field = match.group('field')
                if field is None:
                    continue
                if self._get_field_setting(field, 'type') == 'alias':
                    field = self._get_field_setting(field, 'field')
                reverse = match.group('reverse') is not None
                closest = match.group('separator') == '~'
                limit_text = match.group('limit')

                has_limit = limit_text is not None
                has_multiple_fields = self._get_field_setting(field, 'type') == 'combined'
                has_multiple_limits = has_limit and has_multiple_fields and not self._get_field_setting(field, 'same_limit')

                fields = self._get_field_setting(field, 'field') if has_multiple_fields else (field,)
                limits = limit_text.split(':') if has_multiple_limits else (limit_text,) if has_limit else tuple()
                limit_count = len(limits)
                for (i, f) in enumerate(fields):
                    add_item(f, reverse, closest,
                             limits[i] if i < limit_count
                             else limits[0] if has_limit and not has_multiple_limits
                             else None)

        def _calculate_field_preference_from_value(self, format, field, type, value):
            reverse = self._get_field_setting(field, 'reverse')
            closest = self._get_field_setting(field, 'closest')
            limit = self._get_field_setting(field, 'limit')

            if type == 'extractor':
                maximum = self._get_field_setting(field, 'max')
                if value is None or (maximum is not None and value >= maximum):
                    value = -1
            elif type == 'boolean':
                in_list = self._get_field_setting(field, 'in_list')
                not_in_list = self._get_field_setting(field, 'not_in_list')
                value = 0 if ((in_list is None or value in in_list) and (not_in_list is None or value not in not_in_list)) else -1
            elif type == 'ordered':
                value = self._resolve_field_value(field, value, True)

            # try to convert to number
            val_num = float_or_none(value, default=self._get_field_setting(field, 'default'))
            is_num = self._get_field_setting(field, 'convert') != 'string' and val_num is not None
            if is_num:
                value = val_num

            return ((-10, 0) if value is None
                    else (1, value, 0) if not is_num  # if a field has mixed strings and numbers, strings are sorted higher
                    else (0, -abs(value - limit), value - limit if reverse else limit - value) if closest
                    else (0, value, 0) if not reverse and (limit is None or value <= limit)
                    else (0, -value, 0) if limit is None or (reverse and value == limit) or value > limit
                    else (-1, value, 0))

        def _calculate_field_preference(self, format, field):
            type = self._get_field_setting(field, 'type')  # extractor, boolean, ordered, field, multiple
            get_value = lambda f: format.get(self._get_field_setting(f, 'field'))
            if type == 'multiple':
                type = 'field'  # Only 'field' is allowed in multiple for now
                actual_fields = self._get_field_setting(field, 'field')

                value = self._get_field_setting(field, 'function')(get_value(f) for f in actual_fields)
            else:
                value = get_value(field)
            return self._calculate_field_preference_from_value(format, field, type, value)

        def calculate_preference(self, format):
            # Determine missing ext
            if not format.get('ext') and 'url' in format:
                format['ext'] = determine_ext(format['url'])
            if format.get('vcodec') == 'none':
                format['audio_ext'] = format['ext'] if format.get('acodec') != 'none' else 'none'
                format['video_ext'] = 'none'
            else:
                format['video_ext'] = format['ext']
                format['audio_ext'] = 'none'
            # if format.get('preference') is None and format.get('ext') in ('f4f', 'f4m'):  # Not supported?
            #    format['preference'] = -1000

            # Determine missing bitrates
            if format.get('tbr') is None:
                if format.get('vbr') is not None and format.get('abr') is not None:
                    format['tbr'] = format.get('vbr', 0) + format.get('abr', 0)
            else:
                if format.get('vcodec') != 'none' and format.get('vbr') is None:
                    format['vbr'] = format.get('tbr') - format.get('abr', 0)
                if format.get('acodec') != 'none' and format.get('abr') is None:
                    format['abr'] = format.get('tbr') - format.get('vbr', 0)

            return tuple(self._calculate_field_preference(format, field) for field in self._order)

    def _sort_formats(self, formats, field_preference=[]):
        if not formats:
            return
        format_sort = self.FormatSort()  # params and to_screen are taken from the downloader
        format_sort.evaluate_params(self._downloader.params, field_preference)
        if self.get_param('verbose', False):
            format_sort.print_verbose_info(self._downloader.write_debug)
        formats.sort(key=lambda f: format_sort.calculate_preference(f))

    def _extract_m3u8_formats(self, *args, **kwargs):
        fmts, subs = self._extract_m3u8_formats_and_subtitles(*args, **kwargs)
        if subs:
            self._report_ignoring_subs('HLS')
        return fmts

    def _extract_m3u8_formats_and_subtitles(
            self, m3u8_url, video_id, ext=None, entry_protocol='m3u8_native',
            preference=None, quality=None, m3u8_id=None, note=None,
            errnote=None, fatal=True, live=False, data=None, headers={},
            query={}):

        res = self._download_webpage_handle(
            m3u8_url, video_id,
            note='Downloading m3u8 information' if note is None else note,
            errnote='Failed to download m3u8 information' if errnote is None else errnote,
            fatal=fatal, data=data, headers=headers, query=query)

        if res is False:
            return [], {}

        m3u8_doc, urlh = res
        m3u8_url = urlh.geturl()

        return self._parse_m3u8_formats_and_subtitles(
            m3u8_doc, m3u8_url, ext=ext, entry_protocol=entry_protocol,
            preference=preference, quality=quality, m3u8_id=m3u8_id,
            note=note, errnote=errnote, fatal=fatal, live=live, data=data,
            headers=headers, query=query, video_id=video_id)

    def _parse_m3u8_formats_and_subtitles(
            self, m3u8_doc, m3u8_url, ext=None, entry_protocol='m3u8_native',
            preference=None, quality=None, m3u8_id=None, live=False, note=None,
            errnote=None, fatal=True, data=None, headers={}, query={},
            video_id=None):
        formats, subtitles = [], {}

        if '#EXT-X-FAXS-CM:' in m3u8_doc:  # Adobe Flash Access
            return formats, subtitles

        has_drm = re.search(r'#EXT-X-(?:SESSION-)?KEY:.*?URI="skd://', m3u8_doc)

        def format_url(url):
            return url if re.match(r'^https?://', url) else compat_urlparse.urljoin(m3u8_url, url)

        if self.get_param('hls_split_discontinuity', False):
            def _extract_m3u8_playlist_indices(manifest_url=None, m3u8_doc=None):
                if not m3u8_doc:
                    if not manifest_url:
                        return []
                    m3u8_doc = self._download_webpage(
                        manifest_url, video_id, fatal=fatal, data=data, headers=headers,
                        note=False, errnote='Failed to download m3u8 playlist information')
                    if m3u8_doc is False:
                        return []
                return range(1 + sum(line.startswith('#EXT-X-DISCONTINUITY') for line in m3u8_doc.splitlines()))

        else:
            def _extract_m3u8_playlist_indices(*args, **kwargs):
                return [None]

        # References:
        # 1. https://tools.ietf.org/html/draft-pantos-http-live-streaming-21
        # 2. https://github.com/ytdl-org/youtube-dl/issues/12211
        # 3. https://github.com/ytdl-org/youtube-dl/issues/18923

        # We should try extracting formats only from master playlists [1, 4.3.4],
        # i.e. playlists that describe available qualities. On the other hand
        # media playlists [1, 4.3.3] should be returned as is since they contain
        # just the media without qualities renditions.
        # Fortunately, master playlist can be easily distinguished from media
        # playlist based on particular tags availability. As of [1, 4.3.3, 4.3.4]
        # master playlist tags MUST NOT appear in a media playlist and vice versa.
        # As of [1, 4.3.3.1] #EXT-X-TARGETDURATION tag is REQUIRED for every
        # media playlist and MUST NOT appear in master playlist thus we can
        # clearly detect media playlist with this criterion.

        if '#EXT-X-TARGETDURATION' in m3u8_doc:  # media playlist, return as is
            formats = [{
                'format_id': '-'.join(map(str, filter(None, [m3u8_id, idx]))),
                'format_index': idx,
                'url': m3u8_url,
                'ext': ext,
                'protocol': entry_protocol,
                'preference': preference,
                'quality': quality,
                'has_drm': has_drm,
            } for idx in _extract_m3u8_playlist_indices(m3u8_doc=m3u8_doc)]

            return formats, subtitles

        groups = {}
        last_stream_inf = {}

        def build_stream_name():
            # Despite specification does not mention NAME attribute for
            # EXT-X-STREAM-INF tag it still sometimes may be present (see [1]
            # or vidio test in TestInfoExtractor.test_parse_m3u8_formats)
            # 1. http://www.vidio.com/watch/165683-dj_ambred-booyah-live-2015
            stream_name = last_stream_inf.get('NAME')
            if stream_name:
                return stream_name
            # If there is no NAME in EXT-X-STREAM-INF it will be obtained
            # from corresponding rendition group
            stream_group_id = last_stream_inf.get('VIDEO')
            if not stream_group_id:
                return
            stream_group = groups.get(stream_group_id)
            if not stream_group:
                return stream_group_id
            rendition = stream_group[0]
            return rendition.get('NAME') or stream_group_id

        for line in m3u8_doc.splitlines():
            if line.startswith('#EXT-X-STREAM-INF:'):
                last_stream_inf = parse_m3u8_attributes(line)
            elif line.startswith('#') or not line.strip():
                continue
            else:
                tbr = float_or_none(
                    last_stream_inf.get('AVERAGE-BANDWIDTH')
                    or last_stream_inf.get('BANDWIDTH'), scale=1000)
                manifest_url = format_url(line.strip())

                for idx in _extract_m3u8_playlist_indices(manifest_url):
                    format_id = [m3u8_id, None, idx]
                    # Bandwidth of live streams may differ over time thus making
                    # format_id unpredictable. So it's better to keep provided
                    # format_id intact.
                    if not live:
                        stream_name = build_stream_name()
                        format_id[1] = stream_name if stream_name else '%d' % (tbr if tbr else len(formats))
                    f = {
                        'format_id': '-'.join(map(str, filter(None, format_id))),
                        'format_index': idx,
                        'url': manifest_url,
                        'manifest_url': m3u8_url,
                        'tbr': tbr,
                        'ext': ext,
                        'fps': float_or_none(last_stream_inf.get('FRAME-RATE')),
                        'protocol': entry_protocol,
                        'preference': preference,
                        'quality': quality,
                    }
                    resolution = last_stream_inf.get('RESOLUTION')
                    if resolution:
                        mobj = re.search(r'(?P<width>\d+)[xX](?P<height>\d+)', resolution)
                        if mobj:
                            f['width'] = int(mobj.group('width'))
                            f['height'] = int(mobj.group('height'))
                    # Unified Streaming Platform
                    mobj = re.search(
                        r'audio.*?(?:%3D|=)(\d+)(?:-video.*?(?:%3D|=)(\d+))?', f['url'])
                    if mobj:
                        abr, vbr = mobj.groups()
                        abr, vbr = float_or_none(abr, 1000), float_or_none(vbr, 1000)
                        f.update({
                            'vbr': vbr,
                            'abr': abr,
                        })
                    codecs = parse_codecs(last_stream_inf.get('CODECS'))
                    f.update(codecs)
                    audio_group_id = last_stream_inf.get('AUDIO')
                    # As per [1, 4.3.4.1.1] any EXT-X-STREAM-INF tag which
                    # references a rendition group MUST have a CODECS attribute.
                    # However, this is not always respected, for example, [2]
                    # contains EXT-X-STREAM-INF tag which references AUDIO
                    # rendition group but does not have CODECS and despite
                    # referencing an audio group it represents a complete
                    # (with audio and video) format. So, for such cases we will
                    # ignore references to rendition groups and treat them
                    # as complete formats.
                    if audio_group_id and codecs and f.get('vcodec') != 'none':
                        audio_group = groups.get(audio_group_id)
                        if audio_group and audio_group[0].get('URI'):
                            # TODO: update acodec for audio only formats with
                            # the same GROUP-ID
                            f['acodec'] = 'none'
                    if not f.get('ext'):
                        f['ext'] = 'm4a' if f.get('vcodec') == 'none' else 'mp4'
                    formats.append(f)

                    # for DailyMotion
                    progressive_uri = last_stream_inf.get('PROGRESSIVE-URI')
                    if progressive_uri:
                        http_f = f.copy()
                        del http_f['manifest_url']
                        http_f.update({
                            'format_id': f['format_id'].replace('hls-', 'http-'),
                            'protocol': 'http',
                            'url': progressive_uri,
                        })
                        formats.append(http_f)

                last_stream_inf = {}
        return formats, subtitles
