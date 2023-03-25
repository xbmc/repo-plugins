
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import logging
import os
import re
import time
from datetime import datetime

import xbmc
import xbmcaddon
from xbmcvfs import translatePath

from codequick.support import logger_id


logger = logging.getLogger('.'.join((logger_id, 'ct_utils')))


def create_addon_info(addon_id=None):
    if addon_id:
        addon = xbmcaddon.Addon(addon_id)
    else:
        addon = xbmcaddon.Addon()
    info = {
        "name": addon.getAddonInfo("name"),
        "id": addon.getAddonInfo("id"),
        "addon": addon,
        "version": addon.getAddonInfo("version"),
        "path": addon.getAddonInfo("path"),
        "profile": translatePath(addon.getAddonInfo('profile'))
    }
    os.makedirs(info['profile'], exist_ok=True)
    return info


addon_info = create_addon_info()


try:
    kodi_vers_major = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
except ValueError:
    kodi_vers_major = 19


def get_os():
    os_type = os.environ.get("OS", "unknown")
    return os_type


def get_subtitles_temp_file():
    tmp_dir = os.path.join(addon_info['profile'], 'subtitles')
    os.makedirs(tmp_dir, exist_ok=True)
    return os.path.join(tmp_dir, 'subtitles.srt')


def random_string(length):
    """Return a string of random upper and lowercase characters and numbers"""
    import random
    import string

    chars = string.ascii_letters + string.digits
    result = ''.join((random.choice(chars) for _ in range(length)))
    return result


def duration_2_seconds(duration: str):
    """Convert strings like '123', '120 min', 3.18, 03:09, or '1:03:00' to the
    corresponding number of seconds.

    """
    try:
        # a duration in a format of: '120 min'.
        splits = duration.split()
        if len(splits) > 1:
            if splits[1] == 'min':
                return int(splits[0]) * 60
            else:
                logger.warning("Unknown duration format '%s': expected 'xx min'", duration)
                return None

        # duration in a format of '3:14', or '1:32:46', or '172.5' (which is 172 minutes, 30 seconds).
        splits = duration.split(':')
        if len(splits) == 1:
            return int(float(duration) * 60)
        if len(splits) == 2:
            return int(splits[0]) * 60 + int(splits[1])
        if len(splits) == 3:
            return int(splits[0]) * 3600 + int(splits[1]) * 60 + int(splits[2])
        else:
            logger.warning("Unknown duration format '%s'", duration)

    except (ValueError, AttributeError) as e:
        logger.debug("Failed to convert duration to seconds for string '%s': %r", duration, e)
    return None


def reformat_date(date_string: str, old_format: str, new_format: str) -> str:
    """Take a string containing a datetime and in a particular format and
    convert it into another format.

    Usually used to convert timestamps obtained from a website into a nice readable format.

    """
    try:
        dt = datetime.strptime(date_string, old_format)
    except TypeError:
        dt = datetime(*(time.strptime(date_string, old_format)[:6]))
    return dt.strftime(new_format)


def vtt_to_srt(vtt_doc: str) -> str:
    """Convert a string containing subtitles in vtt format into srt format.

    Very simple that does not expect much styling, position or colours and tries
    to ignore most fancy vtt stuff. But seems to be enough for Cinetree films.

    All styling, except bold, italic and underline defined by HTML text in the cue payload is
    removed, as well as position information.

    """
    from io import StringIO

    # Match a line that start with cue timings. Accept timings with or without hours.
    regex = re.compile(r'(\d{2})?:?(\d{2}:\d{2})\.(\d{3}) +--> +(\d{2})?:?(\d{2}:\d{2})\.(\d{3})')

    # Convert new lines conform WebVTT specs
    vtt_doc = vtt_doc.replace('\r\n', '\n')
    vtt_doc = vtt_doc.replace('\r', '\n')

    # Split the document into blocks that are separated by an empty line.
    vtt_blocks = vtt_doc.split('\n\n')
    seq_nr = 0

    with StringIO() as f:
        for block in vtt_blocks:
            lines = iter(block.split('\n'))

            # Find cue timings, ignore all cue settings.
            try:
                line = next(lines)
                timings_match = regex.match(line)
                if not timings_match:
                    # The first line may be a cue identifier
                    line = next(lines)
                    timings_match = regex.match(line)
                    if not timings_match:
                        # Also no timings in the second line: this is not a cue block
                        continue
            except StopIteration:
                # Not enough lines to find timings: this is not a cue block
                continue

            # Write newline and sequence number
            seq_nr += 1
            f.write('\n{}\n'.format(seq_nr))
            # Write cue timings, add "00" for missing hours.
            f.write('{}:{},{} --> {}:{},{}\n'.format(*timings_match.groups('00')))
            # Write out the lines of the cue payload
            for line in lines:
                f.write(line + '\n')

        srt_doc = f.getvalue()
        # Remove any markup tag other than the supported bold, italic and underline.
        srt_doc = re.sub(r'<([^biu]).*?>(.*)</\1.*?>', r'\2', srt_doc)
    return srt_doc


def replace_markdown(markdown_text):
    """Simpel and basic converter of markdown to kodi tags; just enough to make texts
    from Cinetree presentable.

    Bold an italic markdown will be converted to their respective Kodi equivalent.
    Markdown hyperlinks will collaps to the link text only. Escaped markdown is unescaped.

    """
    if not markdown_text:
        return markdown_text

    try:
        # Replace hyperlinks by the link text.
        # NOTE:
        #     Doesn't handle escaped block bracket at the start of the match, but the pattern itself
        #     should be unique enough for practical use.
        markdown_text = re.sub(r'\[((?:\\]|[^]])+)]\(.+?\)', r'\1', markdown_text, flags=re.DOTALL)

        # Replace bold, accept Markdown formatting with stars (**) wel as underscores (__)
        #
        # Rather complex regexes to find parts of string enclosed in markdown , i.e. enclosed
        # in either '*' or '_' characters for italics, or '**', '__' for bold.
        # The regex allows for backslash escapes of both markdown and backslashes themselves.

        # (?:(?<=\\\\)|(?<!\\)) The match must be preceded by: either a character that is not '\',
        #                       or an escaped '\'
        # (?P<md>\*\*|__) The match must start with '**' or '__
        # ((?:\\[\\*_]|.)+?) what follows is either an escaped  '\', '*', or '_',
        #                    or any other single character and capture that one or more times
        # (?P=md) It must end with the same sequence of '**' or '__' that it started with.
        markdown_text = re.sub(r'(?:(?<!\\)|(?<=\\\\))(?P<md>\*\*|__)((?:\\[\\*_]|.)+?)(?P=md)',
                               r'[B]\2[/B]',
                               markdown_text,
                               flags=re.DOTALL)

        # replace italic
        markdown_text = re.sub(r'(?:(?<!\\)|(?<=\\\\))(?P<md>[*_])((?:\\[\\*_]|.)+?)(?P=md)',
                               r'[I]\2[/I]',
                               markdown_text,
                               flags=re.DOTALL)

        # Unescape escaped markup characters '*' '_' '[', ']'and '\'.
        markdown_text = re.sub(r'\\([*_\\[\]])', r'\1', markdown_text)
    except TypeError:
        markdown_text = ''
    return markdown_text


def replace_markdown_from_quoted_strings(src_text):
    """Scan src_text for parts within double quotes and replace markdown in these parts.
    Everything not in double quotes is left as is.

    """
    def repl(match):
        new_str = replace_markdown(match.group(0))
        return new_str

    # Capture everything enclosed in double quotes, but ignore escaped double quotes.
    new_text = re.sub(r'\"(?:\\"|[^\"])*\"', repl, src_text, flags=re.MULTILINE)
    return new_text


def remove_markdown(src_text):
    """Completely remove all markdown and return a plain text

    """
    if not src_text:
        return src_text

    try:
        # remove hyperlinks
        src_text = re.sub(r'\[((?:\\]|[^]])+)]\(.+?\)', r'\1', src_text, flags=re.DOTALL)
        # remove every not escaped '#', '*' or '_'
        src_text = re.sub(r'(?:(?<!\\)|(?<=\\\\))[*_#]+', r'', src_text,)

        # Unescape escaped markup characters '*' '_' '[', ']'and '\'.
        src_text = re.sub(r'\\([*_\\[\]])', r'\1', src_text)
    except TypeError:
        src_text = ''
    return src_text
