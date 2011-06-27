from domain.multi_media_type import MultiMediaType

class RedditPost:
    kind = None
    domain = None
    media_embed = None
    levenshtein = None
    subreddit = None
    selfText = None
    selfText_html = None
    likes = None
    saved = None
    id = None
    clicked = None
    author = None
    media = None
    score = None
    over_18 = None
    hidden = None
    thumbnail = None
    subreddit_id = None
    downs = None
    is_self = None
    permalink = None
    name = None
    created = None
    url = None
    title = None
    created_utc = None
    num_comment = None
    ups = None
    
    def getMultiMediaType(self):
        return MultiMediaType().getTypeFromUrl(self.url)
