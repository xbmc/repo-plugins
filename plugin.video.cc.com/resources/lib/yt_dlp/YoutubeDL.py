#!/usr/bin/env python3
# coding: utf-8

from __future__ import absolute_import, unicode_literals

import collections
import copy
import datetime
import errno
import functools
import io
import itertools
import json
import os
import re
import sys
import tempfile
import time
import tokenize
import traceback
import random


from .compat import (
    compat_basestring,
    compat_numeric_types,
    compat_str,
    compat_tokenize_tokenize,
    compat_urllib_error,
    compat_urllib_request,
    compat_urllib_request_DataHandler,
)
from .utils import (
    args_to_str,
    determine_ext,
    DownloadError,
    encode_compat_str,
    EntryNotInPlaylist,
    error_to_compat_str,
    ExistingVideoReached,
    ExtractorError,
    format_field,
    GeoRestrictedError,
    HEADRequest,
    int_or_none,
    LazyList,
    locked_file,
    make_HTTPS_handler,
    MaxDownloadsReached,
    network_exceptions,
    orderedSet,
    PagedList,
    PerRequestProxyHandler,
    PostProcessingError,
    register_socks_protocols,
    RejectedVideoReached,
    replace_extension,
    SameFileError,
    sanitize_filename,
    sanitize_url,
    sanitized_Request,
    std_headers,
    STR_FORMAT_RE_TMPL,
    STR_FORMAT_TYPES,
    str_or_none,
    strftime_or_none,
    supports_terminal_sequences,
    TERMINAL_SEQUENCES,
    ThrottledDownload,
    traverse_obj,
    try_get,
    UnavailableVideoError,
    url_basename,
    variadic,
    write_string,
    YoutubeDLCookieProcessor,
    YoutubeDLHandler,
    YoutubeDLRedirectHandler,
)
from .extractor import (
    gen_extractor_classes,
    get_info_extractor,
)


class YoutubeDL(object):
    _NUMERIC_FIELDS = set((
        'width', 'height', 'tbr', 'abr', 'asr', 'vbr', 'fps', 'filesize', 'filesize_approx',
        'timestamp', 'release_timestamp',
        'duration', 'view_count', 'like_count', 'dislike_count', 'repost_count',
        'average_rating', 'comment_count', 'age_limit',
        'start_time', 'end_time',
        'chapter_number', 'season_number', 'episode_number',
        'track_number', 'disc_number', 'release_year',
    ))

    _format_selection_exts = {
        'audio': {'m4a', 'mp3', 'ogg', 'aac'},
        'video': {'mp4', 'flv', 'webm', '3gp'},
        'storyboards': {'mhtml'},
    }

    params = None
    _ies = {}
    _pps = {'pre_process': [], 'before_dl': [], 'after_move': [], 'post_process': []}
    _printed_messages = set()
    _first_webpage_request = True
    _download_retcode = None
    _num_downloads = None
    _playlist_level = 0
    _playlist_urls = set()
    _screen_file = None

    def __init__(self, params=None, auto_init=True):
        """Create a FileDownloader object with the given options.
        @param auto_init    Whether to load the default extractors and print header (if verbose).
                            Set to 'no_verbose_header' to not ptint the header
        """
        if params is None:
            params = {}
        self._ies = {}
        self._ies_instances = {}
        self._pps = {'pre_process': [], 'before_dl': [], 'after_move': [], 'post_process': []}
        self._printed_messages = set()
        self._first_webpage_request = True
        self._post_hooks = []
        self._progress_hooks = []
        self._postprocessor_hooks = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]
        self._err_file = sys.stderr
        self.params = params

        if sys.version_info < (3, 6):
            self.report_warning(
                'Python version %d.%d is not supported! Please update to Python 3.6 or above' % sys.version_info[:2])

        for msg in self.params.get('warnings', []):
            self.report_warning(msg)

        if 'overwrites' not in self.params and self.params.get('nooverwrites') is not None:
            # nooverwrites was unnecessarily changed to overwrites
            # in 0c3d0f51778b153f65c21906031c2e091fcfb641
            # This ensures compatibility with both keys
            self.params['overwrites'] = not self.params['nooverwrites']
        elif self.params.get('overwrites') is None:
            self.params.pop('overwrites', None)
        else:
            self.params['nooverwrites'] = not self.params['overwrites']

        if (sys.platform != 'win32'
                and sys.getfilesystemencoding() in ['ascii', 'ANSI_X3.4-1968']
                and not params.get('restrictfilenames', False)):
            # Unicode filesystem API will throw errors (#1474, #13027)
            self.report_warning(
                'Assuming --restrict-filenames since file system encoding '
                'cannot encode all characters. '
                'Set the LC_ALL environment variable to fix this.')
            self.params['restrictfilenames'] = True

        self.format_selector = None

        self._setup_opener()

        if auto_init:
            self.add_default_info_extractors()

        for ph in self.params.get('post_hooks', []):
            self.add_post_hook(ph)

        for ph in self.params.get('progress_hooks', []):
            self.add_progress_hook(ph)

        register_socks_protocols()

        def preload_download_archive(fn):
            """Preload the archive, if any is specified"""
            if fn is None:
                return False
            self.write_debug('Loading archive file %r\n' % fn)
            try:
                with locked_file(fn, 'r', encoding='utf-8') as archive_file:
                    for line in archive_file:
                        self.archive.add(line.strip())
            except IOError as ioe:
                if ioe.errno != errno.ENOENT:
                    raise
                return False
            return True

        self.archive = set()
        preload_download_archive(self.params.get('download_archive'))

    def warn_if_short_id(self, argv):
        # short YouTube ID starting with dash?
        idxs = [
            i for i, a in enumerate(argv)
            if re.match(r'^-[0-9A-Za-z_-]{10}$', a)]
        if idxs:
            correct_argv = (
                ['yt-dlp']
                + [a for i, a in enumerate(argv) if i not in idxs]
                + ['--'] + [argv[i] for i in idxs]
            )
            self.report_warning(
                'Long argument string detected. '
                'Use -- to separate parameters and URLs, like this:\n%s\n' %
                args_to_str(correct_argv))

    def add_info_extractor(self, ie):
        """Add an InfoExtractor object to the end of the list."""
        ie_key = ie.ie_key()
        self._ies[ie_key] = ie
        if not isinstance(ie, type):
            self._ies_instances[ie_key] = ie
            ie.set_downloader(self)

    def _get_info_extractor_class(self, ie_key):
        ie = self._ies.get(ie_key)
        if ie is None:
            ie = get_info_extractor(ie_key)
            self.add_info_extractor(ie)
        return ie

    def get_info_extractor(self, ie_key):
        """
        Get an instance of an IE with name ie_key, it will try to get one from
        the _ies list, if there's no instance it will create a new one and add
        it to the extractor list.
        """
        ie = self._ies_instances.get(ie_key)
        if ie is None:
            ie = get_info_extractor(ie_key)()
            self.add_info_extractor(ie)
        return ie

    def add_default_info_extractors(self):
        """
        Add the InfoExtractors returned by gen_extractors to the end of the list
        """
        for ie in gen_extractor_classes():
            self.add_info_extractor(ie)

    def add_post_hook(self, ph):
        """Add the post hook"""
        self._post_hooks.append(ph)

    def add_progress_hook(self, ph):
        """Add the download progress hook"""
        self._progress_hooks.append(ph)

    def add_postprocessor_hook(self, ph):
        """Add the postprocessing progress hook"""
        self._postprocessor_hooks.append(ph)

    def _bidi_workaround(self, message):
        if not hasattr(self, '_output_channel'):
            return message

        assert hasattr(self, '_output_process')
        assert isinstance(message, compat_str)
        line_count = message.count('\n') + 1
        self._output_process.stdin.write((message + '\n').encode('utf-8'))
        self._output_process.stdin.flush()
        res = ''.join(self._output_channel.readline().decode('utf-8')
                      for _ in range(line_count))
        return res[:-len('\n')]

    def _write_string(self, message, out=None, only_once=False):
        if only_once:
            if message in self._printed_messages:
                return
            self._printed_messages.add(message)
        write_string(message, out=out, encoding=self.params.get('encoding'))

    def to_stdout(self, message, skip_eol=False, quiet=False):
        """Print message to stdout"""
        if self.params.get('logger'):
            self.params['logger'].debug(message)
        elif not quiet or self.params.get('verbose'):
            self._write_string(
                '%s%s' % (self._bidi_workaround(message), ('' if skip_eol else '\n')),
                self._err_file if quiet else self._screen_file)

    def to_stderr(self, message, only_once=False):
        """Print message to stderr"""
        assert isinstance(message, compat_str)
        if self.params.get('logger'):
            self.params['logger'].error(message)
        else:
            self._write_string('%s\n' % self._bidi_workaround(message), self._err_file, only_once=only_once)

    def __enter__(self):
        return self

    def __exit__(self, *args):

        if self.params.get('cookiefile') is not None:
            self.cookiejar.save(ignore_discard=True, ignore_expires=True)

    def trouble(self, message=None, tb=None):
        """Determine action to take when a download problem appears.

        Depending on if the downloader has been configured to ignore
        download errors or not, this method may throw an exception or
        not when errors are found, after printing the message.

        tb, if given, is additional traceback information.
        """
        if message is not None:
            self.to_stderr(message)
        if self.params.get('verbose'):
            if tb is None:
                if sys.exc_info()[0]:  # if .trouble has been called from an except block
                    tb = ''
                    if hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                        tb += ''.join(traceback.format_exception(*sys.exc_info()[1].exc_info))
                    tb += encode_compat_str(traceback.format_exc())
                else:
                    tb_data = traceback.format_list(traceback.extract_stack())
                    tb = ''.join(tb_data)
            if tb:
                self.to_stderr(tb)
        if not self.params.get('ignoreerrors'):
            if sys.exc_info()[0] and hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                exc_info = sys.exc_info()[1].exc_info
            else:
                exc_info = sys.exc_info()
            raise DownloadError(message, exc_info)
        self._download_retcode = 1

    def to_screen(self, message, skip_eol=False):
        """Print message to stdout if not in quiet mode"""
        self.to_stdout(
            message, skip_eol, quiet=self.params.get('quiet', False))

    def report_warning(self, message, only_once=False):
        '''
        Print the message to stderr, it will be prefixed with 'WARNING:'
        If stderr is a tty file the 'WARNING:' will be colored
        '''
        if self.params.get('logger') is not None:
            self.params['logger'].warning(message)
        else:
            if self.params.get('no_warnings'):
                return
            self.to_stderr(f'{"WARNING:"} {message}', only_once)

    def report_error(self, message, tb=None):
        '''
        Do the same as trouble, but prefixes the message with 'ERROR:', colored
        in red if stderr is a tty file.
        '''
        self.trouble(f'{"ERROR:"} {message}', tb)

    def write_debug(self, message, only_once=False):
        '''Log debug message or Print message to stderr'''
        if not self.params.get('verbose', False):
            return
        message = '[debug] %s' % message
        if self.params.get('logger'):
            self.params['logger'].debug(message)
        else:
            self.to_stderr(message, only_once)

    def raise_no_formats(self, info, forced=False):
        has_drm = info.get('__has_drm')
        msg = 'This video is DRM protected' if has_drm else 'No video formats found!'
        expected = self.params.get('ignore_no_formats_error')
        if forced or not expected:
            raise ExtractorError(msg, video_id=info['id'], ie=info['extractor'],
                                 expected=has_drm or expected)
        else:
            self.report_warning(msg)

    def _match_entry(self, info_dict, incomplete=False, silent=False):
        """ Returns None if the file should be downloaded """

        video_title = info_dict.get('title', info_dict.get('id', 'video'))

        def check_filter():
            if 'title' in info_dict:
                # This can happen when we're just evaluating the playlist
                title = info_dict['title']
                matchtitle = self.params.get('matchtitle', False)
                if matchtitle:
                    if not re.search(matchtitle, title, re.IGNORECASE):
                        return '"' + title + '" title did not match pattern "' + matchtitle + '"'
                rejecttitle = self.params.get('rejecttitle', False)
                if rejecttitle:
                    if re.search(rejecttitle, title, re.IGNORECASE):
                        return '"' + title + '" title matched reject pattern "' + rejecttitle + '"'
            view_count = info_dict.get('view_count')
            if view_count is not None:
                min_views = self.params.get('min_views')
                if min_views is not None and view_count < min_views:
                    return 'Skipping %s, because it has not reached minimum view count (%d/%d)' % (video_title, view_count, min_views)
                max_views = self.params.get('max_views')
                if max_views is not None and view_count > max_views:
                    return 'Skipping %s, because it has exceeded the maximum view count (%d/%d)' % (video_title, view_count, max_views)

            match_filter = self.params.get('match_filter')
            if match_filter is not None:
                try:
                    ret = match_filter(info_dict, incomplete=incomplete)
                except TypeError:
                    # For backward compatibility
                    ret = None if incomplete else match_filter(info_dict)
                if ret is not None:
                    return ret
            return None

        reason = check_filter()
        break_opt, break_err = 'break_on_reject', RejectedVideoReached
        if reason is not None:
            if not silent:
                self.to_screen('[download] ' + reason)
            if self.params.get(break_opt, False):
                raise break_err()
        return reason

    @staticmethod
    def add_extra_info(info_dict, extra_info):
        '''Set the keys from extra_info in info dict if they are missing'''
        for key, value in extra_info.items():
            info_dict.setdefault(key, value)

    def extract_info(self, url, download=True, ie_key=None, extra_info=None,
                     process=True, force_generic_extractor=False):
        """
        Return a list with a dictionary for each video extracted.

        Arguments:
        url -- URL to extract

        Keyword arguments:
        download -- whether to download videos during extraction
        ie_key -- extractor key hint
        extra_info -- dictionary containing the extra values to add to each result
        process -- whether to resolve all unresolved references (URLs, playlist items),
            must be True for download to work.
        force_generic_extractor -- force using the generic extractor
        """

        if extra_info is None:
            extra_info = {}

        if not ie_key and force_generic_extractor:
            ie_key = 'Generic'

        if ie_key:
            ies = {ie_key: self._get_info_extractor_class(ie_key)}
        else:
            ies = self._ies

        for ie_key, ie in ies.items():
            if not ie.suitable(url):
                continue

            if not ie.working():
                self.report_warning('The program functionality for this site has been marked as broken, '
                                    'and will probably not work.')

            return self.__extract_info(url, self.get_info_extractor(ie_key), download, extra_info, process)
        else:
            self.report_error('no suitable InfoExtractor for URL %s' % url)

    def __handle_extraction_exceptions(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except GeoRestrictedError as e:
                msg = e.msg
                msg += '\nYou might want to use a VPN or a proxy server (with --proxy) to workaround.'
                self.report_error(msg)
            except ExtractorError as e:  # An error we somewhat expected
                self.report_error(compat_str(e), e.format_traceback())
            except (MaxDownloadsReached, ExistingVideoReached, RejectedVideoReached, LazyList.IndexError):
                raise
            except Exception as e:
                raise e
        return wrapper

    @__handle_extraction_exceptions
    def __extract_info(self, url, ie, download, extra_info, process):
        ie_result = ie.extract(url)
        if ie_result is None:  # Finished already (backwards compatibility; listformats and friends should be moved here)
            return
        if isinstance(ie_result, list):
            # Backwards compatibility: old IE result format
            ie_result = {
                '_type': 'compat_list',
                'entries': ie_result,
            }
        if extra_info.get('original_url'):
            ie_result.setdefault('original_url', extra_info['original_url'])
        self.add_default_extra_info(ie_result, ie, url)
        if process:
            return self.process_ie_result(ie_result, download, extra_info)
        else:
            return ie_result

    def add_default_extra_info(self, ie_result, ie, url):
        if url is not None:
            self.add_extra_info(ie_result, {
                'webpage_url': url,
                'original_url': url,
                'webpage_url_basename': url_basename(url),
            })
        if ie is not None:
            self.add_extra_info(ie_result, {
                'extractor': ie.IE_NAME,
                'extractor_key': ie.ie_key(),
            })

    def process_ie_result(self, ie_result, download=True, extra_info=None):
        """
        Take the result of the ie(may be modified) and resolve all unresolved
        references (URLs, playlist items).

        It will also download the videos if 'download'.
        Returns the resolved ie_result.
        """
        if extra_info is None:
            extra_info = {}
        result_type = ie_result.get('_type', 'video')

        if result_type in ('url', 'url_transparent'):
            ie_result['url'] = sanitize_url(ie_result['url'])
            if ie_result.get('original_url'):
                extra_info.setdefault('original_url', ie_result['original_url'])

            extract_flat = self.params.get('extract_flat', False)
            if ((extract_flat == 'in_playlist' and 'playlist' in extra_info)
                    or extract_flat is True):
                info_copy = ie_result.copy()
                ie = try_get(ie_result.get('ie_key'), self.get_info_extractor)
                if ie and not ie_result.get('id'):
                    info_copy['id'] = ie.get_temp_id(ie_result['url'])
                self.add_default_extra_info(info_copy, ie, ie_result['url'])
                self.add_extra_info(info_copy, extra_info)
                self.__forced_printings(info_copy, self.prepare_filename(info_copy), incomplete=True)
                if self.params.get('force_write_download_archive', False):
                    self.record_download_archive(info_copy)
                return ie_result

        if result_type == 'video':
            self.add_extra_info(ie_result, extra_info)
            ie_result = self.process_video_result(ie_result, download=download)
            additional_urls = (ie_result or {}).get('additional_urls')
            if additional_urls:
                # TODO: Improve MetadataParserPP to allow setting a list
                if isinstance(additional_urls, compat_str):
                    additional_urls = [additional_urls]
                self.to_screen(
                    '[info] %s: %d additional URL(s) requested' % (ie_result['id'], len(additional_urls)))
                self.write_debug('Additional URLs: "%s"' % '", "'.join(additional_urls))
                ie_result['additional_entries'] = [
                    self.extract_info(
                        url, download, extra_info,
                        force_generic_extractor=self.params.get('force_generic_extractor'))
                    for url in additional_urls
                ]
            return ie_result
        elif result_type == 'url':
            # We have to add extra_info to the results because it may be
            # contained in a playlist
            return self.extract_info(
                ie_result['url'], download,
                ie_key=ie_result.get('ie_key'),
                extra_info=extra_info)
        elif result_type == 'url_transparent':
            # Use the information from the embedding page
            info = self.extract_info(
                ie_result['url'], ie_key=ie_result.get('ie_key'),
                extra_info=extra_info, download=False, process=False)

            # extract_info may return None when ignoreerrors is enabled and
            # extraction failed with an error, don't crash and return early
            # in this case
            if not info:
                return info

            force_properties = dict(
                (k, v) for k, v in ie_result.items() if v is not None)
            for f in ('_type', 'url', 'id', 'extractor', 'extractor_key', 'ie_key'):
                if f in force_properties:
                    del force_properties[f]
            new_result = info.copy()
            new_result.update(force_properties)

            # Extracted info may not be a video result (i.e.
            # info.get('_type', 'video') != video) but rather an url or
            # url_transparent. In such cases outer metadata (from ie_result)
            # should be propagated to inner one (info). For this to happen
            # _type of info should be overridden with url_transparent. This
            # fixes issue from https://github.com/ytdl-org/youtube-dl/pull/11163.
            if new_result.get('_type') == 'url':
                new_result['_type'] = 'url_transparent'

            return self.process_ie_result(
                new_result, download=download, extra_info=extra_info)
        elif result_type in ('playlist', 'multi_video'):
            # Protect from infinite recursion due to recursively nested playlists
            # (see https://github.com/ytdl-org/youtube-dl/issues/27833)
            webpage_url = ie_result['webpage_url']
            if webpage_url in self._playlist_urls:
                self.to_screen(
                    '[download] Skipping already downloaded playlist: %s'
                    % ie_result.get('title') or ie_result.get('id'))
                return

            self._playlist_level += 1
            self._playlist_urls.add(webpage_url)
            self._sanitize_thumbnails(ie_result)
            try:
                return self.__process_playlist(ie_result, download)
            finally:
                self._playlist_level -= 1
                if not self._playlist_level:
                    self._playlist_urls.clear()
        elif result_type == 'compat_list':
            self.report_warning(
                'Extractor %s returned a compat_list result. '
                'It needs to be updated.' % ie_result.get('extractor'))

            def _fixup(r):
                self.add_extra_info(r, {
                    'extractor': ie_result['extractor'],
                    'webpage_url': ie_result['webpage_url'],
                    'webpage_url_basename': url_basename(ie_result['webpage_url']),
                    'extractor_key': ie_result['extractor_key'],
                })
                return r
            ie_result['entries'] = [
                self.process_ie_result(_fixup(r), download, extra_info)
                for r in ie_result['entries']
            ]
            return ie_result
        else:
            raise Exception('Invalid result type: %s' % result_type)

    def __process_playlist(self, ie_result, download):
        # We process each entry in the playlist
        playlist = ie_result.get('title') or ie_result.get('id')
        self.to_screen('[download] Downloading playlist: %s' % playlist)

        if 'entries' not in ie_result:
            raise EntryNotInPlaylist('There are no entries')
        incomplete_entries = bool(ie_result.get('requested_entries'))
        if incomplete_entries:
            def fill_missing_entries(entries, indexes):
                ret = [None] * max(*indexes)
                for i, entry in zip(indexes, entries):
                    ret[i - 1] = entry
                return ret
            ie_result['entries'] = fill_missing_entries(ie_result['entries'], ie_result['requested_entries'])

        playlist_results = []

        playliststart = self.params.get('playliststart', 1)
        playlistend = self.params.get('playlistend')
        # For backwards compatibility, interpret -1 as whole list
        if playlistend == -1:
            playlistend = None

        playlistitems_str = self.params.get('playlist_items')
        playlistitems = None
        if playlistitems_str is not None:
            def iter_playlistitems(format):
                for string_segment in format.split(','):
                    if '-' in string_segment:
                        start, end = string_segment.split('-')
                        for item in range(int(start), int(end) + 1):
                            yield int(item)
                    else:
                        yield int(string_segment)
            playlistitems = orderedSet(iter_playlistitems(playlistitems_str))

        ie_entries = ie_result['entries']
        msg = (
            'Downloading %d videos' if not isinstance(ie_entries, list)
            else 'Collected %d videos; downloading %%d of them' % len(ie_entries))

        if isinstance(ie_entries, list):
            def get_entry(i):
                return ie_entries[i - 1]
        else:
            if not isinstance(ie_entries, (PagedList, LazyList)):
                ie_entries = LazyList(ie_entries)

            def get_entry(i):
                return YoutubeDL.__handle_extraction_exceptions(
                    lambda self, i: ie_entries[i - 1]
                )(self, i)

        entries = []
        items = playlistitems if playlistitems is not None else itertools.count(playliststart)
        for i in items:
            if i == 0:
                continue
            if playlistitems is None and playlistend is not None and playlistend < i:
                break
            entry = None
            try:
                entry = get_entry(i)
                if entry is None:
                    raise EntryNotInPlaylist()
            except (IndexError, EntryNotInPlaylist):
                if incomplete_entries:
                    raise EntryNotInPlaylist()
                elif not playlistitems:
                    break
            entries.append(entry)
            try:
                if entry is not None:
                    self._match_entry(entry, incomplete=True, silent=True)
            except (ExistingVideoReached, RejectedVideoReached):
                break
        ie_result['entries'] = entries

        # Save playlist_index before re-ordering
        entries = [
            ((playlistitems[i - 1] if playlistitems else i + playliststart - 1), entry)
            for i, entry in enumerate(entries, 1)
            if entry is not None]
        n_entries = len(entries)

        if not playlistitems and (playliststart or playlistend):
            playlistitems = list(range(playliststart, playliststart + n_entries))
        ie_result['requested_entries'] = playlistitems

        if self.params.get('allow_playlist_files', True):
            ie_copy = {
                'playlist': playlist,
                'playlist_id': ie_result.get('id'),
                'playlist_title': ie_result.get('title'),
                'playlist_uploader': ie_result.get('uploader'),
                'playlist_uploader_id': ie_result.get('uploader_id'),
                'playlist_index': 0,
            }
            ie_copy.update(dict(ie_result))

        if self.params.get('playlistreverse', False):
            entries = entries[::-1]
        if self.params.get('playlistrandom', False):
            random.shuffle(entries)

        x_forwarded_for = ie_result.get('__x_forwarded_for_ip')

        self.to_screen('[%s] playlist %s: %s' % (ie_result['extractor'], playlist, msg % n_entries))
        failures = 0
        max_failures = self.params.get('skip_playlist_after_errors') or float('inf')
        for i, entry_tuple in enumerate(entries, 1):
            playlist_index, entry = entry_tuple
            if 'playlist-index' in self.params.get('compat_opts', []):
                playlist_index = playlistitems[i - 1] if playlistitems else i + playliststart - 1
            self.to_screen('[download] Downloading video %s of %s' % (i, n_entries))
            # This __x_forwarded_for_ip thing is a bit ugly but requires
            # minimal changes
            if x_forwarded_for:
                entry['__x_forwarded_for_ip'] = x_forwarded_for
            extra = {
                'n_entries': n_entries,
                '_last_playlist_index': max(playlistitems) if playlistitems else (playlistend or n_entries),
                'playlist_index': playlist_index,
                'playlist_autonumber': i,
                'playlist': playlist,
                'playlist_id': ie_result.get('id'),
                'playlist_title': ie_result.get('title'),
                'playlist_uploader': ie_result.get('uploader'),
                'playlist_uploader_id': ie_result.get('uploader_id'),
                'extractor': ie_result['extractor'],
                'webpage_url': ie_result['webpage_url'],
                'webpage_url_basename': url_basename(ie_result['webpage_url']),
                'extractor_key': ie_result['extractor_key'],
            }

            if self._match_entry(entry, incomplete=True) is not None:
                continue

            entry_result = self.__process_iterable_entry(entry, download, extra)
            if not entry_result:
                failures += 1
            if failures >= max_failures:
                self.report_error(
                    'Skipping the remaining entries in playlist "%s" since %d items failed extraction' % (playlist, failures))
                break
            # TODO: skip failed (empty) entries?
            playlist_results.append(entry_result)
        ie_result['entries'] = playlist_results
        self.to_screen('[download] Finished downloading playlist: %s' % playlist)
        return ie_result

    @__handle_extraction_exceptions
    def __process_iterable_entry(self, entry, download, extra_info):
        return self.process_ie_result(
            entry, download=download, extra_info=extra_info)

    def _default_format_spec(self, info_dict, download=True):

        prefer_best = (
            not self.params.get('simulate')
            and download
            and info_dict.get('is_live', False))
        compat = (
            prefer_best
            or self.params.get('allow_multiple_audio_streams', False)
            or 'format-spec' in self.params.get('compat_opts', []))

        return (
            'best/bestvideo+bestaudio' if prefer_best
            else 'bestvideo*+bestaudio/best' if not compat
            else 'bestvideo+bestaudio/best')

    def build_format_selector(self, format_spec):
        def syntax_error(note, start):
            message = (
                'Invalid format specification: '
                '{0}\n\t{1}\n\t{2}^'.format(note, format_spec, ' ' * start[1]))
            return SyntaxError(message)

        PICKFIRST = 'PICKFIRST'
        MERGE = 'MERGE'
        SINGLE = 'SINGLE'
        GROUP = 'GROUP'
        FormatSelector = collections.namedtuple('FormatSelector', ['type', 'selector', 'filters'])

        check_formats = self.params.get('check_formats')

        def _parse_filter(tokens):
            filter_parts = []
            for type, string, start, _, _ in tokens:
                if type == tokenize.OP and string == ']':
                    return ''.join(filter_parts)
                else:
                    filter_parts.append(string)

        def _remove_unused_ops(tokens):
            # Remove operators that we don't use and join them with the surrounding strings
            # for example: 'mp4' '-' 'baseline' '-' '16x9' is converted to 'mp4-baseline-16x9'
            ALLOWED_OPS = ('/', '+', ',', '(', ')')
            last_string, last_start, last_end, last_line = None, None, None, None
            for type, string, start, end, line in tokens:
                if type == tokenize.OP and string == '[':
                    if last_string:
                        yield tokenize.NAME, last_string, last_start, last_end, last_line
                        last_string = None
                    yield type, string, start, end, line
                    # everything inside brackets will be handled by _parse_filter
                    for type, string, start, end, line in tokens:
                        yield type, string, start, end, line
                        if type == tokenize.OP and string == ']':
                            break
                elif type == tokenize.OP and string in ALLOWED_OPS:
                    if last_string:
                        yield tokenize.NAME, last_string, last_start, last_end, last_line
                        last_string = None
                    yield type, string, start, end, line
                elif type in [tokenize.NAME, tokenize.NUMBER, tokenize.OP]:
                    if not last_string:
                        last_string = string
                        last_start = start
                        last_end = end
                    else:
                        last_string += string
            if last_string:
                yield tokenize.NAME, last_string, last_start, last_end, last_line

        def _parse_format_selection(tokens, inside_merge=False, inside_choice=False, inside_group=False):
            selectors = []
            current_selector = None
            for type, string, start, _, _ in tokens:
                # ENCODING is only defined in python 3.x
                if type == getattr(tokenize, 'ENCODING', None):
                    continue
                elif type in [tokenize.NAME, tokenize.NUMBER]:
                    current_selector = FormatSelector(SINGLE, string, [])
                elif type == tokenize.OP:
                    if string == ')':
                        if not inside_group:
                            # ')' will be handled by the parentheses group
                            tokens.restore_last_token()
                        break
                    elif inside_merge and string in ['/', ',']:
                        tokens.restore_last_token()
                        break
                    elif inside_choice and string == ',':
                        tokens.restore_last_token()
                        break
                    elif string == ',':
                        if not current_selector:
                            raise syntax_error('"," must follow a format selector', start)
                        selectors.append(current_selector)
                        current_selector = None
                    elif string == '/':
                        if not current_selector:
                            raise syntax_error('"/" must follow a format selector', start)
                        first_choice = current_selector
                        second_choice = _parse_format_selection(tokens, inside_choice=True)
                        current_selector = FormatSelector(PICKFIRST, (first_choice, second_choice), [])
                    elif string == '[':
                        if not current_selector:
                            current_selector = FormatSelector(SINGLE, 'best', [])
                        format_filter = _parse_filter(tokens)
                        current_selector.filters.append(format_filter)
                    elif string == '(':
                        if current_selector:
                            raise syntax_error('Unexpected "("', start)
                        group = _parse_format_selection(tokens, inside_group=True)
                        current_selector = FormatSelector(GROUP, group, [])
                    elif string == '+':
                        if not current_selector:
                            raise syntax_error('Unexpected "+"', start)
                        selector_1 = current_selector
                        selector_2 = _parse_format_selection(tokens, inside_merge=True)
                        if not selector_2:
                            raise syntax_error('Expected a selector', start)
                        current_selector = FormatSelector(MERGE, (selector_1, selector_2), [])
                    else:
                        raise syntax_error('Operator not recognized: "{0}"'.format(string), start)
                elif type == tokenize.ENDMARKER:
                    break
            if current_selector:
                selectors.append(current_selector)
            return selectors

        def _check_formats(formats):
            if not check_formats:
                yield from formats
                return
            for f in formats:
                self.to_screen('[info] Testing format %s' % f['format_id'])
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.tmp', delete=False,
                    dir=self.get_output_path('temp') or None)
                temp_file.close()
                try:
                    success, _ = self.dl(temp_file.name, f, test=True)
                except (DownloadError, IOError, OSError, ValueError) + network_exceptions:
                    success = False
                finally:
                    if os.path.exists(temp_file.name):
                        try:
                            os.remove(temp_file.name)
                        except OSError:
                            self.report_warning('Unable to delete temporary file "%s"' % temp_file.name)
                if success:
                    yield f
                else:
                    self.to_screen('[info] Unable to download format %s. Skipping...' % f['format_id'])

        def _build_selector_function(selector):
            if isinstance(selector, list):  # ,
                fs = [_build_selector_function(s) for s in selector]

                def selector_function(ctx):
                    for f in fs:
                        yield from f(ctx)
                return selector_function

            elif selector.type == GROUP:  # ()
                selector_function = _build_selector_function(selector.selector)

            elif selector.type == PICKFIRST:  # /
                fs = [_build_selector_function(s) for s in selector.selector]

                def selector_function(ctx):
                    for f in fs:
                        picked_formats = list(f(ctx))
                        if picked_formats:
                            return picked_formats
                    return []

            elif selector.type == MERGE:  # +
                selector_1, selector_2 = map(_build_selector_function, selector.selector)

                def selector_function(ctx):
                    for pair in itertools.product(
                            selector_1(copy.deepcopy(ctx)), selector_2(copy.deepcopy(ctx))):
                        yield _merge(pair)

            elif selector.type == SINGLE:  # atom
                format_spec = selector.selector or 'best'

                # TODO: Add allvideo, allaudio etc by generalizing the code with best/worst selector
                if format_spec == 'all':
                    def selector_function(ctx):
                        yield from _check_formats(ctx['formats'])
                elif format_spec == 'mergeall':
                    def selector_function(ctx):
                        formats = list(_check_formats(ctx['formats']))
                        if not formats:
                            return
                        merged_format = formats[-1]
                        for f in formats[-2::-1]:
                            merged_format = _merge((merged_format, f))
                        yield merged_format

                else:
                    format_fallback, format_reverse, format_idx = False, True, 1
                    mobj = re.match(
                        r'(?P<bw>best|worst|b|w)(?P<type>video|audio|v|a)?(?P<mod>\*)?(?:\.(?P<n>[1-9]\d*))?$',
                        format_spec)
                    if mobj is not None:
                        format_idx = int_or_none(mobj.group('n'), default=1)
                        format_reverse = mobj.group('bw')[0] == 'b'
                        format_type = (mobj.group('type') or [None])[0]
                        not_format_type = {'v': 'a', 'a': 'v'}.get(format_type)
                        format_modified = mobj.group('mod') is not None

                        format_fallback = not format_type and not format_modified  # for b, w
                        _filter_f = (
                            (lambda f: f.get('%scodec' % format_type) != 'none')
                            if format_type and format_modified  # bv*, ba*, wv*, wa*
                            else (lambda f: f.get('%scodec' % not_format_type) == 'none')
                            if format_type  # bv, ba, wv, wa
                            else (lambda f: f.get('vcodec') != 'none' and f.get('acodec') != 'none')
                            if not format_modified  # b, w
                            else lambda f: True)  # b*, w*
                        filter_f = lambda f: _filter_f(f) and (
                            f.get('vcodec') != 'none' or f.get('acodec') != 'none')
                    else:
                        if format_spec in self._format_selection_exts['audio']:
                            filter_f = lambda f: f.get('ext') == format_spec and f.get('acodec') != 'none'
                        elif format_spec in self._format_selection_exts['video']:
                            filter_f = lambda f: f.get('ext') == format_spec and f.get('acodec') != 'none' and f.get('vcodec') != 'none'
                        elif format_spec in self._format_selection_exts['storyboards']:
                            filter_f = lambda f: f.get('ext') == format_spec and f.get('acodec') == 'none' and f.get('vcodec') == 'none'
                        else:
                            filter_f = lambda f: f.get('format_id') == format_spec  # id

                    def selector_function(ctx):
                        formats = list(ctx['formats'])
                        matches = list(filter(filter_f, formats)) if filter_f is not None else formats
                        if format_fallback and ctx['incomplete_formats'] and not matches:
                            # for extractors with incomplete formats (audio only (soundcloud)
                            # or video only (imgur)) best/worst will fallback to
                            # best/worst {video,audio}-only format
                            matches = formats
                        matches = LazyList(_check_formats(matches[::-1 if format_reverse else 1]))
                        try:
                            yield matches[format_idx - 1]
                        except IndexError:
                            return

            filters = [self._build_format_filter(f) for f in selector.filters]

            def final_selector(ctx):
                ctx_copy = copy.deepcopy(ctx)
                for _filter in filters:
                    ctx_copy['formats'] = list(filter(_filter, ctx_copy['formats']))
                return selector_function(ctx_copy)
            return final_selector

        stream = io.BytesIO(format_spec.encode('utf-8'))
        try:
            tokens = list(_remove_unused_ops(compat_tokenize_tokenize(stream.readline)))
        except tokenize.TokenError:
            raise syntax_error('Missing closing/opening brackets or parenthesis', (0, len(format_spec)))

        class TokenIterator(object):
            def __init__(self, tokens):
                self.tokens = tokens
                self.counter = 0

            def __iter__(self):
                return self

            def __next__(self):
                if self.counter >= len(self.tokens):
                    raise StopIteration()
                value = self.tokens[self.counter]
                self.counter += 1
                return value

            next = __next__

            def restore_last_token(self):
                self.counter -= 1

        parsed_selector = _parse_format_selection(iter(TokenIterator(tokens)))
        return _build_selector_function(parsed_selector)

    def _calc_headers(self, info_dict):
        res = std_headers.copy()

        add_headers = info_dict.get('http_headers')
        if add_headers:
            res.update(add_headers)

        if 'X-Forwarded-For' not in res:
            x_forwarded_for_ip = info_dict.get('__x_forwarded_for_ip')
            if x_forwarded_for_ip:
                res['X-Forwarded-For'] = x_forwarded_for_ip

        return res

    def _sanitize_thumbnails(self, info_dict):
        thumbnails = info_dict.get('thumbnails')
        if thumbnails is None:
            thumbnail = info_dict.get('thumbnail')
            if thumbnail:
                info_dict['thumbnails'] = thumbnails = [{'url': thumbnail}]
        if thumbnails:
            thumbnails.sort(key=lambda t: (
                t.get('preference') if t.get('preference') is not None else -1,
                t.get('width') if t.get('width') is not None else -1,
                t.get('height') if t.get('height') is not None else -1,
                t.get('id') if t.get('id') is not None else '',
                t.get('url')))

            def thumbnail_tester():
                if self.params.get('check_formats'):
                    test_all = True
                    to_screen = lambda msg: self.to_screen(f'[info] {msg}')
                else:
                    test_all = False
                    to_screen = self.write_debug

                def test_thumbnail(t):
                    if not test_all and not t.get('_test_url'):
                        return True
                    to_screen('Testing thumbnail %s' % t['id'])
                    try:
                        self.urlopen(HEADRequest(t['url']))
                    except network_exceptions as err:
                        to_screen('Unable to connect to thumbnail %s URL "%s" - %s. Skipping...' % (
                            t['id'], t['url'], error_to_compat_str(err)))
                        return False
                    return True

                return test_thumbnail

            for i, t in enumerate(thumbnails):
                if t.get('id') is None:
                    t['id'] = '%d' % i
                if t.get('width') and t.get('height'):
                    t['resolution'] = '%dx%d' % (t['width'], t['height'])
                t['url'] = sanitize_url(t['url'])

            if self.params.get('check_formats') is not False:
                info_dict['thumbnails'] = LazyList(filter(thumbnail_tester(), thumbnails[::-1])).reverse()
            else:
                info_dict['thumbnails'] = thumbnails

    def process_video_result(self, info_dict, download=True):
        assert info_dict.get('_type', 'video') == 'video'

        if 'id' not in info_dict:
            raise ExtractorError('Missing "id" field in extractor result')
        if 'title' not in info_dict:
            raise ExtractorError('Missing "title" field in extractor result',
                                 video_id=info_dict['id'], ie=info_dict['extractor'])

        def report_force_conversion(field, field_not, conversion):
            self.report_warning(
                '"%s" field is not %s - forcing %s conversion, there is an error in extractor'
                % (field, field_not, conversion))

        def sanitize_string_field(info, string_field):
            field = info.get(string_field)
            if field is None or isinstance(field, compat_str):
                return
            report_force_conversion(string_field, 'a string', 'string')
            info[string_field] = compat_str(field)

        def sanitize_numeric_fields(info):
            for numeric_field in self._NUMERIC_FIELDS:
                field = info.get(numeric_field)
                if field is None or isinstance(field, compat_numeric_types):
                    continue
                report_force_conversion(numeric_field, 'numeric', 'int')
                info[numeric_field] = int_or_none(field)

        sanitize_string_field(info_dict, 'id')
        sanitize_numeric_fields(info_dict)

        if 'playlist' not in info_dict:
            # It isn't part of a playlist
            info_dict['playlist'] = None
            info_dict['playlist_index'] = None

        self._sanitize_thumbnails(info_dict)

        thumbnail = info_dict.get('thumbnail')
        thumbnails = info_dict.get('thumbnails')
        if thumbnail:
            info_dict['thumbnail'] = sanitize_url(thumbnail)
        elif thumbnails:
            info_dict['thumbnail'] = thumbnails[-1]['url']

        if info_dict.get('display_id') is None and 'id' in info_dict:
            info_dict['display_id'] = info_dict['id']

        for ts_key, date_key in (
                ('timestamp', 'upload_date'),
                ('release_timestamp', 'release_date'),
        ):
            if info_dict.get(date_key) is None and info_dict.get(ts_key) is not None:
                # Working around out-of-range timestamp values (e.g. negative ones on Windows,
                # see http://bugs.python.org/issue1646728)
                try:
                    upload_date = datetime.datetime.utcfromtimestamp(info_dict[ts_key])
                    info_dict[date_key] = upload_date.strftime('%Y%m%d')
                except (ValueError, OverflowError, OSError):
                    pass

        live_keys = ('is_live', 'was_live')
        live_status = info_dict.get('live_status')
        if live_status is None:
            for key in live_keys:
                if info_dict.get(key) is False:
                    continue
                if info_dict.get(key):
                    live_status = key
                break
            if all(info_dict.get(key) is False for key in live_keys):
                live_status = 'not_live'
        if live_status:
            info_dict['live_status'] = live_status
            for key in live_keys:
                if info_dict.get(key) is None:
                    info_dict[key] = (live_status == key)

        # Auto generate title fields corresponding to the *_number fields when missing
        # in order to always have clean titles. This is very common for TV series.
        for field in ('chapter', 'season', 'episode'):
            if info_dict.get('%s_number' % field) is not None and not info_dict.get(field):
                info_dict[field] = '%s %d' % (field.capitalize(), info_dict['%s_number' % field])

        for cc_kind in ('subtitles', 'automatic_captions'):
            cc = info_dict.get(cc_kind)
            if cc:
                for _, subtitle in cc.items():
                    for subtitle_format in subtitle:
                        if subtitle_format.get('url'):
                            subtitle_format['url'] = sanitize_url(subtitle_format['url'])
                        if subtitle_format.get('ext') is None:
                            subtitle_format['ext'] = determine_ext(subtitle_format['url']).lower()

        automatic_captions = info_dict.get('automatic_captions')
        subtitles = info_dict.get('subtitles')

        # We now pick which formats have to be downloaded
        if info_dict.get('formats') is None:
            # There's only one format available
            formats = [info_dict]
        else:
            formats = info_dict['formats']

        info_dict['__has_drm'] = any(f.get('has_drm') for f in formats)
        if not self.params.get('allow_unplayable_formats'):
            formats = [f for f in formats if not f.get('has_drm')]

        if not formats:
            self.raise_no_formats(info_dict)

        def is_wellformed(f):
            url = f.get('url')
            if not url:
                self.report_warning(
                    '"url" field is missing or empty - skipping format, '
                    'there is an error in extractor')
                return False
            if isinstance(url, bytes):
                sanitize_string_field(f, 'url')
            return True

        # Filter out malformed formats for better extraction robustness
        formats = list(filter(is_wellformed, formats))

        formats_dict = {}

        # We check that all the formats have the format and format_id fields
        for i, format in enumerate(formats):
            sanitize_string_field(format, 'format_id')
            sanitize_numeric_fields(format)
            format['url'] = sanitize_url(format['url'])
            if not format.get('format_id'):
                format['format_id'] = compat_str(i)
            else:
                # Sanitize format_id from characters used in format selector expression
                format['format_id'] = re.sub(r'[\s,/+\[\]()]', '_', format['format_id'])
            format_id = format['format_id']
            if format_id not in formats_dict:
                formats_dict[format_id] = []
            formats_dict[format_id].append(format)

        # Make sure all formats have unique format_id
        common_exts = set(itertools.chain(*self._format_selection_exts.values()))
        for format_id, ambiguous_formats in formats_dict.items():
            ambigious_id = len(ambiguous_formats) > 1
            for i, format in enumerate(ambiguous_formats):
                if ambigious_id:
                    format['format_id'] = '%s-%d' % (format_id, i)
                if format.get('ext') is None:
                    format['ext'] = determine_ext(format['url']).lower()
                # Ensure there is no conflict between id and ext in format selection
                # See https://github.com/yt-dlp/yt-dlp/issues/1282
                if format['format_id'] != format['ext'] and format['format_id'] in common_exts:
                    format['format_id'] = 'f%s' % format['format_id']

        for i, format in enumerate(formats):
            if format.get('format') is None:
                format['format'] = '{id} - {res}{note}'.format(
                    id=format['format_id'],
                    res=self.format_resolution(format),
                    note=format_field(format, 'format_note', ' (%s)'),
                )
            # Add HTTP headers, so that external programs can use them from the
            # json output
            full_format_info = info_dict.copy()
            full_format_info.update(format)
            format['http_headers'] = self._calc_headers(full_format_info)
        # Remove private housekeeping stuff
        if '__x_forwarded_for_ip' in info_dict:
            del info_dict['__x_forwarded_for_ip']

        # TODO Central sorting goes here

        if not formats or formats[0] is not info_dict:
            # only set the 'formats' fields if the original info_dict list them
            # otherwise we end up with a circular reference, the first (and unique)
            # element in the 'formats' field in info_dict is info_dict itself,
            # which can't be exported to json
            info_dict['formats'] = formats

        info_dict, _ = self.pre_process(info_dict)

        if self.params.get('list_thumbnails'):
            self.list_thumbnails(info_dict)
        if self.params.get('listformats'):
            if not info_dict.get('formats') and not info_dict.get('url'):
                self.to_screen('%s has no formats' % info_dict['id'])
            else:
                self.list_formats(info_dict)
        if self.params.get('listsubtitles'):
            if 'automatic_captions' in info_dict:
                self.list_subtitles(
                    info_dict['id'], automatic_captions, 'automatic captions')
            self.list_subtitles(info_dict['id'], subtitles, 'subtitles')
        list_only = self.params.get('simulate') is None and (
            self.params.get('list_thumbnails') or self.params.get('listformats') or self.params.get('listsubtitles'))
        if list_only:
            # Without this printing, -F --print-json will not work
            self.__forced_printings(info_dict, self.prepare_filename(info_dict), incomplete=True)
            return

        format_selector = self.format_selector
        if format_selector is None:
            req_format = self._default_format_spec(info_dict, download=download)
            self.write_debug('Default format spec: %s' % req_format)
            format_selector = self.build_format_selector(req_format)

        # While in format selection we may need to have an access to the original
        # format set in order to calculate some metrics or do some processing.
        # For now we need to be able to guess whether original formats provided
        # by extractor are incomplete or not (i.e. whether extractor provides only
        # video-only or audio-only formats) for proper formats selection for
        # extractors with such incomplete formats (see
        # https://github.com/ytdl-org/youtube-dl/pull/5556).
        # Since formats may be filtered during format selection and may not match
        # the original formats the results may be incorrect. Thus original formats
        # or pre-calculated metrics should be passed to format selection routines
        # as well.
        # We will pass a context object containing all necessary additional data
        # instead of just formats.
        # This fixes incorrect format selection issue (see
        # https://github.com/ytdl-org/youtube-dl/issues/10083).
        incomplete_formats = (
            # All formats are video-only or
            all(f.get('vcodec') != 'none' and f.get('acodec') == 'none' for f in formats)
            # all formats are audio-only
            or all(f.get('vcodec') == 'none' and f.get('acodec') != 'none' for f in formats))

        ctx = {
            'formats': formats,
            'incomplete_formats': incomplete_formats,
        }

        formats_to_download = list(format_selector(ctx))
        if not formats_to_download:
            if not self.params.get('ignore_no_formats_error'):
                raise ExtractorError('Requested format is not available', expected=True,
                                     video_id=info_dict['id'], ie=info_dict['extractor'])
            else:
                self.report_warning('Requested format is not available')
                # Process what we can, even without any available formats.
                self.process_info(dict(info_dict))
        elif download:
            self.to_screen(
                '[info] %s: Downloading %d format(s): %s' % (
                    info_dict['id'], len(formats_to_download),
                    ", ".join([f['format_id'] for f in formats_to_download])))
            for fmt in formats_to_download:
                new_info = dict(info_dict)
                # Save a reference to the original info_dict so that it can be modified in process_info if needed
                new_info['__original_infodict'] = info_dict
                new_info.update(fmt)
                self.process_info(new_info)
        # We update the info dict with the best quality format (backwards compatibility)
        if formats_to_download:
            info_dict.update(formats_to_download[-1])
        return info_dict

    def __forced_printings(self, info_dict, filename, incomplete):
        def print_mandatory(field, actual_field=None):
            if actual_field is None:
                actual_field = field
            if (self.params.get('force%s' % field, False)
                    and (not incomplete or info_dict.get(actual_field) is not None)):
                self.to_stdout(info_dict[actual_field])

        info_dict = info_dict.copy()
        if filename is not None:
            info_dict['filename'] = filename
        if info_dict.get('requested_formats') is not None:
            # For RTMP URLs, also include the playpath
            info_dict['urls'] = '\n'.join(f['url'] + f.get('play_path', '') for f in info_dict['requested_formats'])
        elif 'url' in info_dict:
            info_dict['urls'] = info_dict['url'] + info_dict.get('play_path', '')

        print_mandatory('title')
        print_mandatory('id')
        print_mandatory('url', 'urls')
        print_mandatory('format')

        if self.params.get('forcejson'):
            self.to_stdout(json.dumps(self.sanitize_info(info_dict)))

    def process_info(self, info_dict):
        """Process a single resolved IE result."""

        assert info_dict.get('_type', 'video') == 'video'

        max_downloads = self.params.get('max_downloads')
        if max_downloads is not None:
            if self._num_downloads >= int(max_downloads):
                raise MaxDownloadsReached()

        # TODO: backward compatibility, to be removed
        info_dict['fulltitle'] = info_dict['title']

        if 'format' not in info_dict and 'ext' in info_dict:
            info_dict['format'] = info_dict['ext']

        if self._match_entry(info_dict) is not None:
            return

        self.post_extract(info_dict)
        self._num_downloads += 1

        # info_dict['_filename'] needs to be set for backward compatibility
        #info_dict['_filename'] = full_filename = self.prepare_filename(info_dict, warn=True)
        #temp_filename = self.prepare_filename(info_dict, 'temp')
        files_to_move = {}

        # Forced printings
        self.__forced_printings(info_dict, 'full_filename', incomplete=('format' not in info_dict))

        if self.params.get('simulate'):
            if self.params.get('force_write_download_archive', False):
                self.record_download_archive(info_dict)
            # Do nothing else if in simulate mode
            return

        try:
            info_dict, files_to_move = self.pre_process(info_dict, 'before_dl', files_to_move)
        except PostProcessingError as err:
            self.report_error('Preprocessing: %s' % str(err))
            return

        max_downloads = self.params.get('max_downloads')
        if max_downloads is not None and self._num_downloads >= int(max_downloads):
            raise MaxDownloadsReached()

    def download(self, url_list):
        """Download a given list of URLs."""
        for url in url_list:
            try:
                # It also downloads the videos
                res = self.extract_info(
                    url, force_generic_extractor=self.params.get('force_generic_extractor', False))
            except UnavailableVideoError:
                self.report_error('unable to download video')
            except MaxDownloadsReached:
                self.to_screen('[info] Maximum number of downloads reached')
                raise
            except ExistingVideoReached:
                self.to_screen('[info] Encountered a video that is already in the archive, stopping due to --break-on-existing')
                raise
            except RejectedVideoReached:
                self.to_screen('[info] Encountered a video that did not match filter, stopping due to --break-on-reject')
                raise
            else:
                if self.params.get('dump_single_json', False):
                    self.post_extract(res)
                    self.to_stdout(json.dumps(self.sanitize_info(res)))

        return self._download_retcode

    @staticmethod
    def sanitize_info(info_dict, remove_private_keys=False):
        ''' Sanitize the infodict for converting to json '''
        if info_dict is None:
            return info_dict
        info_dict.setdefault('epoch', int(time.time()))
        remove_keys = {'__original_infodict'}  # Always remove this since this may contain a copy of the entire dict
        keep_keys = ['_type'],  # Always keep this to facilitate load-info-json
        if remove_private_keys:
            remove_keys |= {
                'requested_formats', 'requested_subtitles', 'requested_entries',
                'filepath', 'entries', 'original_url', 'playlist_autonumber',
            }
            empty_values = (None, {}, [], set(), tuple())
            reject = lambda k, v: k not in keep_keys and (
                k.startswith('_') or k in remove_keys or v in empty_values)
        else:
            reject = lambda k, v: k in remove_keys
        filter_fn = lambda obj: (
            list(map(filter_fn, obj)) if isinstance(obj, (LazyList, list, tuple, set))
            else obj if not isinstance(obj, dict)
            else dict((k, filter_fn(v)) for k, v in obj.items() if not reject(k, v)))
        return filter_fn(info_dict)

    @staticmethod
    def filter_requested_info(info_dict, actually_filter=True):
        ''' Alias of sanitize_info for backward compatibility '''
        return YoutubeDL.sanitize_info(info_dict, actually_filter)

    @staticmethod
    def post_extract(info_dict):
        def actual_post_extract(info_dict):
            if info_dict.get('_type') in ('playlist', 'multi_video'):
                for video_dict in info_dict.get('entries', {}):
                    actual_post_extract(video_dict or {})
                return

            post_extractor = info_dict.get('__post_extractor') or (lambda: {})
            extra = post_extractor().items()
            info_dict.update(extra)
            info_dict.pop('__post_extractor', None)

            original_infodict = info_dict.get('__original_infodict') or {}
            original_infodict.update(extra)
            original_infodict.pop('__post_extractor', None)

        actual_post_extract(info_dict or {})

    def pre_process(self, ie_info, key='pre_process', files_to_move=None):
        info = dict(ie_info)
        info['__files_to_move'] = files_to_move or {}
        for pp in self._pps[key]:
            info = self.run_pp(pp, info)
        return info, info.pop('__files_to_move', None)

    def _make_archive_id(self, info_dict):
        video_id = info_dict.get('id')
        if not video_id:
            return
        # Future-proof against any change in case
        # and backwards compatibility with prior versions
        extractor = info_dict.get('extractor_key') or info_dict.get('ie_key')  # key in a playlist
        if extractor is None:
            url = str_or_none(info_dict.get('url'))
            if not url:
                return
            # Try to find matching extractor for the URL and take its ie_key
            for ie_key, ie in self._ies.items():
                if ie.suitable(url):
                    extractor = ie_key
                    break
            else:
                return
        return '%s %s' % (extractor.lower(), video_id)

    @staticmethod
    def format_resolution(format, default='unknown'):
        is_images = format.get('vcodec') == 'none' and format.get('acodec') == 'none'
        if format.get('vcodec') == 'none' and format.get('acodec') != 'none':
            return 'audio only'
        if format.get('resolution') is not None:
            return format['resolution']
        if format.get('width') and format.get('height'):
            res = '%dx%d' % (format['width'], format['height'])
        elif format.get('height'):
            res = '%sp' % format['height']
        elif format.get('width'):
            res = '%dx?' % format['width']
        elif is_images:
            return 'images'
        else:
            return default
        return f'{res} images' if is_images else res

    def urlopen(self, req):
        """ Start an HTTP download """
        if isinstance(req, compat_basestring):
            req = sanitized_Request(req)
        return self._opener.open(req, timeout=self._socket_timeout)

    def _setup_opener(self):
        timeout_val = self.params.get('socket_timeout')
        self._socket_timeout = 600 if timeout_val is None else float(timeout_val)

        opts_proxy = self.params.get('proxy')

        cookie_processor = YoutubeDLCookieProcessor(None)
        if opts_proxy is not None:
            if opts_proxy == '':
                proxies = {}
            else:
                proxies = {'http': opts_proxy, 'https': opts_proxy}
        else:
            proxies = compat_urllib_request.getproxies()
            # Set HTTPS proxy to HTTP one if given (https://github.com/ytdl-org/youtube-dl/issues/805)
            if 'http' in proxies and 'https' not in proxies:
                proxies['https'] = proxies['http']
        proxy_handler = PerRequestProxyHandler(proxies)

        debuglevel = 1 if self.params.get('debug_printtraffic') else 0
        https_handler = make_HTTPS_handler(self.params, debuglevel=debuglevel)
        ydlh = YoutubeDLHandler(self.params, debuglevel=debuglevel)
        redirect_handler = YoutubeDLRedirectHandler()
        data_handler = compat_urllib_request_DataHandler()

        # When passing our own FileHandler instance, build_opener won't add the
        # default FileHandler and allows us to disable the file protocol, which
        # can be used for malicious purposes (see
        # https://github.com/ytdl-org/youtube-dl/issues/8227)
        file_handler = compat_urllib_request.FileHandler()

        def file_open(*args, **kwargs):
            raise compat_urllib_error.URLError('file:// scheme is explicitly disabled in yt-dlp for security reasons')
        file_handler.file_open = file_open

        opener = compat_urllib_request.build_opener(
            proxy_handler, https_handler, cookie_processor, ydlh, redirect_handler, data_handler, file_handler)

        # Delete the default user-agent header, which would otherwise apply in
        # cases where our custom HTTP handler doesn't come into play
        # (See https://github.com/ytdl-org/youtube-dl/issues/1309 for details)
        opener.addheaders = []
        self._opener = opener
