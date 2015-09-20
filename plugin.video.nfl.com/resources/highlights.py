
from BeautifulSoup import BeautifulSoup

class Navigation:
    def __init__(self):
        self.nav = None
        self.team = None
        self.season = None
        self.season_type = None
        self.week = None
        self.game = None

    def get_navigation(self, html):
        ''' will parse the navigation for nfl highlights html into a dict
            e.g. http://www.nfl.com/big-play-highlights '''
        def parse_soup(soup):
            return [{'value':i['data-value'], 'href': i.a['href'],
                     'label': i.a.string, 'selected': i['class']} for
                         i in soup('li')]

        def set_selected(item_list):
            try:
                return [i['label'] for i in item_list if
                            'selected' in i['selected']][0]
            except IndexError:
                pass

        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        scripts = soup.findAll('script', attrs={'class': "page-nav-template"})
        nav = {}
        for i in scripts:
            if 'data-value="2013"' in i.contents[0]:
                nav['seasons'] = parse_soup(BeautifulSoup(i.contents[0],
                        convertEntities=BeautifulSoup.HTML_ENTITIES))
                self.season = set_selected(nav['seasons'])
            elif 'data-value="All Teams"' in i.contents[0]:
                nav['teams'] = parse_soup(BeautifulSoup(i.contents[0],
                        convertEntities=BeautifulSoup.HTML_ENTITIES))
                self.team = set_selected(nav['teams'])
            elif ('data-value="REG"' in i.contents[0] or 'data-value="PRE"' in
                    i.contents[0] or 'data-value="POST"' in i.contents[0]):
                nav['seasontypes'] = parse_soup(BeautifulSoup(i.contents[0],
                        convertEntities=BeautifulSoup.HTML_ENTITIES))
                self.season_type = set_selected(nav['seasontypes'])
            elif 'data-value="1"' in i.contents[0]:
                nav['weeks'] = parse_soup(BeautifulSoup(i.contents[0],
                        convertEntities=BeautifulSoup.HTML_ENTITIES))
                self.week = set_selected(nav['weeks'])
            else:
                try:
                    if int(i.contents[0].split('data-value="')[1].split('"')[0]
                           ) > 100000:
                        nav['games'] = parse_soup(BeautifulSoup(i.contents[0],
                                convertEntities=BeautifulSoup.HTML_ENTITIES))
                        self.game = set_selected(nav['games'])
                except:
                    pass

        self.nav = nav
        return nav


    def get_feed_url(self, href=None):
        ''' formats and returns the feed url for the given href
            e.g. /big-play-highlights/2013/REG/1 '''
        team = None
        season = None
        season_type = None
        week = None
        game = None
        base_url = ('http://www.nfl.com/feeds-rs/videos/byChannel/'
            'nfl-game-highlights')
        years = ['2010', '2011', '2012', '2013', '2014', '2015']
        season_types = ['PRE','REG', 'POST']

        if href is None:
            filter = '/bySeasonType/%s/%s' %(self.nav['seasons'][-1]['value'],
                    self.nav['seasontypes'][-1]['value'])
        else:
            items = href.split('/')
            try:
                week = str(int(items[-1].split('?')[0]))
            except:
                week = '1'
            if 'team=' in items[-1]:
                team = items[-1].split('team=')[1]
            elif 'gameId=' in items[-1]:
                game = items[-1].split('gameId=')[1]
            try: season = [i for i in items if i in years][0]
            except: pass
            try: season_type = [i for i in season_types if i in href][0]
            except: pass

            if season_type == 'POST':
                if int(week) in range(18, 23):
                    week = str(int(week) - 17)

            if team:
                if season_type == 'PRE':
                    filter = '/byTeam/%s/bySeasonType/%s/%s' %(
                            team, season, season_type)
                elif week == '100':
                    filter = '/byTeam/%s/bySeasonType/%s/%s' %(
                            team, season, season_type)
                else:
                    filter = '/byTeam/%s/byWeek/%s/%s/%s' %(
                            team, season, season_type, week)

            elif game:
                filter = '/byGame/%s' %game

            else:
                if season_type == 'PRE':
                    filter = '/bySeasonType/%s/%s' %(season, season_type)
                else:
                    filter = '/byWeek/%s/%s/%s' %(season, season_type, week)

        return '%s/%s.json?limit=16&offset=0' %(base_url, filter)