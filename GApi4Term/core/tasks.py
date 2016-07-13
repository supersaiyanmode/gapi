import json
from httplib2 import Http

from apiclient import discovery, errors

from oauth2client.client import OAuth2Credentials

class Tasks(object):
    DEFAULT_LIST = "To Do"

    def __init__(self, cred):
        credentials = OAuth2Credentials.from_json(json.dumps(cred))
        http = credentials.authorize(Http())
        self.service = discovery.build("tasks", "v1", http=http)
    
    def list_tasks(self, title):
        tasklist = self.get_list_by_title(title)
        if not tasklist:
            return None
        tid = tasklist['id']
        return self.list_tasks_by_list_id(tid)

    def list_tasks_by_list_id(self, tlid):
        res = self.service.tasks().list(tasklist=tlid).execute()
        for task in res['items']:
            yield self.get_task(tlid, task["id"])

    def get_list_by_title(self, title):
        for task_list in self.get_all_tasklists():
            if task_list['title'] == title:
                return task_list

    def get_all_tasklists(self):
        for x in self.service.tasklists().list().execute()['items']:
            yield x

    def get_task(self, tlid, tid):
        return self.service.tasks().get(tasklist=tlid, task=tid).execute()
