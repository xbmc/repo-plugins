from urllib.parse import urlparse, parse_qsl
from resources.lib.webutils import WebScraper


class DocumentaryHeaven():
    BASE_URL = "https://documentaryheaven.com"

    def __init__(self):
        self.scraper = WebScraper()


    def get_documentaries(self, content_path, page=1):
        content_url = self.BASE_URL + content_path + "/page/" + str(page)
        html = self.scraper.get_html(content_url)
        documentaries = html.find_all("div", {"class": "post-thumbnail"})

        for documentary in documentaries:
            docu_info = {}
            try:
                docu_info["url"] = documentary.find("a", href=True).get("href")
            except AttributeError:
                continue

            try:
                docu_info["title"] = documentary.find("a", title=True).get("title")
            except AttributeError:
                docu_info["title"] = "no title"

            try:
                docu_info["icon"] = documentary.find("img", src=True).get("src")
            except AttributeError:
                docu_info["icon"] = None

            try:
                docu_info["plot"] = documentary.next_sibling.text
            except AttributeError:
                docu_info["plot"] = ""

            yield docu_info


    def get_categories(self):
        content_url = self.BASE_URL + "/watch-online"
        html = self.scraper.get_html(content_url)
        categories = html.find_all("a", {"class": "browse-all"})

        for category in categories:
            category_info = {}
            try:
                label = category.text
                start = len("Browse ")
                end = label.find(" Documentaries")
                label = label[start:end]
                category_info["label"] = label
                category_info["url"] = self.BASE_URL + category.get("href")[1:]

            except AttributeError:
                continue

            yield category_info


    def get_toplist(self, content_path):
        content_url = self.BASE_URL + content_path
        html = self.scraper.get_html(content_url)
        documentaries = html.find_all("a", {"itemprop": "url"})

        for (rank, documentary) in enumerate(documentaries):
            docu_info = {}
            try:
                docu_info["url"] = documentary.get("href")
            except AttributeError:
                continue

            try:
                title = documentary.get("title")
                docu_info["title"] = "{0}. {1}".format(rank+1, title)
            except AttributeError:
                docu_info["title"] = "no title"

            try:
                docu_info["icon"] = documentary.find("img", src=True).get("src")
            except AttributeError:
                docu_info["icon"] = None

            try:
                docu_info["plot"] = documentary.text
            except AttributeError:
                docu_info["plot"] = ""

            yield docu_info


    def search(self, query, offset):
        query = query.replace(" ", "+")
        search_url = "https://api.qwant.com/v3/search/web/?" \
            "q=site%3Adocumentaryheaven.com+AND+{0}" \
            "&count=10&locale=en_gb&offset={1}".format(query, offset)

        json = self.scraper.get_json(search_url)
        try:
            if json["status"] != "success":
                return ()

            contents = json["data"]["result"]["items"]["mainline"]
        except (AttributeError, KeyError):
            return ()

        for content in contents:
            try:
                if content["type"] == "web":
                    web_content = content
                    break
            except (KeyError, AttributeError):
                continue
        else:
            return ()

        try:
            web_content_items = web_content["items"]
        except (KeyError, AttributeError):
            return ()

        for item in web_content_items:
            documentary = {}

            try:
                documentary["title"] = item["title"].split(" | Docu")[0].split(" - Docu")[0]
                documentary["url"] = item["url"]
                documentary["plot"] = item["desc"]
            except (AttributeError, KeyError):
                continue

            # Only want urls corresponding to videos
            if ".com/all/" in documentary["url"] or \
                    ".com/best/" in documentary["url"] or \
                    ".com/category/" in documentary["url"] or \
                    ".com/popular/" in documentary["url"] or \
                    ".com/watch-online/" in documentary["url"] or \
                    ".com/page/" in documentary["url"] or \
                    documentary["url"] == self.BASE_URL or \
                    documentary["url"] == self.BASE_URL + "/":
                continue

            yield documentary


    def get_plot(self, documentary_path):
        documentary_url = self.BASE_URL + documentary_path
        html = self.scraper.get_html(documentary_url)
        plot = {}
        try:
            plot["title"] = html.find("meta", {"property": "og:title"}).get("content")
        except AttributeError:
            plot["title"] = ""

        try:
            plot["text"] = html.find("div", {"class": "entry-content"}).text
        except AttributeError:
            plot["text"] = ""

        return plot


    def get_documentary_info(self, documentary_path):
        documentary_url = self.BASE_URL + documentary_path
        html = self.scraper.get_html(documentary_url)

        video_url = html.find("meta", {"itemprop": "embedUrl"}).get("content")
        if "youtube.com/" in video_url:
            video_info = self._extract_youtube_info(video_url)
        elif "vimeo.com/" in video_url:
            video_info = self._extract_vimeo_info(video_url)
        elif "dailymotion.com/" in video_url:
            video_info = self._extract_dailymotion_info(video_url)
        elif "archive.org/" in video_url:
            video_info = self._extract_archive_info(video_url)

        return video_info


    @staticmethod
    def _extract_youtube_info(video_url):
        video = {}
        parsed_video_url = urlparse(video_url)
        video_path = parsed_video_url.path
        video_params = dict(parse_qsl(parsed_video_url.query))

        if "/embed/" in video_path:
            video["id"] = video_path.split("/embed/")[-1]
        elif "/p/" in video_path:
            video["id"] = video_path.split("/p/")[-1]
        else:
            video["id"] = None

        if video["id"] == "videoseries":
            video["id"] = video_params["list"]
            video["playlist"] = True
        else:
            try:
                video["id"] = video_params["list"]
                video["playlist"] = True
            except KeyError:
                video["playlist"] = False

        video["player"] = "youtube"
        return video


    @staticmethod
    def _extract_vimeo_info(video_url):
        video = {}
        parsed_video_url = urlparse(video_url)
        video_path = parsed_video_url.path
        video["id"] = video_path.split("video/")[-1]
        video["player"] = "vimeo"
        return video


    @staticmethod
    def _extract_dailymotion_info(video_url):
        video = {}
        parsed_video_url = urlparse(video_url)
        video_path = parsed_video_url.path
        video["id"] = video_path.split("video/")[-1]
        video["player"] = "dailymotion"
        return video


    def _extract_archive_info(self, video_url):
        video = {}
        html = self.scraper.get_html(video_url)
        try:
            path = html.find("meta", {"property": "og:video"}).get("content")
        except AttributeError:
            path = ""
        video["player"] = "archive"
        video["path"] = path
        return video
