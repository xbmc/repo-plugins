'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from bs4 import BeautifulSoup
import resources.lib.webget as webget
from resources.lib.kodiutils import AddonUtils
import requests
import re


class Filmarkivet():
    MOVIES_PER_PAGE = 50

    MAIN_MENU = [{'mode': 'categories', 'title': 30010},
                 {'mode': 'letters', 'title': 30011},
                 {'mode': 'themes', 'title': 30012},
                 {'mode': 'search', 'title': 30023}]

    class ListItem():
        def __init__(self, title, url, description, icon):
            self.title = title
            self.url = url
            self.description = description
            self.icon = icon
            self.playable = False
            self.year = None
            self.duration = None

    def __init__(self, addon_utils):
        self.addon_utils = addon_utils
        self.webget = webget.WebGet(self.addon_utils.cache_file)
        self.movies_regex = re.compile(".*Visar.*av (.*) filmer")
        self.meta_regex = re.compile("(\d+) / (\d+) min")

    def get_mainmenu(self):
        for item in self.MAIN_MENU:
            li = self.ListItem(self.addon_utils.localize(item["title"]),
                self.addon_utils.url_for("?mode={0}".format(item["mode"])), "", "")
            yield li

    def mode_url(self, mode):
        return "plugin://{0}?mode={1}".format(self.addon_utils.id, mode)

    def get_categories(self):
        html = self.webget.get_url("/")
        soup = BeautifulSoup(html, "html.parser")
        soup = soup.find("ul", {"class": "site-nav-menu"})
        lists = soup.find_all("ul")
        items = lists[0].find_all("li")
        mode_url = self.mode_url("category")

        for item in items[1:]:
            li = self.ListItem(item.a.string, "{0}&url={1}".format(mode_url,
                item.a["href"]), "", "")
            yield li

    def __get_range(self, soup):
        try:
            soup = soup.find("span", {"id": "pageSpan"})
            m_range = soup.string.split("-")
            t = soup.parent.get_text().strip()
            match = self.movies_regex.match(t)
            return [int(m_range[0]), int(m_range[1])], int(match.group(1))
        except Exception:
            return None, None

    def get_theme_categories(self, url):
        html = self.webget.get_url(url)
        soup = BeautifulSoup(html, "html.parser")
        soup = soup.find("div", {"class": "teacher-theme-list"})
        categories = soup.find_all("a")
        mode_url = self.mode_url("category")
        for category in categories:
            title = category.h2.text
            category_url = "{0}&url={1}".format(mode_url, category.get("href"))
            desc = ""
            try:
                category = category.find("img").get("data-lazy-src")
                category = category.split(",")[-1].replace(" ", "")
            except AttributeError:
                category = category.find("img").get("src")
                category = category.split(",")[-1].replace(" ", "")

            img = re.sub(r".jpg.*", ".jpg", category)
            li = self.ListItem(title, category_url, desc, img)
            li.playable = False
            yield li

    def get_url_movies(self, url, mode, page=1, limit=False):
        get_url = url
        if limit:
            get_url += "{0}limit={1}&pg={2}".format("?" if url.rfind("?") < 0
                else "&", self.MOVIES_PER_PAGE, page)
        html = self.webget.get_url(get_url)
        soup = BeautifulSoup(html, "html.parser")
        _range, range_max = self.__get_range(soup)
        soup = soup.find("div", {"id": "list"})
        movies = soup.find_all("a", {"class": "item"})
        mode_url = self.mode_url("watch")
        for movie in movies:
            title = movie.h3.contents[0].strip()
            movie_url = "{0}&url={1}".format(
                mode_url,
                requests.utils.quote(movie["href"].replace("#038;", "")))
            meta = movie.h3.span.string.strip()
            desc = "{0} ({1})".format(movie.p.string.strip(), meta)
            img = movie.figure.img["src"]
            li = self.ListItem(title, movie_url, desc, img)
            li.playable = True
            try:
                match = self.meta_regex.match(meta)
                if match:
                    li.year = int(match.group(1))
                    li.duration = int(match.group(2)) * 60
            except Exception:
                pass
            yield li

        if _range is not None and _range[1] < range_max:
            next_url = "{0}&url={1}&page={2}".format(self.mode_url(mode),
                requests.utils.quote(url), page + 1)
            li = self.ListItem(self.addon_utils.localize(30001), next_url, None, None)
            yield li

    def get_letters(self):
        mode_url = self.mode_url("letter")
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ":
            li = self.ListItem(letter, "{0}&l={1}".format(mode_url, letter), "", "")
            yield li

    def get_letter_movies(self, letter):
        html = self.webget.get_url("/filmer-a-o/")
        soup = BeautifulSoup(html, 'html.parser')
        soup = soup.find("section", {"class": "block", "id": letter.lower()})
        soup = soup.find("ul", {"class": "alphabetical"})
        movies = soup.find_all("a")
        mode_url = self.mode_url("watch")
        for movie in movies:
            title = movie.contents[0].strip()
            url = "{0}&url={1}".format(mode_url,
                requests.utils.quote(movie["href"]))
            li = self.ListItem(title, url, None, None)
            li.playable = True
            yield li

    def get_plot(self, content_url):
        html = self.webget.get_url(content_url)
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("meta", {"property": "og:description"}).get("content")

    def get_themes(self):
        html = self.webget.get_url("/")
        soup = BeautifulSoup(html, "html.parser")
        soup = soup.find("ul", {"class": "site-nav-menu"})
        lists = soup.find_all("ul")
        items = lists[1].find_all("li")
        mode_url = self.mode_url("theme")
        for item in items[1:]:
            li = self.ListItem(item.a.string, "{0}&url={1}".format(
                mode_url, requests.utils.quote(item.a["href"])),
                "", "")
            yield li

    def get_media_url(self, url):
        html = self.webget.get_url(url)
        soup = BeautifulSoup(html, "html.parser")
        media_info = soup.find("div", {"class": "video-container"})
        media_info = media_info.find("script", {"type": "text/javascript"}).decode()
        media_info = media_info.replace("\t", "")
        media_info = media_info.split("jQuery")[0]

        start = media_info.find("{") + 1
        end = media_info.rfind("}")
        media_info = media_info[start:end]

        for line in media_info.split("\n"):
            if line.startswith("//"):  # line is a javascript comment, ignore
                continue
            if ("https" in line or "http" in line) and ".mp4" in line:  # bingo! video url found
                start = line.find("\"") + 1
                end = line.rfind("\"")
                video_url = line[start:end]
                return video_url

        return None
