# coding:UTF-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import re
import json

from resources.lib.backtothefuture import unichr


#noinspection PyShadowingNames
class JsonHelper(object):
    def __init__(self, data, logger=None):
        """Creates a class that wraps json.

        :param str|unicode data:    JSON data to parse.
        :param any logger:      If specified it is used for logging.

        """

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        self.logger = logger
        self.data = data.strip()
        self.json = dict()

        if len(self.data) == 0:
            # no data in, no data out
            self.json = dict()
            return

        if self.data[0] not in "[{":
            # find the actual start in case of a jQuery18303627530449324564_1370950605750({"success":true});
            if self.logger is not None:
                self.logger.debug("Removing non-Json wrapper")
            start = self.data.find("(") + 1
            end = self.data.rfind(")")
            self.data = self.data[start:end]

        # here we are call the json.loads
        self.json = json.loads(self.data)

    @staticmethod
    def convert_special_chars(text, do_quotes=True):
        """ Converts special characters in json to their Unicode equivalents. Quotes can
        be omitted by specifying the doQuotes as False. The input text should be able to
        hold the output format. That means that for UTF-8 charachters
        to be allowed, the string should be UTF-8 decoded because, Python will otherwise
        assume it to be ASCII.

        :param str|unicode text:    The text to search for.
        :param bool do_quotes:      Should quotes be replaced?

        :return: Returns text with all the \\uXXXX values replaced with their Unicode
        characters. XXXX is considered a Hexvalue. It returns unichr(int(hex)). The
        returnvalue is UTF-8 byte encoded.
        :rtype: str|unicode

        """

        # special chars
        # unicode chars
        clean_text = re.sub("(\\\\u)(.{4})", JsonHelper.__special_chars_handler, text)

        # other replacements
        replacements = [("\\n", "\n"), ("\\r", "\r"), ("\\/", "/")]
        for k, v in replacements:
            clean_text = clean_text.replace(k, v)

        if do_quotes:
            clean_text = JsonHelper.__convert_quotes(clean_text)

        return clean_text

    @staticmethod
    def __convert_quotes(text):
        """ Replaces escaped quotes with their none escaped ones.

        :param str|unicode text:    The input text to clean.

        :return: text with quotes converted.
        :rtype: str|unicode

        """

        clean_text = text
        replacements = [('\\"', '"'), ("\\'", "'")]

        for k, v in replacements:
            clean_text = clean_text.replace(k, v)

        return clean_text

    @staticmethod
    def __special_chars_handler(match):
        """ Helper method to replace \\uXXXX with unichr(int(hex))

        :param re.Match match:  The matched element in which group(2) holds the
                                hex value.

        :return: Returns the Unicode character corresponding to the Hex value.
        :rtype: chr

        """

        hex_string = "0x%s" % (match.group(2))
        hex_value = int(hex_string, 16)
        return unichr(hex_value)

    #noinspection PyUnboundLocalVariable
    def get_value(self, *args, **kwargs):
        """ Retrieves data from the JSON object based on the input parameters

        :param str args|int:    The dictionary keys, or list indexes.
        :param any kwargs:      Possible value = fallback and allows the specification of a fallback value.

        :return: the selected JSON object

        """

        try:
            data = self.json
            for arg in args:
                data = data[arg]
        except KeyError:
            if "fallback" in kwargs:
                if self.logger:
                    self.logger.debug("Key ['%s'] not found in Json", arg)
                return kwargs["fallback"]

            if self.logger:
                self.logger.warning("Key ['%s'] not found in Json", arg, exc_info=True)
            return None

        return data

    @staticmethod
    def dump(dictionary, pretty_print=True, sort_keys=False):
        """ Dumps a JSON object to a string

        :param bool pretty_print:       Indicating if the format should be nice.
        :param dict|list dictionary:    The object to dump.
        :param bool sort_keys:          Show we sort by keys?

        :return: a valid JSON string
        :rtype: str

        """

        if pretty_print:
            return json.dumps(dictionary, indent=4, sort_keys=sort_keys, ensure_ascii=False)
        else:
            return json.dumps(dictionary, sort_keys=sort_keys, ensure_ascii=False)

    @staticmethod
    def loads(json_data):
        """ Loads a JSON object to a valid object

        :param str|unicode json_data:   The JSON data to load
        :return: a valid JSON object

        """

        return json.loads(json_data)

    def __str__(self):
        return self.data
