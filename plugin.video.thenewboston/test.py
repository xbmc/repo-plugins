from resources.lib import tnb


def test_get_categories_returns_categories():
    """Should return categories (live test)."""
    categories = tnb.get_categories()
    assert all([isinstance(c['title'], unicode) for c in categories])


def test_get_most_popular_topics():
    """Should return most popular topics."""
    topics = tnb.get_topics(u'Most Popular Courses')
    assert all([isinstance(t['lesson_id'], int) for t in topics])


def test_get_topics():
    """Should return a list of topic dicts."""
    topics = tnb.get_topics(u'Computer Programming')
    assert all([
        isinstance(t['lesson_id'], int) and isinstance(t['title'], unicode)
        for t in topics])


def test_get_lessons():
    """Should return a list of lessons."""
    lessons = tnb.get_lessons(6)
    assert isinstance(lessons[0], dict)


def test_get_lessons():
    """Should return a list of lessons."""
    video = tnb.get_video(3, 16676)
    assert video == u'DLElzmuhrnY'
