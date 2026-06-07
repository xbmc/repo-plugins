class RTPPlayConfig:
    def __init__(self, config):
        rtp_play_json_config = config.get("config", {})
        self.AUTH_URL_ENDPOINT = rtp_play_json_config.get("auth_url", "")
        self.BASE_API_URL_ENDPOINT = rtp_play_json_config.get("base_api_url", "")  # base url endpoint for all requests
        self.SEARCH_URL_ENDPOINT = rtp_play_json_config.get("search_url", "")  # for search requests
        self.PEER5 = rtp_play_json_config.get("peer5", "") == 1
        self.DVR_CHANNELS = rtp_play_json_config.get("dvr_channels", [])
        self.MENU = [{ent["type"]: ent["title"]} for ent in config.get("menu", [])]  # home, live, programs, podcasts
        self.SHELFS = config.get("shelfs", [])  # the sections displayed on the main page
