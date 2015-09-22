__author__ = 'bromix'


class AbstractContextUI(object):
    def __init__(self):
        pass

    def create_progress_dialog(self, heading, text=None, background=False):
        raise NotImplementedError()

    def get_skin_id(self):
        raise NotImplementedError()

    def on_keyboard_input(self, title, default='', hidden=False):
        raise NotImplementedError()

    def on_numeric_input(self, title, default=None):
        raise NotImplementedError()

    def on_yes_no_input(self, title, text):
        raise NotImplementedError()

    def on_ok(self, title, text):
        raise NotImplementedError()

    def on_select(self, title, items, default=-1):
        raise NotImplementedError()

    def open_settings(self):
        raise NotImplementedError()

    def show_notification(self, message, header='', image_uri='', time_milliseconds=5000):
        raise NotImplementedError()

    def refresh_container(self):
        """
        Needs to be implemented by a mock for testing or the real deal.
        This will refresh the current container or list.
        :return:
        """
        raise NotImplementedError()

    pass
