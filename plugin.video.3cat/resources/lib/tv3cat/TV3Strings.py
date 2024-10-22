from builtins import object
class TV3Strings(object):

    def __init__(self, addon):
        self.addon = addon
        self.strs = {
            'avuidestaquem': 30001,
            'noperdis': 30002,
            'mesvist': 30003,
            'programes': 30004,
            'series': 30005,
            'informatius': 30006,
            'entreteniment': 30007,
            'esports': 30008,
            'documentals': 30009,
            'divulgacio': 30010,
            'cultura': 30011,
            'musica': 30012,
            'tots': 30013,
            'emissio': 30014,
            'seguent': 30015,
            'anterior': 30016,
            'directe': 30017,
            'tv3': 30018,
            'canal324': 30019,
            'sx3': 30020,
            'esport3': 30021,
            'cercar': 30022,
            'coleccions': 30023,
            'tv3_int': 30024,
            'canal324_int': 30025,
            'c33super3_int': 30026,
            'esport3_int': 30027
        }

    def get(self, string):
        code = self.strs[string]
        st = self.addon.getLocalizedString(code).encode("utf-8")

        return st