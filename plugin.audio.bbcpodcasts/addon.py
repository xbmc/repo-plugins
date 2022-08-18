from resources.lib.bbcpodcasts.bbcpodcastsaddon import BbcPodcastsAddon
import sys

if __name__ == '__main__':

    bbcPodcastsAddon = BbcPodcastsAddon(int(sys.argv[1]))
    bbcPodcastsAddon.handle(sys.argv)
