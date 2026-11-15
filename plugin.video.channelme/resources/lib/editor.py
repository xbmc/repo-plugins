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
from resources.lib import valueprompt

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
WEIGHT_LIST = 5203       # per-show selection weight (right column of the Mode panel)
MODE_HEADER = 5204       # left column header ("Mode")
WEIGHT_HEADER = 5205     # right column header ("Selection weight")
CONSEC_HINT = 5302
CONSEC_MODE_BTN = 5303   # "Up to" / "Always" toggle (channel default)
BIAS_LIST = 5304         # per-show back-to-back override (right column of the panel)
BIAS_HEADER = 5305       # right column header ("Per-show")
DEFAULT_HEADER = 5306    # left column header ("Channel default")
CONSEC_SLIDER = 5307     # channel default back-to-back (focusable overlay; Left/Right = adjust)
CONSEC_VALUE = 5308      # inline numeric readout beside the capsule
CONSEC_PROGRESS = 5309   # the fill track
CONSEC_HANDLE = 5310     # the dull knob (shown when hovered, not editing)
CONSEC_HANDLE_LIVE = 5314  # the white knob (shown while editing)
CONSEC_FRAME = 5311      # the idle (grey) capsule frame - always shown

# Capsule handle geometry (absolute, matching the skin): knob left at 0%, its travel range,
# the track (progress) width and knob width for the "fill to the knob's right edge" maths.
CONSEC_KNOB_LEFT, CONSEC_KNOB_TRAVEL, CONSEC_HANDLE_Y = 564, 276, 398
CONSEC_INNER_W, CONSEC_KNOB_W = 312, 36
# The three visual states (idle grey -> hover white -> edit blue) are driven entirely by the
# skin (colour-fixed images gated on Control.HasFocus + the 'cm_edit' window property).
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
    # Two-column panel headers (Mode: weight | Back-to-back: per-show).
    (MODE_HEADER, 32003), (WEIGHT_HEADER, 32055),
    (DEFAULT_HEADER, 32067), (BIAS_HEADER, 32068),
]

# ----------------------------------------------------------------------------
# Kodi action IDs we care about
# ----------------------------------------------------------------------------

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2

# ----------------------------------------------------------------------------
# Field option tables
# ----------------------------------------------------------------------------

# (stored value, label string id)
MODES = [('serial_random', 32050), ('pure_random', 32051)]

# Back-to-back run length is a 1..30 slider (single-step, for fine control). The old
# "Unlimited" option is gone; a legacy value is clamped into range on load.
UNLIMITED_CONSEC = 999
CONSEC_MIN, CONSEC_MAX = 1, 30


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


def _clamp_consec(value):
    """Fold a stored back-to-back count (incl. a legacy 'Unlimited' 999) into 1..30."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 2
    return max(CONSEC_MIN, min(CONSEC_MAX, value))


def _weight_label(value):
    """Per-show selection weight: 1.0 == 'Normal', otherwise e.g. '1.2x' / '3x'."""
    if not value or value <= 1:
        return storage.L(32056)          # Normal
    return storage.L(32057).format('{0:g}'.format(value))


def _bias_label(entry):
    """Per-show back-to-back override: 'Default' (inherit), else 'Up to N' / 'Always N'
    ('Up to Unlimited' when the count is unlimited). `entry` is None or {count, always}."""
    if not entry:
        return storage.L(32063)          # Default (inherit the channel setting)
    word = storage.L(32066) if entry.get('always') else storage.L(32065)
    count = entry.get('count', 0)
    amount = storage.L(32060) if count >= UNLIMITED_CONSEC else str(count)
    return '{0} {1}'.format(word, amount)


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
        self.consec_editing = False   # channel-default slider: hover vs edit (two-stage)

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
        self._fill_weights()
        self._fill_consec_mode()
        self._init_consec()
        self._fill_bias()
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
        # The channel-default slider only steps the count while EDITING; when merely
        # hovered the arrows navigate normally (so you can reach the toggle / lists).
        elif self.getFocusId() == CONSEC_SLIDER and self.consec_editing:
            if action_id == ACTION_MOVE_LEFT:
                self._step_consec(-1)
            elif action_id == ACTION_MOVE_RIGHT:
                self._step_consec(1)

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
        elif control_id == WEIGHT_LIST:
            self._choose_weight()
        elif control_id == CONSEC_MODE_BTN:
            self._toggle_consec_mode()
        elif control_id == CONSEC_SLIDER:
            self._set_consec_editing(not self.consec_editing)
        elif control_id == BIAS_LIST:
            self._choose_bias()
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

    def _fill_weights(self):
        """Right column of the Mode panel: each channel title with its selection
        weight ('Normal' unless biased). Weight decides how OFTEN a title is picked."""
        control = self.getControl(WEIGHT_LIST)
        control.reset()
        if not self.channel['items']:
            control.addItem(_row(storage.L(32058)))
            return
        weights = self.channel.get('weight_overrides', {})
        for item in self.channel['items']:
            control.addItem(_row(_title_text(item),
                                 label2=_weight_label(weights.get(_key(item), 1))))

    def _fill_consec_mode(self):
        """Label the toggle: 'Always' (fixed run) vs 'Up to' (maximum cap)."""
        always = self.channel.get('consec_always', False)
        self.getControl(CONSEC_MODE_BTN).setLabel(
            storage.L(32066) if always else storage.L(32065))

    def _init_consec(self):
        """Seed the channel-default back-to-back slider (1..30) from the working copy."""
        self.channel['max_consecutive'] = _clamp_consec(self.channel.get('max_consecutive', 2))
        self._paint_consec()
        self._set_consec_editing(False)

    def _set_consec_editing(self, editing):
        """Two-stage: enter/leave edit mode. Editing traps the arrows for value changes,
        lights the capsule frame and brightens the knob."""
        self.consec_editing = editing
        slider = self.getControl(CONSEC_SLIDER)
        if editing:
            slider.setNavigation(slider, slider, slider, slider)
        else:
            slider.setNavigation(self.getControl(CONSEC_MODE_BTN), slider,
                                 self.getControl(CAT_LIST), self.getControl(BIAS_LIST))
        # The skin swaps frame/knob colours on this property (idle/hover vs editing).
        self.setProperty('cm_edit', '1' if editing else '')

    def _step_consec(self, direction):
        """Nudge the channel default count by +/-1 (called on Left/Right while editing)."""
        self.channel['max_consecutive'] = _clamp_consec(
            self.channel['max_consecutive'] + direction)
        self._paint_consec()

    def _paint_consec(self):
        """Repaint the numeric readout, the fill percent and the handle position."""
        count = self.channel['max_consecutive']
        self.getControl(CONSEC_VALUE).setLabel(str(count))
        fraction = (count - CONSEC_MIN) / float(CONSEC_MAX - CONSEC_MIN)
        # Fill to the knob's RIGHT edge so the bar reads as filled up to the knob.
        fill_percent = (fraction * CONSEC_KNOB_TRAVEL + CONSEC_KNOB_W) * 100.0 / CONSEC_INNER_W
        self.getControl(CONSEC_PROGRESS).setPercent(fill_percent)
        handle_x = CONSEC_KNOB_LEFT + int(fraction * CONSEC_KNOB_TRAVEL)
        self.getControl(CONSEC_HANDLE).setPosition(handle_x, CONSEC_HANDLE_Y)
        self.getControl(CONSEC_HANDLE_LIVE).setPosition(handle_x, CONSEC_HANDLE_Y)

    def _fill_bias(self):
        """Right column of the Back-to-back panel: each channel title with its
        back-to-back override ('Default' == inherit the channel setting on the left)."""
        control = self.getControl(BIAS_LIST)
        control.reset()
        if not self.channel['items']:
            control.addItem(_row(storage.L(32058)))
            return
        overrides = self.channel.get('consec_overrides', {})
        for item in self.channel['items']:
            control.addItem(_row(_title_text(item),
                                 label2=_bias_label(overrides.get(_key(item)))))

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
            # A deselected title keeps no per-show overrides.
            self.channel.get('consec_overrides', {}).pop(key, None)
            self.channel.get('weight_overrides', {}).pop(key, None)
            item.setProperty('sel', '')
        else:
            source = next((i for i in self.catalog if _key(i) == key), None)
            if source is None:   # folders live in the snapshot, not the catalog
                source = next((i for i in self.file_items if _key(i) == key), None)
            if source is not None:
                self.channel['items'].append(source)
            item.setProperty('sel', '1')
        # Titles drive the per-show weight / back-to-back / Starting-eps / Artwork
        # panels - rebuild them all.
        self._fill_weights()
        self._fill_bias()
        self._fill_starteps()
        self._fill_artwork()

    def _choose_mode(self):
        control = self.getControl(MODE_LIST)
        position = control.getSelectedPosition()
        self.channel['mode'] = MODES[position][0]
        self._select_only(control, position)

    def _choose_weight(self):
        """Slider prompt (1.0..3.0) for the highlighted title's selection weight.
        Default / a weight of 1.0 clears the override (the title then weighs Normal)."""
        if not self.channel['items']:
            return
        control = self.getControl(WEIGHT_LIST)
        position = control.getSelectedPosition()
        item = self.channel['items'][position]
        weights = self.channel.setdefault('weight_overrides', {})
        current = float(weights.get(_key(item), 1.0))
        result = valueprompt.show('weight', storage.L(32054).format(item['title']), current)
        if result is None:                    # cancelled
            return
        if result == 'default':
            weights.pop(_key(item), None)
        else:
            weights[_key(item)] = result
        control.getListItem(position).setLabel2(_weight_label(weights.get(_key(item), 1.0)))

    def _toggle_consec_mode(self):
        """Flip the channel default between 'Up to' (cap) and 'Always' (fixed run)."""
        self.channel['consec_always'] = not self.channel.get('consec_always', False)
        self._fill_consec_mode()

    def _choose_bias(self):
        """Slider prompt (Up to/Always + 1..30) for the highlighted title's back-to-back
        override. Default clears it so the title follows the channel setting on the left."""
        if not self.channel['items']:
            return
        control = self.getControl(BIAS_LIST)
        position = control.getSelectedPosition()
        item = self.channel['items'][position]
        overrides = self.channel.setdefault('consec_overrides', {})
        current = overrides.get(_key(item))
        init_count = _clamp_consec(current['count']) if current \
            else _clamp_consec(self.channel.get('max_consecutive', 2))
        init_always = current.get('always') if current \
            else self.channel.get('consec_always', False)
        result = valueprompt.show('consec', storage.L(32064).format(item['title']),
                                  init_count, always=init_always)
        if result is None:                    # cancelled
            return
        if result == 'default':
            overrides.pop(_key(item), None)
        else:
            overrides[_key(item)] = result
        control.getListItem(position).setLabel2(_bias_label(overrides.get(_key(item))))

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
