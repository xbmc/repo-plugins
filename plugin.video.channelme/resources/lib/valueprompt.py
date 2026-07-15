# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - value prompt (a slider popup)
#
# A small modal used from the channel editor's per-show lists. Two shapes:
#   kind='consec' : an "Up to / Always" toggle + an integer 1..30 slider, for a show's
#                   back-to-back run.
#   kind='weight' : a float 1.0..3.0 slider, for a show's selection weight.
# Both offer OK / Default / Cancel. show() returns:
#   None       - cancelled,
#   'default'  - clear the per-show override (inherit / Normal),
#   value      - {'count': int, 'always': bool} for consec, or a float weight for weight.
#
# The "slider" is a progress bar (its fill shows the value) with a focusable transparent
# button on top; Left/Right on the button steps the value. We DON'T use xbmcgui's
# ControlSlider - in a custom window its nib texture renders at an uncontrollable size.
#
# Skin: resources/skins/Default/1080i/script-channelme-value.xml; keep the IDs in sync.

import xbmcgui

from resources.lib import storage

# ----------------------------------------------------------------------------
# Control IDs (must match the skin XML), actions and ranges
# ----------------------------------------------------------------------------

HEADING = 7000
TOGGLE = 7001
SLIDER = 7002          # focusable transparent button that captures Left/Right
VALUE = 7003
OK_BTN = 7004
DEFAULT_BTN = 7005
CANCEL_BTN = 7006
PROGRESS = 7008        # the fill bar under the button
HANDLE = 7009          # the dull knob (shown when hovered, not editing)
FRAME = 7010           # the idle (grey) capsule frame - always shown
HOVER = 7012           # the white frame - shown on hover
EDIT = 7013            # the blue frame - shown while editing
HANDLE_LIVE = 7014     # the white knob - shown while editing

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2

CONSEC_MIN, CONSEC_MAX = 1, 30
WEIGHT_MIN, WEIGHT_MAX, WEIGHT_STEP = 1.0, 3.0, 0.1

# Capsule geometry (absolute, matching the skin). The whole slider is one row: for consec
# it sits right of the toggle (base 840); for weight it fills across (base 720).
ROW_TOP = 470
BAR_W = 400
INSET = 4              # track inset inside the capsule frame
KNOB_W = 36
KNOB_TOP = ROW_TOP + 6
NUM_GAP = 10
BASE_CONSEC, BASE_WEIGHT = 840, 720
INNER_W = BAR_W - 2 * INSET                   # the track width
TRACK_TRAVEL = INNER_W - KNOB_W               # knob travel range across the track

# Three visual states are driven ENTIRELY by the skin (colour-fixed frame/knob images gated
# on Control.HasFocus + the 'cm_edit' window property): idle grey -> hovered white -> editing
# blue. Python only flips 'cm_edit'. (setColorDiffuse is ignored on the 9-slice frame.)


def _clamp(value, low, high):
    return max(low, min(high, value))


# ============================================================================
# The prompt window
# ============================================================================

class ValuePrompt(xbmcgui.WindowXMLDialog):
    """Slider popup for a per-show back-to-back run ('consec') or selection weight."""

    def __init__(self, *args, **kwargs):
        self.kind = kwargs.get('kind', 'consec')
        self.heading = kwargs.get('heading', '')
        self.always = bool(kwargs.get('always', False))
        if self.kind == 'consec':
            self.current = _clamp(int(kwargs.get('value', CONSEC_MIN)), CONSEC_MIN, CONSEC_MAX)
        else:
            self.current = round(_clamp(float(kwargs.get('value', WEIGHT_MIN)),
                                        WEIGHT_MIN, WEIGHT_MAX), 1)
        self.result = None
        self.editing = False        # two-stage: hover to navigate, click to edit

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def onInit(self):
        self.getControl(HEADING).setLabel(self.heading)
        self.getControl(OK_BTN).setLabel(storage.L(32213))
        self.getControl(DEFAULT_BTN).setLabel(storage.L(32063))     # Default
        self.getControl(CANCEL_BTN).setLabel(storage.L(32034))      # Cancel

        # Lay the one-row slider out for this kind: consec sits right of the toggle.
        self.base_x = BASE_CONSEC if self.kind == 'consec' else BASE_WEIGHT
        for control_id in (FRAME, HOVER, EDIT, SLIDER):
            self.getControl(control_id).setPosition(self.base_x, ROW_TOP)
        self.getControl(PROGRESS).setPosition(self.base_x + INSET, ROW_TOP + INSET)
        self.getControl(VALUE).setPosition(self.base_x + BAR_W + NUM_GAP, ROW_TOP)

        toggle = self.getControl(TOGGLE)
        if self.kind == 'consec':
            toggle.setVisible(True)
            self._paint_toggle()
        else:
            toggle.setVisible(False)
        self._paint()
        self._set_editing(False)
        self.setFocusId(SLIDER)

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self.result = None
            self.close()
            return
        # Left/Right only change the value while EDITING; when merely hovered they
        # navigate normally (so you can reach the Up to / Always toggle).
        if self.getFocusId() == SLIDER and self.editing:
            if action_id == ACTION_MOVE_LEFT:
                self._step(-1)
            elif action_id == ACTION_MOVE_RIGHT:
                self._step(1)

    def onClick(self, control_id):
        if control_id == SLIDER:
            self._set_editing(not self.editing)     # click to edit, click again to finish
        elif control_id == TOGGLE:
            self.always = not self.always
            self._paint_toggle()
        elif control_id == OK_BTN:
            self.result = self._read()
            self.close()
        elif control_id == DEFAULT_BTN:
            self.result = 'default'
            self.close()
        elif control_id == CANCEL_BTN:
            self.result = None
            self.close()

    # ------------------------------------------------------------------
    # Value + painting
    # ------------------------------------------------------------------

    def _step(self, direction):
        if self.kind == 'consec':
            self.current = int(_clamp(self.current + direction, CONSEC_MIN, CONSEC_MAX))
        else:
            self.current = round(_clamp(self.current + direction * WEIGHT_STEP,
                                        WEIGHT_MIN, WEIGHT_MAX), 1)
        self._paint()

    def _paint_toggle(self):
        self.getControl(TOGGLE).setLabel(storage.L(32066) if self.always else storage.L(32065))

    def _set_editing(self, editing):
        """Enter/leave edit mode: trap the arrows for value changes (vs normal nav) and
        light the knob up (dulled while only hovered)."""
        self.editing = editing
        slider = self.getControl(SLIDER)
        if editing:
            slider.setNavigation(slider, slider, slider, slider)   # arrows adjust, click exits
        elif self.kind == 'consec':
            toggle = self.getControl(TOGGLE)
            slider.setNavigation(toggle, self.getControl(DEFAULT_BTN), toggle, slider)
        else:
            slider.setNavigation(slider, self.getControl(DEFAULT_BTN), slider, slider)
        # The skin swaps frame/knob colours on this property (idle/hover vs editing).
        self.setProperty('cm_edit', '1' if editing else '')

    def _paint(self):
        if self.kind == 'consec':
            fraction = (self.current - CONSEC_MIN) / float(CONSEC_MAX - CONSEC_MIN)
            text = str(self.current)
        else:
            fraction = (self.current - WEIGHT_MIN) / float(WEIGHT_MAX - WEIGHT_MIN)
            text = storage.L(32056) if self.current <= 1.0 \
                else storage.L(32057).format('{0:g}'.format(self.current))
        # Fill to the knob's RIGHT edge (not its centre) so the bar looks filled up to it.
        fill_percent = (fraction * TRACK_TRAVEL + KNOB_W) * 100.0 / INNER_W
        self.getControl(PROGRESS).setPercent(fill_percent)
        self.getControl(VALUE).setLabel(text)
        knob_x = self.base_x + INSET + int(fraction * TRACK_TRAVEL)
        self.getControl(HANDLE).setPosition(knob_x, KNOB_TOP)
        self.getControl(HANDLE_LIVE).setPosition(knob_x, KNOB_TOP)

    def _read(self):
        if self.kind == 'consec':
            return {'count': int(self.current), 'always': self.always}
        return 'default' if self.current <= 1.0 else self.current


# ----------------------------------------------------------------------------
# Entry point used by the editor
# ----------------------------------------------------------------------------

def show(kind, heading, value, always=False):
    """Show the slider prompt and return None / 'default' / a value (see module docs)."""
    dialog = ValuePrompt('script-channelme-value.xml', storage.ADDON_PATH, 'Default', '1080i',
                         kind=kind, heading=heading, value=value, always=always)
    dialog.doModal()
    result = dialog.result
    del dialog
    return result
