import re
from resources.lib.kodiutils import AddonUtils
from resources.lib.webutils import WebScraper


class Kvartal():

    addon_utils = AddonUtils()
    shows = [{"name": addon_utils.localize(30000), "suburl": "den-svenska-modellen"},
             {"name": addon_utils.localize(30001), "suburl": "fredagsintervjun"},
             {"name": addon_utils.localize(30002), "suburl": "inlasta-essaer"},
             {"name": addon_utils.localize(30003), "suburl": "veckopanelen"}]

    def __init__(self):
        self.scraper = WebScraper()

    def get_content(self, show_id):
        base_url = "https://feeder.acast.com/api/v1/shows"
        content_url = "{0}/{1}".format(base_url, self.shows[show_id]["suburl"])
        show = self.scraper.get_json(content_url)
        for episode in show["episodes"]:
            summary = self._extract_string_from_html(episode["summary"])
            item = {"label": episode["title"],
                    "summary": summary,
                    "date": episode["publishDate"].split("T")[0],
                    "media_url": episode["url"],
                    "image_url": show["image"]}
            yield item

    def get_show_summary(self, show_id):
        base_url = "https://feeder.acast.com/api/v1/shows"
        content_url = "{0}/{1}".format(base_url, self.shows[show_id]["suburl"])
        show = self.scraper.get_json(content_url)
        summary = self._extract_string_from_html(show["description"])
        return summary[:-2]

    def _extract_string_from_html(self, summary_html):
        start = 0
        stop = summary_html.find("&#10") - 1
        summary = summary_html[start:stop]
        pattern = re.compile("<(.*?)>")
        summary = pattern.sub("", summary).replace("&nbsp;", " ")
        summary = re.sub(r" +", " ", summary)
        return summary
