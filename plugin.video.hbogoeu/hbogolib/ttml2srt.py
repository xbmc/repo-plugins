# encoding: utf-8
#
#  --------------------------------------------
#  based on https://github.com/yuppity/ttml2srt
#  --------------------------------------------

from __future__ import absolute_import, division

import sys

from defusedxml import minidom


class Ttml2srt(object):

    def __init__(self, ttml_input_file, default_fps):
        self.subtitle = self.extract_subtitle_data(ttml_input_file)
        if not self.subtitle['fps']:
            self.subtitle['fps'] = default_fps

    def write_srt_file(self, str_file, shift=0):
        filename = str_file + '.srt'
        if self.subtitle['lang'] is not None:
            filename = str_file + '.' + self.subtitle['lang'] + '.srt'
        f = None
        if (sys.version_info > (3, 0)):
            f = open(filename, 'w', encoding='utf-8')
        else:
            f = open(filename, 'wb')
        self.subrip_writer(f, self.subtitle['lines'], f, shift, self.subtitle['fps'], self.subtitle['tick_rate'])
        return filename

    #######################################################################
    #                                TTML                                 #
    #######################################################################

    def extract_dialogue(self, nodes):
        dialogue = ''
        for node in nodes:
            if node.localName == 'span' and node.hasChildNodes():
                dialogue = dialogue + "<i>" + self.extract_dialogue(node.childNodes) + "</i>"
                continue
            if node.localName == 'br':
                dialogue = dialogue + '\n'
            elif node.nodeValue:
                dialogue = dialogue + node.nodeValue.replace("\n", "")
            if node.hasChildNodes():
                dialogue = dialogue + self.extract_dialogue(node.childNodes)
        return dialogue

    @staticmethod
    def extract_subtitle_data(ttml_file):
        data = minidom.parse(ttml_file)

        s_encoding = data.encoding
        if s_encoding and s_encoding.lower() not in ['utf8', 'utf-8']:
            # Don't bother with subtitles that aren't utf-8 encoded
            # but assume utf-8 when the encoding attr is missing
            raise NotImplementedError('Source is not declared as utf-8')

        # Get the root tt element (assume the file contains
        # a single subtitle document)
        tt_element = data.getElementsByTagName('tt')[0]

        # Get Language
        try:
            lang = str(tt_element.attributes['xml:lang'].value)
        except KeyError:
            lang = None

        # Detect source FPS and tick rate
        try:
            fps = int(tt_element.attributes['ttp:frameRate'].value)
        except KeyError:
            fps = None
        try:
            tick_rate = int(tt_element.attributes['ttp:tickRate'].value)
        except KeyError:
            tick_rate = None

        lines = [i for i in data.getElementsByTagName('p') if 'begin' \
                 in list(i.attributes.keys())]

        return {'fps': fps, 'tick_rate': tick_rate, 'lines': lines, 'lang': lang}

    @staticmethod
    def get_start_end(parag):
        return [parag.attributes['begin'].value, parag.attributes['end'].value]

    #######################################################################
    #                           TIME/TIMESTAMPS                           #
    #######################################################################

    @staticmethod
    def calc_scale(sdur, tdur):
        return (tdur * 1.0) / sdur

    @staticmethod
    def scaler(time, scale):
        return scale * time

    @staticmethod
    def frames_to_ms(frames, fps=23.976):
        return int(int(frames) * (1000 / fps))

    def ticks_to_ms(self, tickrate, ticks, scale=1):
        return self.scaler(((1.0 / tickrate) * int(ticks.rstrip('t'))) * 1000, scale)

    @staticmethod
    def ms_to_subrip(ms):
        hh = int(ms / 3.6e6)
        mm = int((ms % 3.6e6) / 60000)
        ss = int((ms % 60000) / 1000)
        ms = int(ms % 1000)
        return '{:02d}:{:02d}:{:02d},{:03d}'.format(hh, mm, ss, ms)

    def timestamp_to_ms(self, time, fps=23.976, delim='.', scale=1):
        hhmmss, frames = time.rsplit(delim, 1)
        ms = self.frames_to_ms(frames, fps)
        hhmmss = hhmmss.split(':')
        hh, mm, ss = [int(hhmmss[0]) * 3600 * 1000,
                      int(hhmmss[1]) * 60 * 1000,
                      int(hhmmss[2]) * 1000]
        return self.scaler(hh + mm + ss + ms, scale)

    def seconds_to_ms(self, time, scale=1):
        ss, cc = time.rsplit('.', 1)
        # Remove the unit signifier before converting to ms.
        cc = int(cc[:-1]) * 10
        ss = int(ss) * 1000
        return self.scaler(ss + cc, scale)

    def get_sb_timestamp_be(self, time, shift=0, fps=23.976, tick_rate=None, scale=1):
        """Return SubRip timestamp after conversion from source timestamp.
        Assumes source timestamp to be in either the form of
            [0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}[,.:]{0-9}{1,3}
        or
            [0-9]*t?$
        Examples of valid timestamps: '00:43:30:07', '00:43:30.07',
        '00:43:30,07', '130964166t'.
        Assumes that all field separated four value timestamps map
        to 'hour:minute:second:frame'.
        """

        delim = ''.join([i for i in time if not i.isdigit()])[-1]
        if delim.lower() == 't':
            ms = self.ticks_to_ms(tick_rate, time, scale)
        elif delim.lower() == 's':
            ms = self.seconds_to_ms(time, scale)
        else:
            ms = self.timestamp_to_ms(time, fps, delim, scale)

        return self.ms_to_subrip(ms + shift)

    #######################################################################
    #                            SubRip output                            #
    #######################################################################

    @staticmethod
    def subrip_dialogue(count, start, end, dialogue):
        return "{}\n{} --> {}\n{}\n\n".format(count, start, end, dialogue)

    def subrip_writer(self, f, lines, dst, shift, fps, tick_rate, scale=1):
        subs = []
        for line in lines:
            start, end = self.get_start_end(line)
            if (sys.version_info > (3, 0)):
                subs.append([self.get_sb_timestamp_be(start, shift, fps, tick_rate, scale),
                             self.get_sb_timestamp_be(end, shift, fps, tick_rate, scale),
                             self.extract_dialogue(line.childNodes)])
            else:
                subs.append([self.get_sb_timestamp_be(start, shift, fps, tick_rate, scale),
                             self.get_sb_timestamp_be(end, shift, fps, tick_rate, scale),
                             self.extract_dialogue(line.childNodes).encode('utf8')])

        # Sort by the start time
        subs.sort(key=lambda x: x[0])

        # Detect and deal with overlapping time intervals. Only
        # works for overlaps that span two elements for now.
        overlaps = []
        for i in range(0, len(subs)):
            if subs[i - 1][0] <= subs[i][0] < subs[i - 1][1]:
                overlaps.append((i - 1, i))

        overlaps.reverse()
        for o in overlaps:
            a, b = o
            subs[a][1] = max(subs[a][1], subs[b][1])
            subs[a][2] = subs[a][2] + '\n' + subs[b][2]
            subs.pop(b)

        # Write to file obj
        lcount = 0
        for line in subs:
            lcount = lcount + 1
            dialg = self.subrip_dialogue(lcount, line[0], line[1], line[2])
            f.write(dialg)
        f.close()
