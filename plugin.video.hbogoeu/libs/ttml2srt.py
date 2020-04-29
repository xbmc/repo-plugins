# encoding: utf-8
#
#  --------------------------------------------
#  based on https://github.com/yuppity/ttml2srt
#  --------------------------------------------
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import, division

from defusedxml import minidom  # type: ignore
import re


class Ttml2Srt(object):

    TIME_BASES = [
        'media',
        'smpte',
    ]

    def __init__(
            self, ttml_filepath, shift=0, source_fps=23.976,
            target_duration=None, source_duration=None):

        self.shift = shift
        self.target_duration = target_duration
        self.source_duration = source_duration

        self.time_multiplier = Ttml2Srt.calc_scale(
            self.source_duration, self.target_duration) \
            if target_duration and source_duration \
            else 1

        self.styles = {}

        self.allowed_style_attrs = (
            'color',
            'fontStyle',
            'fontWeight',
        )

        self.lang = None

        # Read TT params, dialogue, etc.
        self._load_ttml_doc(ttml_filepath)

        # Set FPS to source_fps if no TT param
        self.frame_rate = self.frame_rate or source_fps

        self.italic_style_ids = []
        for sid, style in list(self.styles.items()):
            if style['font_style'] == 'italic':
                self.italic_style_ids.append(sid)

    def _load_ttml_doc(self, filepath):
        """Read TTML file. Extract <p> elements and various attributes.
        """

        ttml_dom = minidom.parse(filepath)
        self.encoding = ttml_dom.encoding

        if self.encoding and self.encoding.lower() not in ['utf8', 'utf-8']:
            # Don't bother with subtitles that aren't utf-8 encoded
            # but assume utf-8 when the encoding attr is missing
            raise NotImplementedError('Source is not utf-8 encoded')

        # Get the root tt element (assume the file contains
        # a single subtitle document)
        tt_element = ttml_dom.getElementsByTagName('tt')[0]

        # Extract doc language
        # https://tools.ietf.org/html/rfc4646#section-2.1
        language_tag = tt_element.getAttribute('xml:lang') or ''
        self.lang = re.split(r'\s+', language_tag.strip())[0].split('-')[0]

        # Store TT parameters as instance vars (in camel case)
        for ttp_name, defval, convfn in (
                # (tt param, default val, fn to process the str)
                ('frameRate', 0, lambda x: float(x)),
                ('tickRate', 0, lambda x: int(x)),
                ('timeBase', 'media', lambda x: x),
                ('clockMode', '', lambda x: x),
                ('frameRateMultiplier', 1, lambda x: int(x)),
                ('subFrameRate', 1, lambda x: int(x)),
                ('markerMode', '', lambda x: x),
                ('dropMode', '', lambda x: x),
        ):
            ttp_val = getattr(
                tt_element.attributes.get('ttp:' + ttp_name), 'value', defval)
            setattr(self, Ttml2Srt.snake_to_camel(ttp_name), convfn(ttp_val))

        if self.time_base not in Ttml2Srt.TIME_BASES:
            raise NotImplementedError('No support for "{}" time base'.format(
                self.time_base))

        # Grab <style>s
        # https://www.w3.org/TR/ttml1/#styling-attribute-vocabulary
        for styles_container in ttml_dom.getElementsByTagName('styling'):
            for style in styles_container.getElementsByTagName('style'):
                style_id = getattr(
                    style.attributes.get('xml:id', {}), 'value', None)
                if not style_id:
                    continue
                self.styles[style_id] = self.get_tt_style_attrs(style, True)

        # Set effective tick rate as per
        # https://www.w3.org/TR/ttml1/#parameter-attribute-tickRate
        # This will obviously only be made use of if we encounter offset-time
        # expressions that have the tick metric.
        if not self.tick_rate and self.frame_rate:
            self.tick_rate = int(self.frame_rate * self.sub_frame_rate)
        elif not self.tick_rate:
            self.tick_rate = 1

        # Get em <p>s.
        #
        # CAUTION: This is very naive and will fail us when the TTML
        # document contains multiple local time contexts with their own
        # offsets, or even just a single context with an offset other
        # than zero.
        self.lines = [i for i in ttml_dom.getElementsByTagName('p') if 'begin' in list(i.attributes.keys())]

    def timeexpr_to_ms(self, *args):
        return self._timeexpr_to_ms(*args)

    def _timeexpr_to_ms(self, time_expr):
        """Use the given time expression to get a matching conversion method
        to overwrite self.timeexpr_to_ms() with.
        """

        self.timeexpr_to_ms = self.determine_ms_convfn(time_expr)
        return self.timeexpr_to_ms(time_expr)

    def _scaler(self, ms):
        return ms * self.time_multiplier

    def _hhmmss_to_ms(self, hh, mm, ss):
        return hh * 3600 * 1000 + mm * 60 * 1000 + ss * 1000

    def subrip_to_ms(self, timestamp):
        """Desconstruct SubRip timecode down to milliseconds
        """

        hh, mm, ss, ms = re.split(r'[:,]', timestamp)
        return int(int(hh) * 3.6e6 + int(mm) * 60000 + int(ss) * 1000 + int(ms))

    def _metric_to_ms(self, metric_multiplier, metric_value):
        return int(metric_multiplier * metric_value)

    def ms_to_subrip(self, ms):
        """Build SubRip timecode from milliseconds
        """

        hh = int(ms / 3.6e6)
        mm = int((ms % 3.6e6) / 60000)
        ss = int((ms % 60000) / 1000)
        ms = int(ms % 1000)
        return '{:02d}:{:02d}:{:02d},{:03d}'.format(hh, mm, ss, ms)

    def frames_to_ms(self, frames):
        """Convert frame count to ms
        """

        return int(int(frames) * (1000 / self.frame_rate))

    def offset_frames_to_ms(self, time):
        """Convert offset-time expression with f metric to milliseconds.
        """

        frames = float(time[:-1])
        return int(int(frames) * (1000 / self.frame_rate))

    def offset_ticks_to_ms(self, time):
        """Convert offset-time expression with t metric to milliseconds.
        """

        ticks = int(time[:-1])
        seconds = 1.0 / self.tick_rate
        return self._scaler((seconds * ticks) * 1000)

    def offset_hours_to_ms(self, time):
        """Convert offset-time expression with h metric to milliseconds.
        """

        hours = float(time[:-1])
        return self._scaler(self._metric_to_ms(3.6e6, hours))

    def offset_minutes_to_ms(self, time):
        """Convert offset-time expression with m metric to milliseconds.
        """

        return self._scaler(self._metric_to_ms(60 * 1000, float(time[:-1])))

    def offset_seconds_to_ms(self, time):
        """Convert offset-time expression with s metric to milliseconds.
        """

        seconds = float(time[:-1])
        return self._scaler(self._metric_to_ms(1000, seconds))

    def offset_ms_to_ms(self, time):
        """Convert offset-time expression with ms metric to milliseconds.
        """

        ms = int(time[:-2])
        return self._scaler(ms)

    def fraction_timestamp_to_ms(self, timestamp):
        """Convert hh:mm:ss.fraction to milliseconds
        """

        hh, mm, ss, fraction = re.split(r'[:.]', timestamp)
        hh, mm, ss = [int(i) for i in (hh, mm, ss)]
        # Resolution beoynd ms is useless for our purposes
        ms = int(fraction[:3])

        return self._scaler(self._hhmmss_to_ms(hh, mm, ss) + ms)

    def get_tt_style_attrs(self, node, in_head=False):
        """Extract node's style attributes

        Node can be a style definition element or a content element (<p>).

        Attributes are filtered against :attr:`Ttml2Srt.allowed_style_attrs`
        and returned as a dict whose keys are attribute names camel cased.
        """

        style = {}
        for attr_name in self.allowed_style_attrs:
            tts = 'tts:' + attr_name
            attr_name = Ttml2Srt.snake_to_camel(attr_name)
            style[attr_name] = node.getAttribute(tts) or ''
        if not in_head:
            style['style_id'] = node.getAttribute('style')
        return style

    def frame_timestamp_to_ms(self, timestamp):
        """Convert hh:mm:ss:frames to milliseconds

        Will handle hh:mm:ss:frames.sub-frames by discarding the sub-frame part
        """

        hh, mm, ss, frames = [int(i) for i in timestamp.split('.')[0].split(':')]
        hhmmss_ms = self._hhmmss_to_ms(hh, mm, ss)
        ms = self.frames_to_ms(frames)
        return self._scaler(hhmmss_ms + ms)

    def extract_dialogue(self, nodes, styles=[]):
        """Extract text content and styling attributes from <p> elements.

        Args:
            nodes (xml.dom.minidom.Node): List of <p> elements
            styles (list): List of style signifiers that should be
                applied to each node

        Return:
            List of SRT paragraphs (strings)
        """

        dialogue = []

        for node in nodes:

            _styles = []

            if node.nodeType == node.TEXT_NODE:

                format_str = '{}'

                # Take the liberty to make a few stylistic choices. We don't
                # want too many leading spaces or any unnessary new lines
                text = re.sub(r'^\s{4,}', '', node.nodeValue.replace('\n', ''))

                for style in styles:
                    format_str = '{ot}{f}{et}'.format(
                        et='</{}>'.format(style),
                        ot='<{}>'.format(style),
                        f=format_str)

                try:
                    dialogue.append(format_str.format(text))
                except UnicodeEncodeError:
                    dialogue.append(format_str.format(text.encode('utf8')))

            elif node.localName == 'br':
                dialogue.append('\n')

            # Checks for italics for now but shouldn't be too much work to
            # support bold text or colors
            elif node.localName == 'span':
                style_attrs = self.get_tt_style_attrs(node)
                inline_italic = style_attrs['font_style'] == 'italic'
                assoc_italic = style_attrs['style_id'] in self.italic_style_ids
                if inline_italic or assoc_italic:
                    _styles.append('i')

            if node.hasChildNodes():
                dialogue += self.extract_dialogue(node.childNodes, _styles)

        return ''.join(dialogue)

    def timeexpr_to_subrip(self, time_expr):
        ms = self.timeexpr_to_ms(time_expr) + self.shift
        return ms, self.ms_to_subrip(ms)

    def sequalize(self, subs):
        """Combine parallel paragraphs

        Args:
            subs (list): list of list like constructs containing five elements:
                0: begin timestamp in ms
                1: end timestamp in ms
                2: begin timestamp in subrip form
                3: end timestamp in subrip form
                4: dialogue

        Returns:
            List of tuples where elements correspond to
                0: begin timestamp in subrip
                1: end timestamp in subrip
                2: dialogue
        """

        sequalized = []

        for i in range(len(subs)):

            _prev_begin_ms, prev_end_ms, prev_begin_sr, \
                prev_end_sr, _prev_dialogue = subs[i - 1]

            curr_begin_ms, curr_end_ms, curr_begin_sr, \
                curr_end_sr, curr_dialogue = subs[i]

            if i == 0 or curr_begin_ms >= prev_end_ms:
                sequalized.append((curr_begin_sr, curr_end_sr, curr_dialogue))
                continue

            sequalized.append((
                prev_begin_sr,
                curr_end_sr if curr_end_ms > prev_end_ms else prev_end_sr,
                sequalized.pop()[-1] + '\n' + curr_dialogue,
            ))

        return sequalized

    def process_parag(self, paragraph):
        """Extract begin and end attrs, and text content of <p> element.

        Args:
            paragragh (xml.dom.minidom.Element): <p> element.

        Returns:
            Tuple containing
                begin in ms,
                end in ms,
                begin in subrip form,
                end in subrip form,
                text content in Subrip (SRT) format.
        """

        begin = paragraph.attributes['begin'].value
        end = paragraph.attributes['end'].value

        ms_begin, subrip_begin = self.timeexpr_to_subrip(begin)
        ms_end, subrip_end = self.timeexpr_to_subrip(end)

        dialogue = self.extract_dialogue(paragraph.childNodes)

        return ms_begin, ms_end, subrip_begin, subrip_end, dialogue

    def to_paragraphs(self):
        subs = sorted(
            [self.process_parag(p) for p in self.lines], key=lambda x: x[0])

        return self.sequalize(subs)

    def determine_ms_convfn(self, time_expr):
        """Determine approriate ms conversion fn to pass the time expression to.

        Args:
            time_exrp (str): TTML time expression

        Return:
            Conversion method (callable)

        Strips the time expression of digits and uses the resulting string as
        a key to a dict of conversion methods.
        """

        # Map time expression delimiters to conversion methods. Saves
        # us from having to exec multibranch code on each line but assumes all
        # time expressions to be of the same form.
        time_expr_fns = {

            # clock-time, no frames or fraction
            # Example(s): "00:02:23"
            '::': self.frame_timestamp_to_ms,

            # clock-time, frames
            # Example(s): "00:02:23:12", "00:02:23:12.222"
            ':::': self.frame_timestamp_to_ms,
            ':::.': self.frame_timestamp_to_ms,

            # clock-time, fraction
            # Example(s): "00:02:23.283"
            '::.': self.fraction_timestamp_to_ms,

            # offset-time, hour metric
            # Example(s): "1h", "1.232837372637h"
            'h': self.offset_hours_to_ms,
            '.h': self.offset_hours_to_ms,

            # offset-time, minute metric
            # Example(s): "1m", "13.72986323m"
            'm': self.offset_minutes_to_ms,
            '.m': self.offset_minutes_to_ms,

            # offset-time, second metric
            # Example(s): "1s", "113.2312312s"
            's': self.offset_seconds_to_ms,
            '.s': self.offset_seconds_to_ms,

            # offset-time, millisecond metric
            # Example(s): "1ms", "1000.1231231231223ms"
            'ms': self.offset_ms_to_ms,
            '.ms': self.offset_ms_to_ms,

            # offset-time, frame metric
            # Example(s): "100f"
            'f': self.offset_frames_to_ms,
            '.f': self.offset_frames_to_ms,

            # offset-time, tick metric
            # Example(s): "19298323t"
            't': self.offset_ticks_to_ms,
            '.t': self.offset_ticks_to_ms,

        }

        try:
            delims = ''.join([i for i in time_expr if not i.isdigit()])
            return time_expr_fns[delims]
        except KeyError:
            raise NotImplementedError(
                'Unknown timestamp format ("{}")'.format(time_expr))

    def paragraphs(self, generator=False):
        """Return SubRip paragraphs
        """

        srt_format_str = '{}\n{} --> {}\n{}\n\n'

        if generator:
            return (srt_format_str.format(i + 1, *s) for i, s in enumerate(self.to_paragraphs()))

        return ''.join([srt_format_str.format(i + 1, *s) for i, s in enumerate(self.to_paragraphs())])

    def write2file(self, output, close_fd=False):
        """Write SRT file

        `output` can be
            - file like object
            - filename (str)
            - None or '-' (for stdout)
        """

        try:
            sys
        except NameError:
            import sys

        if hasattr(output, 'write') and callable(output.write):
            handle = output
        elif output == '-':
            handle = sys.stdout
        else:
            handle = open(output, 'w')

        try:
            for parag in self.paragraphs(generator=True):
                handle.write(parag)
        finally:
            if (handle is output and close_fd) or \
                    (handle is not output and handle is not sys.stdout):
                handle.close()
        return output

    @staticmethod
    def mfn2srtfn(media_filename, lang=None, m_ext=True):
        """Create SRT filename from media filename

        Uses the <media file w/o ext>.<lang>.srt form recognized by Kodi,
        Plex, VLC, MPV, and others.
        """

        if not m_ext:
            return '{}{}.srt'.format(
                media_filename,
                '.{}'.format(lang) if lang else '')
        else:
            return '{}{}.srt'.format(
                '.'.join(media_filename.split('.')[:-1]),
                '.{}'.format(lang) if lang else '')

    @staticmethod
    def calc_scale(sdur, tdur):
        return (tdur * 1.0) / sdur

    @staticmethod
    def snake_to_camel(s):
        camel = ''
        for c in s:
            d = ord(c)
            if d < 91 and d > 64:
                camel += '_' + c.lower()
            else:
                camel += c
        return camel
