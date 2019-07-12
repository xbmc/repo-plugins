#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================


class ContextMenuItem:
    """Context menu item class that is used to pass on contextmenu items."""

    def __init__(self, label, function_name, item_types=None):
        """Instantiation of the class. 

        :param str label:               The label/name of the item.
        :param str function_name:       The name of the method that is called when the
                                        item is selcted.
        :param list[str] item_types:    The MediaItem types for which the contextitem should be
                                        shown [optional].

        """

        self.label = label
        self.functionName = function_name
        self.itemTypes = item_types

    def __str__(self):
        """Returns the string representation of the contextmenu item"""

        return "%s (%s), Types:%s" % (
            self.label, self.functionName, self.itemTypes)
