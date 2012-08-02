CHANNELS = list()

class Channel(object):
    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url

        CHANNELS.append(self)


Channel(1, 'Specific Radio', 'shout://stream.specific.dk/SR')
Channel(2, 'Specific Mainstram Radio', 'shout://stream.specific.dk/MS')
Channel(3, 'The Voice', 'shout://195.184.101.203/voice128')
Channel(4, 'Radio 100', 'shout://onair.100fmlive.dk/100fm_live.mp3')
Channel(5, 'Radio 100 Soft', 'shout://onair.100fmlive.dk/soft_live.mp3')
Channel(6, 'Radio 100 Klassisk', 'shout://onair.100fmlive.dk/klassisk_live.mp3')
Channel(7, 'Nova FM', 'shout://195.184.101.204/nova128')
Channel(8, 'Radio24syv', 'rtmp://fl1.sz.xlcdn.com/live/sz=Radio24syv=ENC1_Web256 live=1')
Channel(9, 'Pop FM','shout://195.184.101.202/pop128')
Channel(10, 'Radio VLR', 'shout://streaming.fynskemedier.dk/vlr')
Channel(11, 'ANR', 'shout://icecast.xstream.dk/anr')
Channel(12, 'NRJ', 'mms://85.233.229.254:8000/NRJ')
Channel(13, 'Radio ABC', 'shout://abc.radiostreaming.dk:8050/')
Channel(14, 'Radio Alfa - \xD8stjylland', 'shout://alfa.radiostreaming.dk:8050/')
Channel(15, 'Radio Alfa - Midtjylland', 'shout://midtjylland.radiostreaming.dk:8050/')
Channel(16, 'Radio Alfa - Sydfyn', 'shout://icecast3.radiostuff.dk:8000/Alfasydfyn128')
Channel(17, 'Radio Aura', 'shout://icecast.xstream.dk/aura')
Channel(18, 'Skala.fm', 'shout://netradio.skala.fm/high')
Channel(19, 'Radio Mojn', 'shout://mojn.radiostreaming.dk:8050/')
Channel(20, 'Radio Skive', 'shout://skive.radiostreaming.dk:8050/')