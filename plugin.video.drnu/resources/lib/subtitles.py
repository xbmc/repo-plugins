#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""WebVTT to SRT subtitle conversion and subtitle file handling."""

import re
from pathlib import Path
from typing import Any, Callable, Optional, Union

import requests

LOCAL_SUBTITLE_LANGUAGES = ['DanishLanguageSubtitles', 'CombinedLanguageSubtitles']


def vtt2srt(vtt: Union[str, bytes]) -> str:
    """Convert a WebVTT subtitle (str or bytes) to SRT format."""
    if isinstance(vtt, bytes):
        vtt = vtt.decode('utf-8')
    srt = vtt.replace("\r\n", "\n")
    srt = re.sub(r'([\d]+)\.([\d]+)', r'\1,\2', srt)
    srt = re.sub(r'WEBVTT\n\n', '', srt)
    srt = re.sub(r'^\d+\n', '', srt)
    srt = re.sub(r'\n\d+\n', '\n', srt)
    srt = re.sub(r'\n([\d]+)', r'\nputINDEXhere\n\1', srt)

    srtout = ['1']
    idx = 2
    for line in srt.splitlines():
        if line == 'putINDEXhere':
            line = str(idx)
            idx += 1
        srtout.append(line)
    return '\n'.join(srtout)


def handle_subtitle_vtts(subs: list[dict], cache_path: Path, tr_func: Callable[[int], str], session: Any) -> dict[str, str]:
    """Download subtitle VTTs and store them as local SRT files.

    Returns a mapping from subtitle language to the written SRT file path: a
    caller must select by language, not by position, because a subtitle whose
    download fails is skipped and a positional list would then point at the
    wrong language. A subtitle that fails to download or write is skipped:
    playback must not be stopped by a subtitle error, since the video can
    still fall back to embedded subtitles.
    """
    subtitles_uri = {}
    for sub in subs:
        language = sub['language']
        tr_id = 30050 if language in LOCAL_SUBTITLE_LANGUAGES else 30051
        name = f'{cache_path}/{tr_func(tr_id)}.da.srt'
        try:
            u = session.get(sub['link'], timeout=10)
            try:
                if u.status_code != 200:
                    continue
                srt = vtt2srt(u.content)
            finally:
                u.close()
            with open(name, 'wb') as fh:
                fh.write(srt.encode('utf-8'))
        except (OSError, requests.RequestException):
            continue
        subtitles_uri[language] = name
    return subtitles_uri


def resolve_subtitle_action(settings: dict, subs: dict, kids_channel: bool,
                            local_subtitles: dict[str, str]) -> tuple[Optional[str], Optional[Union[int, str]]]:
    """Decide which subtitle action to take once playback has started.

    settings holds the relevant addon settings (disable.kids.subtitles,
    enable.subtitles, enable.localsubtitles, inputstream), subs maps subtitle
    language codes to their embedded stream index and local_subtitles maps
    language codes to locally downloaded SRT files.

    Returns one of:
        ('off', None)          hide subtitles
        ('stream', index)      enable embedded subtitle stream at index
        ('local', file_path)   enable local SRT file at file_path
        (None, None)           leave subtitles untouched
    """
    local_subs = settings['enable.localsubtitles'] or settings['inputstream'] == 1
    if settings['disable.kids.subtitles'] and kids_channel:
        return ('off', None)
    if settings['enable.subtitles']:
        # hard-of-hearing: prefer the local file, then the embedded stream, in
        # language priority order
        for language in ['DanishLanguageSubtitles', 'CombinedLanguageSubtitles', 'ForeignLanguageSubtitles']:
            if local_subs and language in local_subtitles:
                return ('local', local_subtitles[language])
            if language in subs:
                return ('stream', subs[language])
        return (None, None)
    if 'ForeignLanguageSubtitles' in subs:
        # hard-of-hearing off: show the foreign translation, which must be the
        # foreign file/stream even when only the Danish subtitle was downloaded
        if local_subs and 'ForeignLanguageSubtitles' in local_subtitles:
            return ('local', local_subtitles['ForeignLanguageSubtitles'])
        return ('stream', subs['ForeignLanguageSubtitles'])
    return ('off', None)
