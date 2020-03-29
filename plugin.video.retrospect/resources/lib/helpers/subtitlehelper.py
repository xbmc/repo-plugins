# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import time
import io
import os

from resources.lib.regexer import Regexer
from resources.lib.retroconfig import Config
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.encodinghelper import EncodingHelper


class SubtitleHelper(object):
    """Helper class that is used for handling subtitle files."""

    # https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    ANSIColours = {
        "<30>": '<font color="#000000">',  # Black
        "<31>": '<font color="#ff0000">',  # Red
        "<32>": '<font color="#00ff00">',  # Green
        "<33>": '<font color="#ffff00">',  # Brown/Yellow
        "<34>": '<font color="#0000ff">',  # Blue
        "<35>": '<font color="#ff00ff">',  # Magenta
        "<36>": '<font color="#00ffff">',  # Cyan
        "<37>": '<font color="#ffffff">',  # Gray
        "</30>": "</font>",
        "</31>": "</font>",
        "</32>": "</font>",
        "</33>": "</font>",
        "</34>": "</font>",
        "</35>": "</font>",
        "</36>": "</font>",
        "</37>": "</font>",
    }

    def __init__(self):
        """Create a class instance. This is not allowed, due to only static
        methods.

        """

        raise Exception("Not allowed to create instance of SubtitleHelper")

    # noinspection PyShadowingBuiltins
    @staticmethod
    def download_subtitle(url, file_name="", format='sami', proxy=None, replace=None):
        """Downloads a SAMI and stores the SRT in the cache folder

        Arguments:
        @param url:         string - URL location of the SAMI file
        @param file_name:    string - [opt] Filename to use to store the subtitle in SRT format.
                                     if not specified, an MD5 hash of the URL with .xml
                                     extension will be used
        @param format:      string - Defines the source format. Defaults to Sami.
        @param proxy:       Proxy  - If specified, a proxy will be used
        @param replace:     dict   - Dictionary with key to will be replaced with their values

        @return: The full patch of the cached SRT file.


        """

        if file_name == "":
            Logger.debug("No filename present, generating filename using MD5 hash of url.")
            file_name = "%s.srt" % (EncodingHelper.encode_md5(url),)
        elif not file_name.endswith(".srt"):
            Logger.debug("No SRT extension present, appending it.")
            file_name = "%s.srt" % (file_name,)

        srt = ""
        try:
            local_complete_path = os.path.join(Config.cacheDir, file_name)

            # no need to download it again!
            if os.path.exists(local_complete_path):
                Logger.debug("Found existing subtitle: %s", local_complete_path)
                return local_complete_path

            Logger.trace("Opening Subtitle URL")
            raw = UriHandler.open(url, proxy=proxy)
            if UriHandler.instance().status.error:
                Logger.warning("Could not retrieve subtitle from %s", url)
                return ""

            if raw == "":
                Logger.warning("Empty Subtitle path found. Not setting subtitles.")
                return ""

            # try to decode it as `raw` should be a string.
            if isinstance(raw, bytes):
                try:
                    raw = raw.decode()
                except:
                    # fix some weird chars
                    try:
                        raw = raw.replace("\x96", "-")
                    except:
                        Logger.error("Error replacing some weird chars.")
                    Logger.warning("Converting input to UTF-8 using 'unicode_escape'")
                    raw = raw.decode('unicode_escape')

            # do some auto detection
            if raw.startswith("WEBVTT") and format != "webvtt":
                Logger.info("Discovered subtitle format 'webvtt' instead of '%s'", format)
                format = "webvtt"

            # Actually transform the subtitle
            srt = SubtitleHelper.__transform(raw, sub_format=format, url=url, proxy=proxy)

            if replace:
                Logger.debug("Replacing SRT data: %s", replace)
                for needle in replace:
                    srt = srt.replace(needle, replace[needle])

            if not srt or not srt.strip():
                Logger.error("Transformed data was empty!")
                return ""

            with io.open(local_complete_path, 'w', encoding="utf-8") as f:
                f.write(srt)

            Logger.info("Saved SRT as %s", local_complete_path)
            return local_complete_path
        except:
            Logger.error("Error handling Subtitle file: [%s]", srt, exc_info=True)
            return ""

    @staticmethod
    def __convert_json_subtitle_to_srt(json_subtitle):
        """Converts Json Subtitle format into SRT format:

        Arguments:
        jsonSubtitle : string - Json Subtitle subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            {"startMillis":80,"endMillis":4170,"text":"Ett Kanal 5:\nAlla gonblick i \"100 jdare!!!\"?","posX":0.5,"posY":0.9,"colorR":220,"colorG":220,"colorB":220}

        Returns
            1
            00:00:20,000 --> 00:00:24,400
            text

        The format of the timecode is Hours:Minutes:Seconds:Ticks where a "Tick"
        is a value of between 0 and 249 and lasts 4 milliseconds.

        """

        regex = r'"startMillis":(\d+),"endMillis":(\d+),"text":"(.+?)(?=["] *,)'
        subs = Regexer.do_regex(regex, json_subtitle)

        # Init some stuff
        srt = ""
        i = 1

        for sub in subs:
            try:
                start = SubtitleHelper.__convert_to_time(sub[0])
                end = SubtitleHelper.__convert_to_time(sub[1])

                text = sub[2].replace('\"', '"')
                text = JsonHelper.convert_special_chars(text)
                text = HtmlEntityHelper.convert_html_entities(text)
                srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text.strip())
                i += 1
            except:
                Logger.error("Error parsing subtitle: %s", sub, exc_info=True)

        return srt

    @staticmethod
    def __convert_dc_subtitle_to_srt(dc_subtitle):
        """Converts DC Subtitle format into SRT format:

        Arguments:
        dcSubtitle : string - DC Subtitle subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            <Subtitle SpotNumber="1" TimeIn="00:00:01:220" TimeOut="00:00:04:001" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="6.0">Line 1</Text>
            </Subtitle>
            <Subtitle SpotNumber="2" TimeIn="00:02:07:180" TimeOut="00:02:10:040" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="6.0">Line 1</Text>
            </Subtitle>
            <Subtitle SpotNumber="3" TimeIn="00:02:15:190" TimeOut="00:02:17:190" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 1</Text>
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="6.0">Line 2</Text>
            </Subtitle>
            <Subtitle SpotNumber="4" TimeIn="00:03:23:140" TimeOut="00:03:30:120" FadeUpTime="20" FadeDownTime="20">
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 1</Text>
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 2</Text>
              <Text Direction="horizontal" HAlign="center" HPosition="0.0" VAlign="bottom" VPosition="14.0">Line 3</Text>
            </Subtitle>

        Returns
            1
            00:00:20,000 --> 00:00:24,400
            text

        The format of the timecode is Hours:Minutes:Seconds:Ticks where a "Tick"
        is a value of between 0 and 249 and lasts 4 milliseconds.

        """

        parse_regex = r'<subtitle[^>]+spotnumber="(\d+)" timein="(\d+:\d+:\d+):(\d+)" ' \
                      r'timeout="(\d+:\d+:\d+):(\d+)"[^>]+>|<text[^>]+>([^<]+)</text>'
        parse_regex = parse_regex.replace('"', '["\']')
        subs = Regexer.do_regex(parse_regex, dc_subtitle)

        srt = ""
        i = 1
        text = ""
        start = ""
        end = ""

        for sub in subs:
            #Logger.Trace(sub)
            try:
                if sub[0]:
                    # new start of a sub
                    if text and start and end:
                        # if we have a complete old one, save it
                        text = HtmlEntityHelper.convert_html_entities(text)
                        srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text.strip())
                        i += 1
                    start = "%s,%03d" % (sub[1], int(sub[2]))
                    end = "%s,%03d" % (sub[3], int(sub[4]))
                    text = ""
                else:
                    text = "%s\n%s" % (text, sub[5].replace("<br />", "\n"))
            except:
                Logger.error("Error parsing subtitle: %s", sub, exc_info=True)
        return srt

    @staticmethod
    def __convert_web_vtt_to_srt(webvvt):
        """Converts sami format into SRT format:

        Arguments:
        ttml : string - TTML (Timed Text Markup Language) subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            1
            00:00:20,000 --> 00:00:24,400
            text

        """

        count = 0
        result = ""
        for line in webvvt.split("\n"):
            line = line.strip()
            if line.endswith("WEBVTT") or line.startswith("X-TIMESTAMP"):
                continue
            if not line:
                continue

            if " --> " in line:
                count += 1
                start, end = line.split(" --> ")
                result = "%s\n\n%s" % (result, count)
                if start.count(":") == 1:
                    result = "%s\n00:%s --> 00:%s" % (result, start.replace(".", ","), end.replace(".", ","))
                else:
                    result = "%s\n%s --> %s" % (result, start.replace(".", ","), end.replace(".", ","))
            elif line == str(count + 1):
                # we apparently have built-in numbering using WebVTT cue-numbering
                continue
            else:
                result = "%s\n%s" % (result, HtmlEntityHelper.convert_html_entities(line))

        return result

    @staticmethod
    def __convert_ttml_to_srt(ttml):
        """Converts sami format into SRT format:

        Arguments:
        ttml : string - TTML (Timed Text Markup Language) subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            1
            00:00:20,000 --> 00:00:24,400
            text

        """

        pars_regex = r'<p[^>]+begin="([^"]+)\.(\d+)"[^>]+end="([^"]+)\.(\d+)"[^>]*>([\w\W]+?)</p>'
        subs = Regexer.do_regex(pars_regex, ttml)

        srt = ""
        i = 1

        for sub in subs:
            try:
                start = "%s,%03d" % (sub[0], int(sub[1]))
                end = "%s,%03d" % (sub[2], int(sub[3]))
                text = sub[4].replace("<br />", "\n")
                text = HtmlEntityHelper.convert_html_entities(text)
                text = text.replace("\r\n", "")
                srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text.strip())
                i += 1
            except:
                Logger.error("Error parsing subtitle: %s", sub[1], exc_info=True)

        return srt

    @staticmethod
    def __convert_sami_to_srt(sami):
        """Converts sami format into SRT format:

        Arguments:
        sami : string - SAMI subtitle format

        Returns:
        SRT formatted subtitle:

        Example:
            1
            00:00:20,000 --> 00:00:24,400
            text

        """
        pars_regex = r'<sync start="(\d+)"><p[^>]+>([^<]+)</p></sync>\W+<sync start="(\d+)">'
        subs = Regexer.do_regex(pars_regex, sami)

        if len(subs) == 0:
            pars_regex2 = r'<sync start=(\d+)>\W+<p[^>]+>([^\n]+)\W+<sync start=(\d+)>'
            subs = Regexer.do_regex(pars_regex2, sami)

        srt = ""
        i = 1

        for sub in subs:
            try:
                start = SubtitleHelper.__convert_to_time(sub[0])
                end = SubtitleHelper.__convert_to_time(sub[2])
                text = sub[1]
                text = HtmlEntityHelper.convert_html_entities(text)
                srt = "%s\n%s\n%s --> %s\n%s\n" % (srt, i, start, end, text)
                i += 1
            except:
                Logger.error("Error parsing subtitle: %s", sub[1], exc_info=True)

        # re-encode to be able to write it
        return srt

    @staticmethod
    def __convert_m3u8_srt_to_subtitle_to_srt(raw, url, proxy):
        # Find the VTT line in the subtitle
        lines = raw.split("\n")
        sub_url = None
        for line in lines:
            if ".vtt" in line:
                sub_url = line
                break

        if not sub_url:
            return ""

        if not sub_url.startswith("http"):
            sub_url = "%s/%s" % (url.rsplit("/", 1)[0], sub_url)

        # Now we know the subtitle, it would be wise to just use the existing converters to just
        # convert the data, but now now
        result = ""
        m3u8_sub = UriHandler.open(sub_url, proxy=proxy)

        if isinstance(m3u8_sub, bytes):
            # Decode the data as it should be str
            try:
                m3u8_sub = m3u8_sub.decode()
            except:
                Logger.warning("Converting input to UTF-8 using 'unicode_escape'")
                m3u8_sub = m3u8_sub.decode('unicode_escape')

        for line in m3u8_sub.split("\n"):
            line = line.strip()
            if line.endswith("WEBVTT") or line.startswith("X-TIMESTAMP"):
                continue

            if " --> " in line:
                start, end = line.split(" --> ")
                if start.count(":") == 1:
                    result = "%s\n00:%s --> 00:%s" % (result, start.replace(".", ","), end.replace(".", ","))
                else:
                    result = "%s\n%s --> %s" % (result, start.replace(".", ","), end.replace(".", ","))
            else:
                result = "%s\n%s" % (result, line)

        return result

    @staticmethod
    def __convert_to_time(timestamp):
        """Converts a SAMI (msecs since start) timestamp into a SRT timestamp

        Arguments:
        timestamp : string - SAMI timestamp

        Returns:
        SRT timestamp (00:04:53,920)

        """
        msecs = timestamp[-3:]
        secs = int(timestamp) // 1000
        sync = time.strftime("%H:%M:%S", time.gmtime(secs)) + ',' + msecs
        return sync

    @staticmethod
    def __transform(raw, sub_format, url, proxy):
        """ Transforms subtitle into a specific format

        @param str url:         URL location of the SAMI file
        @param str raw:         The raw subtitle data
        @param str sub_format:  Defines the source format. Defaults to Sami.
        @param Proxy proxy:     If specified, a proxy will be used

        """

        if sub_format.lower() == 'sami':
            srt = SubtitleHelper.__convert_sami_to_srt(raw)
        elif sub_format.lower() == 'srt':
            srt = raw
        elif sub_format.lower() == 'webvtt':
            srt = SubtitleHelper.__convert_web_vtt_to_srt(
                raw)  # With Krypton and Leia VTT is supported natively
        elif sub_format.lower() == 'ttml':
            srt = SubtitleHelper.__convert_ttml_to_srt(raw)
        elif sub_format.lower() == 'dcsubtitle':
            srt = SubtitleHelper.__convert_dc_subtitle_to_srt(raw)
        elif sub_format.lower() == 'json':
            srt = SubtitleHelper.__convert_json_subtitle_to_srt(raw)
        elif sub_format.lower() == 'm3u8srt':
            srt = SubtitleHelper.__convert_m3u8_srt_to_subtitle_to_srt(raw, url, proxy)
        else:
            error = "Unknown subtitle format: %s" % (sub_format,)
            raise NotImplementedError(error)

        return srt
