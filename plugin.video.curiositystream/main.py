import sys
from resources.lib import router

if __name__ == "__main__":
    router = router.Router(plugin_url=sys.argv[0], plugin_handle=int(sys.argv[1]))
    router.route(sys.argv[2])
