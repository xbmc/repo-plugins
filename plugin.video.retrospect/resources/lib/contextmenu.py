# SPDX-License-Identifier: CC-BY-NC-SA-4.0


class ContextMenuItem:
    """Context menu item class that is used to pass on contextmenu items."""

    def __init__(self, label, function_name, item_types=None):
        """Instantiation of the class. 

        :param str label:               The label/name of the item.
        :param str function_name:       The name of the method that is called when the
                                        item is selected.
        :param list[str] item_types:    The MediaItem types for which the contextmenu item should be
                                        shown [optional].

        """

        self.label = label
        self.functionName = function_name
        self.itemTypes = item_types

    def __str__(self):
        """Returns the string representation of the contextmenu item"""

        return "%s (%s), Types:%s" % (
            self.label, self.functionName, self.itemTypes)
