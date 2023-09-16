import sys

from resources.lib.podcasts.actions.commit_gpodder import CommitGPodderAction
from resources.lib.podcasts.actions.commit_nextcloud import CommitNextcloudAction
from resources.lib.podcasts.actions.download_gpodder_subscriptions_action import DownloadGpodderSubscriptionsAction
from resources.lib.podcasts.actions.export_opml_action import ExportOpmlAction
from resources.lib.podcasts.actions.import_gpodder_subscriptions_action import ImportGPodderSubscriptionsAction
from resources.lib.podcasts.actions.import_opml_action import ImportOpmlAction
from resources.lib.podcasts.actions.search_fyyd_action import SearchFyydAction
from resources.lib.podcasts.actions.sync_nextcloud_subscriptions_action import SyncNextcloudSubscriptionsAction
from resources.lib.podcasts.actions.unassign_opml_action import UnassignOpmlAction
from resources.lib.podcasts.podcastsaddon import PodcastsAddon

if __name__ == '__main__':

    if sys.argv[1] == "import_gpodder_subscriptions":
        importGPodderSubscriptionsAction = ImportGPodderSubscriptionsAction()
        importGPodderSubscriptionsAction.import_gpodder_subscriptions(
            "True" == sys.argv[2])

    elif sys.argv[1] == "download_gpodder_subscriptions":
        downloadGpodderSubscriptionsAction = DownloadGpodderSubscriptionsAction()
        downloadGpodderSubscriptionsAction.download_gpodder_subscriptions()

    elif sys.argv[1] == "import_opml":
        importOpmlAction = ImportOpmlAction()
        importOpmlAction.import_opml()

    elif sys.argv[1] == "unassign_opml":
        unassignOpmlAction = UnassignOpmlAction()
        unassignOpmlAction.unassign_opml()

    elif sys.argv[1] == "commit_gpodder":
        commitGPodderAction = CommitGPodderAction()
        commitGPodderAction.commit_gpodder()

    elif sys.argv[1] == "commit_nextcloud":
        commitNextcloudAction = CommitNextcloudAction()
        commitNextcloudAction.commit_nextcloud()

    elif sys.argv[1] == "sync_nextcloud_subscriptions":
        syncNextcloudSubscriptionsAction = SyncNextcloudSubscriptionsAction()
        syncNextcloudSubscriptionsAction.sync_nextcloud_subscriptions(
            "True" == sys.argv[2], "True" == sys.argv[3])

    elif sys.argv[1] == "export_to_nextcloud":
        syncNextcloudSubscriptionsAction = SyncNextcloudSubscriptionsAction()
        syncNextcloudSubscriptionsAction.export_to_nextcloud()

    elif sys.argv[1] == "export_opml":
        exportOpmlAction = ExportOpmlAction()
        exportOpmlAction.export_opml()

    elif sys.argv[1] == "search_fyyd":
        searchFyydAction = SearchFyydAction()
        searchFyydAction.search_fyyd()

    else:
        podcastsAddon = PodcastsAddon(int(sys.argv[1]))
        podcastsAddon.handle(sys.argv)
        syncNextcloudSubscriptionsAction = SyncNextcloudSubscriptionsAction()
        syncNextcloudSubscriptionsAction.check_for_updates()
