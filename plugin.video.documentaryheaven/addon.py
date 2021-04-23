import sys
from resources.lib.script import router

if __name__ == "__main__":
    paramstring = sys.argv[2][1:]
    router(paramstring)
