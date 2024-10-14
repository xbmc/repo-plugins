#!/usr/bin/env python3
# coding: utf-8

f'You are using an unsupported version of Python. Only Python versions 3.6 and above are supported by yt-dlp'  # noqa: F541

__license__ = 'Public Domain'

import codecs
import os
import sys

from .options import (
    parseOpts,
)
from .compat import (
    workaround_optparse_bug9161,
)
from .utils import (
    DownloadError,
    error_to_compat_str,
    ExistingVideoReached,
    MaxDownloadsReached,
    preferredencoding,
    RejectedVideoReached,
    SameFileError,
)
from .extractor import gen_extractors, list_extractors

from .YoutubeDL import YoutubeDL


def _real_main(argv=None):
    # Compatibility fixes for Windows
    if sys.platform == 'win32':
        # https://github.com/ytdl-org/youtube-dl/issues/820
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

    workaround_optparse_bug9161()

    parser, opts, args = parseOpts(argv)
    warnings = []

    # Batch file verification
    batch_urls = []
    all_urls = batch_urls + [url.strip() for url in args]  # batch_urls are already striped in read_batch_urls
    _enc = preferredencoding()
    all_urls = [url.decode(_enc, 'ignore') if isinstance(url, bytes) else url for url in all_urls]

    def parse_retries(retries, name=''):
        if retries in ('inf', 'infinite'):
            parsed_retries = float('inf')
        else:
            try:
                parsed_retries = int(retries)
            except (TypeError, ValueError):
                parser.error('invalid %sretry count specified' % name)
        return parsed_retries

    def validate_outtmpl(tmpl, msg):
        err = YoutubeDL.validate_outtmpl(tmpl)
        if err:
            parser.error('invalid %s %r: %s' % (msg, tmpl, error_to_compat_str(err)))

    any_getting = opts.dumpjson

    def report_conflict(arg1, arg2):
        warnings.append('%s is ignored since %s was given' % (arg2, arg1))
    
    def report_args_compat(arg, name):
        warnings.append('%s given without specifying name. The arguments will be given to all %s' % (arg, name))

    final_ext = None

    ydl_opts = {
        'quiet': any_getting,
        'forcejson': opts.dumpjson,
        'logtostderr': True,
        'verbose': opts.verbose,
        'final_ext': final_ext,
        'warnings': warnings,
    }

    with YoutubeDL(ydl_opts) as ydl:
        actual_use = len(all_urls)

        # Maybe do nothing
        if not actual_use:
            ydl.warn_if_short_id(sys.argv[1:] if argv is None else argv)
            parser.error(
                'You must provide at least one URL.\n'
                'Type yt-dlp --help to see a list of all options.')

        try:
            retcode = ydl.download(all_urls)
        except (MaxDownloadsReached, ExistingVideoReached, RejectedVideoReached):
            ydl.to_screen('Aborting remaining downloads')
            retcode = 101

    sys.exit(retcode)


def main(argv=None):
    try:
        _real_main(argv)
    except DownloadError:
        sys.exit(1)
    except SameFileError as e:
        sys.exit(f'ERROR: {e}')
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')
    except BrokenPipeError as e:
        # https://docs.python.org/3/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(f'\nERROR: {e}')


__all__ = ['main', 'YoutubeDL', 'gen_extractors', 'list_extractors']
