# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import re
import io
from xml.etree import ElementTree


class TemplateHelper(object):
    def __init__(self, logger, template_path=None, template=None):
        """ Instantiates a new TemplateHelper class object. This object can walk a Kodi settings.xml
        file and modify it based on a template.

        :param Logger logger:       A `Logger` object used for logging.
        :param str template_path:   Path to a template file.
        :param str template:        Actual template string.

        """

        self.__logger = logger
        self.__settingsIndex = {}
        self.__relativeRegex = re.compile("(%([^%]+)%)")

        self.__templateLines = []
        if template_path:
            with io.open(template_path, "r", encoding="utf-8") as fp:
                self.__templateLines = fp.readlines()
        else:
            with io.StringIO(template) as fp:
                self.__templateLines = fp.readlines()

        if template_path:
            self.__template = ElementTree.parse(template_path)
        else:
            self.__template = ElementTree.fromstring(template)

        categories = self.__template.findall('.//category')
        for category in categories:
            category_settings_index = []
            category_id = category.attrib["id"]
            self.__settingsIndex[category_id] = category_settings_index

            settings = category.findall('.//setting')
            self.__logger.debug("Found %d settings in Category '%s'", len(settings), category_id)
            for node in settings:
                setting_id = node.attrib.get("id", ElementTree.tostring(node).strip())
                node_str = ElementTree.tostring(node).strip()
                category_settings_index.append(setting_id)
                self.__logger.trace("%02d: %s - %s", len(category_settings_index), setting_id, node_str)

    def get_offset(self, category_id, reference_id, setting_id, skip=0):
        """ Determines the offset from one setting to a reference settings.

        :param str category_id:             Current category ID.
        :param str|unicode reference_id:    The ID of the setting we are pointing to.
        :param str setting_id:              The current setting ID.
        :param int skip:                    Should we skip a number of found matched settings?

        :return: The offset for the setting with `reference_id` relative to the current setting with
                 `setting_id`.
        :rtype: int

        """

        if self.__settingsIndex[category_id].count(reference_id) > 1:
            raise ValueError("Multiple reference setting indexes found for %s." % (reference_id,))

        if self.__settingsIndex[category_id].count(setting_id) > 1:
            self.__logger.warning("Multiple values found for %s, using #%s", setting_id, skip)

        return self.get_index_of(category_id, reference_id) - self.get_index_of(category_id, setting_id, skip)

    def get_index_of(self, category_id, setting_id, skip=0):
        """ Returns the index of the setting with `setting_id` within the category with
        `category_id`.

        :param str category_id:     Current category ID.
        :param str setting_id:      The current setting ID.
        :param int skip:            Should we skip a number of found matched settings?

        :return: The index of the setting with `setting_id` within the category.
        :rtype: int

        """

        settings_in_category = self.__settingsIndex[category_id]
        if settings_in_category.count(setting_id) == 1:
            return settings_in_category.index(setting_id)

        self.__logger.warning("Multiple values found for setting_id %s, using #%s", setting_id, skip)
        setting_indexes = [s for s in settings_in_category if s == setting_id]
        # The old way:
        # setting_indexes = filter(lambda s: s == setting_id, settings_in_category)
        if not setting_indexes:
            raise ValueError("No settings found for %s" % (setting_id,))

        index = 0
        index_start = 0
        for i in range(0, skip + 1):
            # start one after the current index (but then we need to add +1 to the found index)
            index += settings_in_category[index_start:].index(setting_id)
            if i > 0:
                index += 1
            index_start = index + 1
        return index

    def transform(self):
        """ Transforms a settings.xml template into an actual settings.xml file.

        :return: The new settings.xml content
        :rtype: str|unicode

        """

        # we go through it line by line, because we don't want to modify any order in attributes
        # or whitespaces. This currently only works for SINGLE LINE XML elements!
        result = []
        category = None
        settings_in_category = []
        for line in self.__templateLines:
            # always append the line
            self.__logger.trace("%s", line.strip())
            result.append(line)

            if "<category" in line:
                line = line.replace(">", "/>")
                element = ElementTree.fromstring(line)
                # we start a new category
                category = element.attrib["id"]
                settings_in_category = []
                continue

            if not line.strip() or "/>" not in line or line.strip().startswith("<!--"):
                continue

            element = ElementTree.fromstring(line.encode('utf-8'))
            element_id = element.attrib.get("id", ElementTree.tostring(element))

            if category is None:
                # visible only works within categories
                continue

            # so we found an ID of a setting see if it was a duplicate and add it to the items
            # that were found. We need this to support duplicate IDs in the settings within a
            # single category.
            setting_ids_found_before = settings_in_category.count(element_id)
            settings_in_category.append(element_id)

            # now see if we need to replace
            if "visible" not in element.attrib or "%" not in element.attrib.get("visible", ""):
                # we need a visible attribute with a template
                continue

            self.__logger.debug("IN:  %s", line.strip())
            matches = self.__relativeRegex.findall(line)
            for match in matches:
                line = line.replace(match[0], str(self.get_offset(category, match[1], element_id, skip=setting_ids_found_before)))

            # replace the line we added at the start
            result[-1] = line
            self.__logger.debug("OUT: %s", line.strip())
        return "".join(result)
