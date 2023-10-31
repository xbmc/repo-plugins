# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

from __future__ import annotations
import logging
import time
import string
from datetime import datetime

from xbmcvfs import translatePath
import xbmcaddon

from codequick.support import logger_id


class AddonInfo:
    def __init__(self):
        self.initialise()

    # noinspection PyAttributeOutsideInit
    def initialise(self):
        self.addon = addon = xbmcaddon.Addon()
        self.name = addon.getAddonInfo("name")
        self.id = addon.getAddonInfo("id")
        self.localise = addon.getLocalizedString
        self.profile = translatePath(addon.getAddonInfo('profile'))


logger = logging.getLogger(logger_id + '.utils')
addon_info = AddonInfo()


def get_os():
    import platform
    return platform.system(), platform.machine()


def random_string(length: int) -> str:
    """Return a string of random upper and lowercase charters and numbers"""
    import random
    import string

    chars = string.ascii_letters + string.digits
    result = ''.join(random.choice(chars) for _ in range(length))
    return result


def ttml_to_srt(ttml_data, outfile):
    """Convert subtitles in XML format to a format that kodi accepts"""
    from xml.etree import ElementTree
    import re

    # Get XML namespace
    match = re.search(r'xmlns="(.*?)" ', ttml_data, re.DOTALL)
    if match:
        xmlns = ''.join(('{', match.group(1), '}'))
    else:
        xmlns = ''

    FONT_COL_WHITE = '<font color="white">'
    FONT_END_TAG = '</font>\n'

    root = ElementTree.fromstring(ttml_data)

    dflt_styles = {}
    path = ''.join(('./', xmlns, 'head', '/', xmlns, 'styling', '/', xmlns, 'style'))
    styles = root.findall(path)
    for style_def in styles:
        style_id = style_def.get(xmlns + 'id')
        colors = [value for tag, value in style_def.items() if tag.endswith('color')]
        if colors:
            col = colors[0]
            # strip possible alpha value if color is a HTML encoded RBGA value
            if col.startswith('#'):
                col = col[:7]
            dflt_styles[style_id] = ''.join(('<font color="', col, '">'))

    body = root.find(xmlns + 'body')
    if body is None:
        return

    index = 0
    # lines = []
    color_tag = "{http://www.w3.org/ns/ttml#styling}" + 'color'

    for paragraph in body.iter(xmlns + 'p'):
        index += 1

        t_start = paragraph.get('begin')
        t_end = paragraph.get('end')
        if not (t_start and t_end):
            continue
        outfile.write(str(index) + '\n')
        # convert xml time format: begin="00:03:33:14" end="00:03:36:06"
        # to srt format: 00:03:33,140 --> 00:03:36,060
        outfile.write(''.join((t_start[0:-3], ',', t_start[-2:], '0', ' --> ', t_end[0:-3], ',', t_end[-2:], '0\n')))

        p_style = paragraph.get('style')
        p_col = dflt_styles.get(p_style, FONT_COL_WHITE)
        if paragraph.text:
            outfile.write(''.join((p_col, paragraph.text, FONT_END_TAG)))
        for el in paragraph:
            if el.tag.endswith('span') and el.text:
                col = el.get(color_tag, 'white')
                # col = [v for k, v in el.items() if k.endswith('color')]
                # if col:
                outfile.write(''.join(('<font color="', col, '">', el.text, FONT_END_TAG)))
                # else:
                #     lines.append(''.join((FONT_COL_WHITE, el.text, FONT_END_TAG)))
            if el.tail:
                outfile.write(''.join((p_col, el.tail, FONT_END_TAG)))
        outfile.write('\n')


def vtt_to_srt(vtt_doc: str, colourize=True) -> str:
    """Convert a string containing subtitles in vtt format into a format kodi accepts.

    Very simple converter that does not expect much styling, position, etc. and tries
    to ignore most fancy vtt stuff. But seems to be enough for most itv subtitles.

    All styling, except bold, italic, underline and colour in the cue payload is
    removed, as well as position information.

    """
    from io import StringIO
    import re

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

    if colourize:
        # Remove any markup tag other than the supported bold, italic underline and colour.
        srt_doc = re.sub(r'<([^biuc]).*?>(.*?)</\1.*?>', r'\2', srt_doc)

        # convert color tags, accept RGB(A) colours and named colours supported by Kodi.
        def sub_color_tags(match):
            colour = match[1]
            if colour in ('white', 'yellow', 'green', 'cyan', 'red'):
                # Named colours
                return '<font color="{}">{}</font>'.format(colour, match[2])
            elif colour.startswith('color'):
                # RBG colour, ensure to strip the alpha channel if present.
                result = '<font color="#{}">{}</font>'.format(colour[5:11], match[2])
                return result
            else:
                logger.debug("Unsupported colour '%s' in vtt file", colour)
                return match[2]

        srt_doc = re.sub(r'<c\.(.*?)>(.*?)</c>', sub_color_tags, srt_doc)
    else:
        # Remove any markup tag other than the supported bold, italic underline.
        srt_doc = re.sub(r'<([^biu]).*?>(.*?)</\1.*?>', r'\2', srt_doc)
    return srt_doc


def duration_2_seconds(duration: str) -> int | None:
    """Convert a string containing duration in various formats to the corresponding number of seconds.

    supported formats:

    * '62' - single number of minutes
    * '1,32 hrs'  - hours as float
    * '78 min' - number of minutes as integer
    * '1h 35m' - hours and minutes, where both hours and minutes are optional.
    * 'PT1H32M' - ISO 8601 duration.

    """

    if not duration:
        return None

    if duration.startswith("P"):
        return iso_duration_2_seconds(duration)

    hours = 0
    minutes = 0

    try:
        splits = duration.split()
        if len(splits) == 2:
            # format  '62 min'
            if splits[1] == 'min':
                return int(splits[0]) * 60
            if splits[1] == 'hrs':
                # format '1.56 hrs'
                return int(float(splits[0]) * 3600)

        for t_str in splits:
            if t_str.endswith('h'):
                # format '2h 15m' or '2h'
                hours = int(t_str[:-1])
            elif t_str.endswith('m'):
                minutes = int(t_str[:-1])
            elif len(splits) == 1:
                # format '62'
                minutes = int(t_str)

        return int(hours) * 3600 + int(minutes) * 60

    except (ValueError, AttributeError, IndexError):
        return None


def iso_duration_2_seconds(iso_str: str) -> int | None:
    """Convert an ISO 8601 duration string into seconds.

    Simple parser to match durations found in films and tv episodes.
    Handles only hours, minutes and seconds.

    """
    try:
        if len(iso_str) > 3:
            import re
            match = re.match(r'^PT(?:([\d.]+)H)?(?:([\d.]+)M)?(?:([\d.]+)S)?$', iso_str)
            if match:
                hours, minutes, seconds = match.groups(default=0)
                return int(float(hours) * 3600 + float(minutes) * 60 + float(seconds))
    except (ValueError, AttributeError, TypeError):
        pass

    logger.warning("Invalid ISO8601 duration: '%s'", iso_str)
    return None


def reformat_date(date_string: str, old_format: str, new_format: str):
    """Take a string containing a datetime in a particular format and
    convert it into another format.

    Usually used to convert datetime strings obtained from a website into a nice readable format.

    """
    dt = datetime(*(time.strptime(date_string, old_format)[0:6]))
    return dt.strftime(new_format)


def strptime(dt_str: str, format: str):
    """A bug free alternative to `datetime.datetime.strptime(...)`"""
    return datetime(*(time.strptime(dt_str, format)[0:6]))


def paginate(items: list, page_nr: int, page_len: int, merge_count: int = 5):
    """Return a subset of the list.

    Prevent last pages of `merge_count` or fewer items by adding them to the previous page.
    """
    start = page_nr * page_len
    end = start + page_len
    if end + merge_count < len(items):
        return items[start:end], page_nr + 1
    else:
        return items[start:end + merge_count], None


def list_start_chars(items: list):
    """Return a list of all starting character present in the sorttitles in the list `items`.

    Used to create an A-Z listing to subdivide long lists of items, but only list those
    characters that have actual items.

    """
    start_chars = set(item['show']['info']['sorttitle'][0].upper() for item in items)
    az_chars = list(string.ascii_uppercase)
    char_list = sorted(start_chars.intersection(az_chars))
    if start_chars.difference(char_list):
        # Anything not a letter
        char_list.append('0-9')
    return char_list
