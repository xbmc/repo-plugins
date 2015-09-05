from resources.lib import abcradionational


def test_get_playable_podcast_returns_content():
    
    soup = abcradionational.get_soup("http://abc.net.au/radionational/podcasts")
    
    podcasts = abcradionational.get_playable_podcast(soup)

    assert type(podcasts) == list
