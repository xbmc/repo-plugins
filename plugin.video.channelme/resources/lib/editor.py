# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - custom channel editor window (xbmcgui.WindowXMLDialog)
#
# A skinned window:
#   - a category list on the LEFT (Name / Titles / Mode / Back-to-back /
#     Starting eps / Artwork),
#   - a content panel on the RIGHT that swaps to match the highlighted category,
#   - a Save / Cancel column on the far right.
#
# The window edits a working copy of a channel dict in place. doModal() blocks;
# afterwards the caller reads `.saved` (True = commit, False = cancel) and the
# mutated `.channel`. The skin layout lives in
# resources/skins/Default/1080i/script-channelme-editor.xml; the control IDs below
# must stay in sync with that file.
#
# Selected rows carry the list-item Property "sel"=1; the skin paints a deep-blue
# "ambient selected" bar for them (the bright cursor is the focused row). All
# visible text comes from resources/language/.../strings.po via storage.L().

import time

import xbmcgui

from resources.lib import library
from resources.lib import storage

# Reopen guard. Two Home-window (10000) properties, shared across all plugin script
# invocations, stop a stray second editor from opening:
#   - BUSY is set for the whole time an editor is open, so a buffered context-action
#     / click that dispatches a second add/edit invocation is rejected instead of
#     stacking a second modal dialog (revealed when the first closes, or as playback
#     starts). It carries a timestamp so a killed script can't lock editing forever.
#   - CLOSED stamps the close time, so a click buffered just past Save is also swallowed.
_GUARD_WINDOW = 10000
_GUARD_PROP = 'channelme_editor_closed'
_BUSY_PROP = 'channelme_editor_busy'
_GUARD_SECONDS = 0.8
_BUSY_MAX_SECONDS = 600    # a BUSY flag older than this is stale (crashed/killed run)

# ----------------------------------------------------------------------------
# Control IDs (must match the skin XML)
# ----------------------------------------------------------------------------

HEADING = 10
CAT_LIST = 100
SAVE_BTN = 900
CANCEL_BTN = 901

NAME_BTN = 5001
NAME_HINT = 5002
# Titles panel: type filters + search bar + the title list.
FILTER_TV = 5110
FILTER_SET = 5111
FILTER_MOVIE = 5112
FILTER_FILE = 5113
SEARCH_BTN = 5120
TITLES_LIST = 5101
TITLES_HINT = 5102
MODE_LIST = 5201
MODE_HINT = 5202
CONSEC_LIST = 5301
CONSEC_HINT = 5302
CONSEC_MODE_BTN = 5303   # "Up to" / "Always" toggle above the count list
STARTEPS_LIST = 5401
STARTEPS_HINT = 5402
ART_LIST = 5501
ART_HINT = 5502

# Category index -> first focusable control in that panel. (Panel VISIBILITY is
# driven by the skin XML via Container(100).CurrentItem, not from here.)
PANEL_FIRST = {0: NAME_BTN, 1: SEARCH_BTN, 2: MODE_LIST, 3: CONSEC_MODE_BTN,
               4: STARTEPS_LIST, 5: ART_LIST}

# Sidebar category labels, in order.
CATEGORY_IDS = [32001, 32002, 32003, 32004, 32005, 32006]

# type key -> (filter control id, section-header string id)
TYPE_SECTIONS = [
    ('tvshow', FILTER_TV, 32040),
    ('movieset', FILTER_SET, 32041),
    ('movie', FILTER_MOVIE, 32042),
    ('folder', FILTER_FILE, 32043),
]

# Each filter is a focusable button base + a deep-blue "on" layer we show/hide
# (field colour shows when off) + a separate text label on top.
# filter button id -> (type key, on-layer image id).
FILTER_TV_ON = 5130
FILTER_SET_ON = 5131
FILTER_MOVIE_ON = 5132
FILTER_FILE_ON = 5133
FILTER_TV_LABEL = 5140
FILTER_SET_LABEL = 5141
FILTER_MOVIE_LABEL = 5142
FILTER_FILE_LABEL = 5143
FILTER_TOGGLE = {
    FILTER_TV: ('tvshow', FILTER_TV_ON),
    FILTER_SET: ('movieset', FILTER_SET_ON),
    FILTER_MOVIE: ('movie', FILTER_MOVIE_ON),
    FILTER_FILE: ('folder', FILTER_FILE_ON),
}

# Static control labels set from Python (so they read from OUR strings.po, not the
# active skin's via $LOCALIZE): (control id, string id).
STATIC_LABELS = [
    (NAME_HINT, 32010), (TITLES_HINT, 32011), (MODE_HINT, 32012),
    (CONSEC_HINT, 32013), (STARTEPS_HINT, 32014), (ART_HINT, 32015),
    (SAVE_BTN, 32033), (CANCEL_BTN, 32034),
    (FILTER_TV_LABEL, 32040), (FILTER_SET_LABEL, 32041), (FILTER_MOVIE_LABEL, 32042),
    (FILTER_FILE_LABEL, 32043), (SEARCH_BTN, 32024),
]

# ----------------------------------------------------------------------------
# Kodi action IDs we care about
# ----------------------------------------------------------------------------

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOVE_RIGHT = 2

# ----------------------------------------------------------------------------
# Field option tables
# ----------------------------------------------------------------------------

# (stored value, label string id)
MODES = [('serial_random', 32050), ('pure_random', 32051)]
MAX_CONSEC_OPTIONS = [1, 2, 3, 4, 5, 8, 10, 15, 20, 999]
UNLIMITED_CONSEC = 999


# ----------------------------------------------------------------------------
# Small helpers (kept local so this module never imports gui -> no import cycle)
# ----------------------------------------------------------------------------

def _key(item):
    return storage.item_key(item)


def _title_text(item):
    """Plain display title - no [TV]/[Set]/[Movie] prefix (sections carry type)."""
    if item['type'] == 'movie' and item.get('year'):
        return '{0} ({1})'.format(item['title'], item['year'])
    return item['title']


def _consec_label(value):
    if value >= UNLIMITED_CONSEC:
        return storage.L(32060)
    return storage.L(32061).format(value)


def _sequence(item):
    """Ordered playables for one title (episodes / set films / single movie)."""
    if item['type'] == 'movieset':
        return library.get_movieset_playables(item['dbid'])
    if item['type'] == 'tvshow':
        return library.get_episode_playables(item['dbid'])
    return library.get_movie_playables(item['dbid'])


def _row(label, selected=False, label2=''):
    """A list row; selected rows get Property(sel)=1 -> the skin's deep-blue bar."""
    item = xbmcgui.ListItem(label=label)
    if label2:
        item.setLabel2(label2)
    if selected:
        item.setProperty('sel', '1')
    return item


# ============================================================================
# The editor window
# ============================================================================

class ChannelEditor(xbmcgui.WindowXMLDialog):
    """Sidebar + panel + Save/Cancel editor for one channel working dict."""

    def __init__(self, *args, **kwargs):
        self.channel = kwargs.get('channel')
        self.is_new = kwargs.get('is_new', False)
        self.saved = False
        self.catalog = []          # library titles for the Titles checklist
        self.file_items = []       # folder items on this channel (the File filter
                                   # universe - there is no global folder catalog)
        self.starteps_titles = []  # multi-item titles shown in Starting eps
        self.filters = {'tvshow': True, 'movieset': True, 'movie': True, 'folder': True}
        self.search_query = ''

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def onInit(self):
        self._set_heading()
        for control_id, string_id in STATIC_LABELS:
            self.getControl(control_id).setLabel(storage.L(string_id))
        self._fill_categories()
        self.catalog = library.get_catalog()
        # Snapshot the channel's folder items - this is the File filter's universe
        # (copied so a deselected folder stays listable for re-selection until Save).
        self.file_items = [dict(item) for item in self.channel['items']
                           if item['type'] == 'folder']
        for _control_id, (type_key, on_image) in FILTER_TOGGLE.items():
            self.getControl(on_image).setVisible(self.filters[type_key])
        self._fill_titles()
        self._fill_mode()
        self._fill_consec_mode()
        self._fill_consec()
        self._fill_starteps()
        self._fill_artwork()
        self._fill_name()
        self.setFocusId(CAT_LIST)

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self.close()          # Back == Cancel
            return
        # The visible panel follows the sidebar highlight automatically (XML).
        # We only need to step focus INTO the current panel when Right is pressed.
        if self.getFocusId() == CAT_LIST and action_id == ACTION_MOVE_RIGHT:
            self._focus_panel()

    def onClick(self, control_id):
        if control_id == SAVE_BTN:
            self._save()
        elif control_id == CANCEL_BTN:
            self.close()
        elif control_id == CAT_LIST:
            self._focus_panel()
        elif control_id == NAME_BTN:
            self._edit_name()
        elif control_id in FILTER_TOGGLE:
            self._toggle_filter(control_id)
        elif control_id == SEARCH_BTN:
            self._edit_search()
        elif control_id == TITLES_LIST:
            self._toggle_title()
        elif control_id == MODE_LIST:
            self._choose_mode()
        elif control_id == CONSEC_MODE_BTN:
            self._toggle_consec_mode()
        elif control_id == CONSEC_LIST:
            self._choose_consec()
        elif control_id == STARTEPS_LIST:
            self._choose_start_episode()
        elif control_id == ART_LIST:
            self._choose_artwork()

    # ------------------------------------------------------------------
    # Panel focus
    # ------------------------------------------------------------------

    def _focus_panel(self):
        """Move focus into the panel for the currently highlighted category."""
        position = self.getControl(CAT_LIST).getSelectedPosition()
        self.setFocusId(PANEL_FIRST.get(position, NAME_BTN))

    # ------------------------------------------------------------------
    # Populate fields from the working copy
    # ------------------------------------------------------------------

    def _set_heading(self):
        verb = storage.L(32020) if self.is_new else storage.L(32021)
        name = self.channel['name'] or storage.L(32023)
        self.getControl(HEADING).setLabel('{0}:  {1}'.format(verb, name))

    def _fill_categories(self):
        control = self.getControl(CAT_LIST)
        control.reset()
        for string_id in CATEGORY_IDS:
            control.addItem(xbmcgui.ListItem(label=storage.L(string_id)))

    def _fill_name(self):
        self.getControl(NAME_BTN).setLabel(self.channel['name'] or storage.L(32022))

    def _fill_titles(self):
        """Rebuild the title checklist from the cached catalog, honouring the type
        filters and the search query, grouped under bold section headers."""
        chosen = {_key(item) for item in self.channel['items']}
        query = self.search_query.lower().strip()
        control = self.getControl(TITLES_LIST)
        control.reset()
        for type_key, _control_id, header_id in TYPE_SECTIONS:
            if not self.filters.get(type_key, True):
                continue
            # Library types come from the catalog; folders from the channel snapshot
            # (there is no global folder catalog to browse here).
            if type_key == 'folder':
                members = list(self.file_items)
            else:
                members = [i for i in self.catalog if i['type'] == type_key]
            if query:
                members = [i for i in members if query in i['title'].lower()]
            if not members:
                continue
            head = xbmcgui.ListItem(label=storage.L(header_id))
            head.setProperty('kind', 'header')
            control.addItem(head)
            for item in members:
                row = _row(_title_text(item), selected=_key(item) in chosen)
                row.setProperty('kind', 'item')
                row.setProperty('key', _key(item))
                control.addItem(row)

    def _fill_mode(self):
        control = self.getControl(MODE_LIST)
        control.reset()
        for value, string_id in MODES:
            control.addItem(_row(storage.L(string_id), selected=value == self.channel['mode']))

    def _fill_consec_mode(self):
        """Label the toggle: 'Always' (fixed run) vs 'Up to' (maximum cap)."""
        always = self.channel.get('consec_always', False)
        self.getControl(CONSEC_MODE_BTN).setLabel(
            storage.L(32066) if always else storage.L(32065))

    def _consec_options(self):
        """Count choices for the current mode. 'Always' drops Unlimited (you cannot
        always play an unlimited run before switching)."""
        if self.channel.get('consec_always'):
            return [v for v in MAX_CONSEC_OPTIONS if v < UNLIMITED_CONSEC]
        return MAX_CONSEC_OPTIONS

    def _fill_consec(self):
        control = self.getControl(CONSEC_LIST)
        control.reset()
        for value in self._consec_options():
            control.addItem(_row(_consec_label(value),
                                 selected=value == self.channel['max_consecutive']))

    def _fill_starteps(self):
        self.starteps_titles = [i for i in self.channel['items']
                                if i['type'] in ('tvshow', 'movieset')]
        control = self.getControl(STARTEPS_LIST)
        control.reset()
        if not self.starteps_titles:
            control.addItem(_row(storage.L(32027)))
            return
        for item in self.starteps_titles:
            control.addItem(_row(item['title'], label2=self._start_label(item)))

    def _fill_artwork(self):
        control = self.getControl(ART_LIST)
        control.reset()
        current = self.channel.get('art_source_key')
        control.addItem(_row(storage.L(32062), selected=not current))
        for item in self.channel['items']:
            control.addItem(_row(_title_text(item), selected=_key(item) == current))

    def _start_label(self, item):
        """Current starting-episode label for one show / set."""
        sequence = _sequence(item)
        if not sequence:
            return storage.L(32028)
        index = self.channel['start_points'].get(_key(item), 0)
        if not 0 <= index < len(sequence):
            index = 0
        return sequence[index]['label']

    # ------------------------------------------------------------------
    # Field edits
    # ------------------------------------------------------------------

    def _select_only(self, control, position):
        """Mark exactly one row selected (deep-blue bar) in a single-choice list."""
        for i in range(control.size()):
            control.getListItem(i).setProperty('sel', '1' if i == position else '')

    def _edit_name(self):
        name = xbmcgui.Dialog().input(storage.L(32026), defaultt=self.channel['name'])
        if name:
            self.channel['name'] = name
            self._fill_name()
            self._set_heading()

    def _toggle_filter(self, control_id):
        """Flip one type filter; show/hide its deep-blue 'on' layer and rebuild."""
        type_key, on_image = FILTER_TOGGLE[control_id]
        self.filters[type_key] = not self.filters[type_key]
        self.getControl(on_image).setVisible(self.filters[type_key])
        self._fill_titles()

    def _edit_search(self):
        query = xbmcgui.Dialog().input(storage.L(32025), defaultt=self.search_query)
        self.search_query = query or ''
        self.getControl(SEARCH_BTN).setLabel(self.search_query or storage.L(32024))
        self._fill_titles()

    def _toggle_title(self):
        item = self.getControl(TITLES_LIST).getSelectedItem()
        if item is None or item.getProperty('kind') != 'item':
            return                                   # a section header - ignore
        key = item.getProperty('key')
        if any(_key(i) == key for i in self.channel['items']):
            self.channel['items'] = [i for i in self.channel['items'] if _key(i) != key]
            item.setProperty('sel', '')
        else:
            source = next((i for i in self.catalog if _key(i) == key), None)
            if source is None:   # folders live in the snapshot, not the catalog
                source = next((i for i in self.file_items if _key(i) == key), None)
            if source is not None:
                self.channel['items'].append(source)
            item.setProperty('sel', '1')
        # Titles drive the Starting-eps and Artwork panels - rebuild them.
        self._fill_starteps()
        self._fill_artwork()

    def _choose_mode(self):
        control = self.getControl(MODE_LIST)
        position = control.getSelectedPosition()
        self.channel['mode'] = MODES[position][0]
        self._select_only(control, position)

    def _toggle_consec_mode(self):
        """Flip Up-to <-> Always. Entering Always hides Unlimited (and snaps a
        currently-Unlimited count down to 2); leaving Always brings it back."""
        always = not self.channel.get('consec_always', False)
        self.channel['consec_always'] = always
        if always and self.channel['max_consecutive'] >= UNLIMITED_CONSEC:
            self.channel['max_consecutive'] = 2
        self._fill_consec()        # rebuild with/without Unlimited for the new mode
        self._fill_consec_mode()

    def _choose_consec(self):
        control = self.getControl(CONSEC_LIST)
        position = control.getSelectedPosition()
        self.channel['max_consecutive'] = self._consec_options()[position]
        self._select_only(control, position)

    def _choose_start_episode(self):
        if not self.starteps_titles:
            return
        control = self.getControl(STARTEPS_LIST)
        position = control.getSelectedPosition()
        item = self.starteps_titles[position]
        sequence = _sequence(item)
        if not sequence:
            xbmcgui.Dialog().ok(storage.NAME, storage.L(32031).format(item['title']))
            return
        labels = [entry['label'] for entry in sequence]
        current = self.channel['start_points'].get(_key(item), 0)
        preselect = current if 0 <= current < len(sequence) else 0
        choice = xbmcgui.Dialog().select(storage.L(32032).format(item['title']),
                                         labels, preselect=preselect)
        if choice >= 0:
            self.channel['start_points'][_key(item)] = choice
            control.getListItem(position).setLabel2(sequence[choice]['label'])

    def _choose_artwork(self):
        control = self.getControl(ART_LIST)
        position = control.getSelectedPosition()
        # Row 0 is Random; rows 1.. map to channel items.
        if position == 0:
            self.channel['art_source_key'] = None
        else:
            self.channel['art_source_key'] = _key(self.channel['items'][position - 1])
        self._select_only(control, position)

    # ------------------------------------------------------------------
    # Save / cancel
    # ------------------------------------------------------------------

    def _save(self):
        if not self.channel['name']:
            xbmcgui.Dialog().ok(storage.NAME, storage.L(32029))
            self.setFocusId(CAT_LIST)
            return
        if not self.channel['items']:
            xbmcgui.Dialog().ok(storage.NAME, storage.L(32030))
            self.setFocusId(CAT_LIST)
            return
        self.saved = True
        self.close()


# ----------------------------------------------------------------------------
# Entry point used by gui.py
# ----------------------------------------------------------------------------

def _within(home, prop, seconds, now):
    """True if `prop` holds a timestamp newer than `seconds` ago."""
    value = home.getProperty(prop)
    if not value:
        return False
    try:
        return now - float(value) < seconds
    except ValueError:
        return False


def run(addon_path, channel, is_new):
    """Open the editor on `channel` (a working dict). Returns True if saved.
    Rejected (returns False, opens nothing) when another editor is already open or
    one closed a moment ago - so a buffered/stray add/edit dispatch can never stack
    a second dialog or re-pop a blank editor."""
    home = xbmcgui.Window(_GUARD_WINDOW)
    now = time.time()
    if _within(home, _BUSY_PROP, _BUSY_MAX_SECONDS, now):     # an editor is already open
        return False
    if _within(home, _GUARD_PROP, _GUARD_SECONDS, now):       # one closed a moment ago
        return False

    home.setProperty(_BUSY_PROP, str(now))
    try:
        dialog = ChannelEditor('script-channelme-editor.xml', addon_path, 'Default', '1080i',
                               channel=channel, is_new=is_new)
        dialog.doModal()
        saved = dialog.saved
        del dialog
    finally:
        home.setProperty(_BUSY_PROP, '')
        home.setProperty(_GUARD_PROP, str(time.time()))
    return saved
