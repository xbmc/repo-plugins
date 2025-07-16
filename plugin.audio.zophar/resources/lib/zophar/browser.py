import requests

from .parsers import GameListPage, PagesSupported, parse_page, parse_searchpage

BASE_URL = "https://www.zophar.net"
SEARCH_PATH = "/music/search"


def get_page(path: str, **params: str) -> str:
    return requests.get(BASE_URL + path, params).text


def home():
    html = get_page(SEARCH_PATH)
    return parse_searchpage(html)


def page(path: str, **params: str) -> PagesSupported:
    html = get_page(path, **params)
    return parse_page(html)


def gamelist(path: str, page_num: int) -> GameListPage:
    html = get_page(path, page=str(page_num))
    page = parse_page(html)
    assert isinstance(page, GameListPage)
    return page


def search(context: str, console: str) -> GameListPage:
    html = get_page(SEARCH_PATH, search=context, search_consoleid=console)
    page = parse_page(html)
    assert isinstance(page, GameListPage)
    assert page.total_pages == 1
    return page
