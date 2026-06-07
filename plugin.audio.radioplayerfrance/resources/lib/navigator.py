from resources.lib.api import RadioplayerAPI
from resources.lib.errors import ApiError
from resources.lib.ui import KodiUI
from resources.lib.i18n import _

class Navigator:
    def __init__(self, ui: KodiUI):
        self.ui = ui
        self.api = RadioplayerAPI()

    def list_root(self):
        self.ui.add_dir(_("Recommended"), "list_recommended")
        self.ui.add_dir(_("Categories"), "list_categories")
        self.ui.end_directory()

    def list_recommended(self):
        try:
            stations = self.api.get_recommended_stations()
        except ApiError as e:
            self.ui.notify_error(str(e))
            return

        for station in stations:
            self.ui.add_playable(
                label=station["name"],
                url=self.ui.build_url("play_stream", stream_id=station["id"]),
                icon=station["image_url"],
            )
        self.ui.end_directory()

    def list_radios(self, category_id: int):
        try:
            stations = self.api.get_radios(category_id)
        except ApiError as e:
            self.ui.notify_error(str(e))
            return

        for station in stations:
            self.ui.add_playable(
                label=station["name"],
                url=self.ui.build_url("play_stream", stream_id=station["id"]),
                icon=station["image_url"],
            )
        self.ui.end_directory()

    def list_categories(self):
        try:
            categories = self.api.get_categories()
        except ApiError as e:
            self.ui.notify_error(str(e))
            return

        for category in categories:
            self.ui.add_dir(
                label=category["name"],
                action="list_radios",
                category_id=category["id"]
            )
        self.ui.end_directory()

    def play_stream(self, stream_id: int):
        try:
            stream_url = self.api.get_stream_url(stream_id)
        except ApiError as e:
            self.ui.notify_error(str(e))
            return

        self.ui.resolve_url(stream_url)

