from xbmcswift2 import xbmcgui, xbmc
import math
import os

import utils


class TextBox(xbmcgui.ControlButton):
    """
    Adds some additional methods to the ControlButton class to
    behave a) more like a HTML input field and b) to present a
    polymorphic interface for all controls used on the quiz page
    """
    @property
    def canUpdateLabel(self):
        return True

    def getContent(self):
        return self.getLabel()

    def updateLabel(self):
        label = self.getLabel()
        keyboard = xbmc.Keyboard(label)
        keyboard.doModal()
        self.setLabel(
            keyboard.getText())

    def updateContent(self, content):
        self.setLabel(content)


class RadioButton(xbmcgui.ControlRadioButton):
    """
    Adds some additional methods to the ControlRadioButton class to present
    a polymorphic interface for all controls used on the quiz page
    """
    @property
    def canUpdateLabel(self):
        return False

    def getContent(self):
        return self.isSelected()

    def updateContent(self, content):
        self.setSelected(content)


class FormQuiz(xbmcgui.WindowDialog):
    def __init__(self):
        xbmcgui.Window.__init__(self)
        self.width = 1280
        self.height = 720
        self.bottom_height = 70
        self.widget_y_offset = 5
        self.widget_y_multiplier_offset = 70
        self.button_width = 100
        self.button_height = 50
        self.radio_button_width = 30
        self.radio_button_height = 30
        self.text_box_width = 100
        self.text_box_height = 50
        self.button_text_colour = '0xFFFFFFFF'
        self.button_spacing = 130
        self.button_y_pos = 660
        self.button_x_pos = 1100

    def build(
            self, course_id, lesson_id, group_id, quiz_id,
            quiz_data, last_submission_data, udacity, plugin):
        self.udacity = udacity
        self.data = quiz_data['data']
        self.widgets = []
        self.plugin = plugin
        self.course_id = course_id
        self.lesson_id = lesson_id
        self.group_id = group_id
        self.quiz_id = quiz_id

        bg_image_path = (
            plugin.addon.getAddonInfo('path') + os.sep +
            'resources' + os.sep + 'media' + os.sep + 'blank.png')

        self.addControl(xbmcgui.ControlImage(
            0, 0, self.width, self.height, bg_image_path)
        )
        if '_background_image' in self.data:
            url = 'http:' + self.data['_background_image']['serving_url']
            self.addControl(xbmcgui.ControlImage(
                x=0, y=0, width=self.width,
                height=self.height - self.bottom_height, filename=url))

        widgets = self.data['widgets']
        for widget in widgets:
            model = widget['model']
            x = int(math.ceil(
                widget['placement']['x'] * self.width))
            y = int(math.ceil(
                widget['placement']['y'] *
                (self.height - self.widget_y_multiplier_offset)) -
                self.widget_y_offset)

            if model == 'TextInputWidget' or model == 'NumericInputWidget':
                widget_height = int(
                    self.height * widget['placement']['height'])
                widget_width = int(
                    self.width * widget['placement']['width'])
                obj = TextBox(
                    x=x, y=y, height=widget_height, width=widget_width,
                    label='', textColor="0xFF000000", shadowColor='0xFF000000')
            else:
                obj = RadioButton(
                    x=x, y=y,
                    height=self.radio_button_height,
                    width=self.radio_button_width, label='')

            self.addControl(obj)

            if last_submission_data:
                for part in last_submission_data['parts']:
                    if part['marker'] == widget['marker']:
                        obj.updateContent(part['content'])

            self.widgets.append({
                'obj': obj, 'data': widget})

        self.submit_button = xbmcgui.ControlButton(
            x=self.button_x_pos, y=self.button_y_pos, width=self.button_width,
            height=self.button_height, shadowColor='0xFF000000',
            label=self.plugin.get_string(30013), font='font13',
            textColor=self.button_text_colour)

        self.back_button = xbmcgui.ControlButton(
            x=self.button_x_pos - self.button_spacing,
            y=self.button_y_pos, width=self.button_width,
            height=self.button_height, label=self.plugin.get_string(30014),
            font='font13', textColor=self.button_text_colour)

        self.addControl(self.submit_button)
        self.addControl(self.back_button)

    def onControl(self, control):
        if control == self.back_button:
            self.close()
            return
        elif control == self.submit_button:
            control.setLabel(self.plugin.get_string(30015))
            answer_data = utils.widgets_to_answer(self.widgets)
            result = self.udacity.submit_quiz(self.data['key'], answer_data)
            if self.udacity.auth.is_authenticated:
                if not self.udacity.update_submission_activity(
                    self.course_id, self.lesson_id, self.group_id,
                        self.quiz_id, result['evaluation'],
                        answer_data['submission']):
                    # Submission wasn't updated correctly
                    self.plugin.log.error(self.udacity.error)
            dialog = xbmcgui.Dialog()
            dialog.ok('Result', result['evaluation']['comment'])
            if result['evaluation']['passed'] is not False:
                self.close()
                return
            else:
                control.setLabel(self.plugin.get_string(30013))
        else:
            for count, widget in enumerate(self.widgets):
                if control == widget['obj'] and widget['obj'].canUpdateLabel:
                    self.widgets[count]['obj'].updateLabel()
