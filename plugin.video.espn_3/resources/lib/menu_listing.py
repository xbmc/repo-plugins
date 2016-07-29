ROOT = ''


class MenuListing:
    def __init__(self, place):
        self.place = place

    def make_mode(self, destination):
        return '/' + self.place + '/' + destination
