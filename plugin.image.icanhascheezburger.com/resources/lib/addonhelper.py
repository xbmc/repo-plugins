class AddonHelper:
    def __init__(self):
        self.lol_url = {30214: 'http://feeds.feedburner.com/ICanHasCheezburger',
                        30215: 'http://feeds.feedburner.com/IHasAHotdog',
                        30216: 'http://feeds.feedburner.com/PunditKitchen',
                        30217: 'http://feeds.roflrazzi.com/ROFLrazzi/',
                        30218: 'http://feeds.feedburner.com/failblog',
                        30219: 'http://feeds.feedburner.com/EngrishFunny'
                       }
        self.url_enum_map = {}
        start = 30211
        for i in range(0, 18):
            self.url_enum_map[i] = start
            start += 1

    def get_current_lol_url(self, id):
        if id in self.lol_url:
            return(self.lol_url[id])
        else:
            return('')

    def get_current_lol_url_by_enum(self, enum):
        e = int(enum)
        if e in self.url_enum_map:
            return(self.get_current_lol_url(self.url_enum_map[e]))

