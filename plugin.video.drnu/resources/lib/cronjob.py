from cron import CronManager, CronJob
import json


cmd_js = {
    "jsonrpc": "2.0",
    "method": "Addons.ExecuteAddon",
    "params": {
        "addonid": "plugin.video.drnu",
        "params": ["?reCache=2"]
        },
    "id": "1"
}


def setup_cronjob(addon_path, bool_setting, get_setting):
    manager = CronManager()
    job = None
    for job in manager.getJobs():
        if job.name == "plugin.video.drnu cronjob":
            job = manager.getJob(job.id)
            break
    if bool_setting('recache.cronjob'):
        if job is None:
            job = CronJob()
        if (job.command == json.dumps(cmd_js)) and (job.expression == get_setting('recache.cronexpression')):
            # same job, no update
            return

        # add job, with new settings
        job.name = "plugin.video.drnu cronjob"
        job.command_type = "json"  # this is set to "built-in" by default
        job.command = json.dumps(cmd_js)
        job.expression = get_setting('recache.cronexpression')
        job.show_notification = "false"
        manager.addJob(job)
    else:
        if job is not None:
            manager.deleteJob(job.id)
