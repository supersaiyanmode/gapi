import json
import os.path
from httplib2 import Http
import mimetypes

from apiclient import discovery, errors
from apiclient.http import MediaFileUpload

from oauth2client.client import OAuth2Credentials

class Drive(object):
    public_folder = "GAPI4TermPublic"
    folder_mime = "application/vnd.google-apps.folder"

    def __init__(self, cred):
        credentials = OAuth2Credentials.from_json(json.dumps(cred))
        http = credentials.authorize(Http())
        self.service = discovery.build("drive", "v3", http=http)
    
    def share_public_link(self, file_id):
        res = self.share_file(file_id, "reader", "anyone")
        fields = ["webContentLink"]
        file_obj = self.get_file_by_id(file_id, fields=fields)
        return file_obj["webContentLink"]
    
    def share_file(self, file_id, role, typ):
        body = {
            "value": "",
            "role": role,
            "type": typ
        }
        res = self.service.permissions().create(fileId=file_id, body=body).execute()
        return res["id"]

    def public_upload(self, path):
        parent_id = self.get_public_dir()
        return self.upload(parent_id, path)

    def upload(self, parent, path):
        mime, encoding = mimetypes.guess_type(path)
        if not mime and not encoding:
            mime = "application/octet-stream"

        name = os.path.basename(path)
        media = MediaFileUpload(path, mimetype=mime)
        body = {
            "mimeType": mime,
            "title": name,
            "name": name,
            "parents": [parent],
        }
        res = self.service.files().create(media_body=media, body=body).execute()
        return res["id"]
    
    def get_file_by_id(self, file_id, fields=None):
        field_list = ["id", "mimeType", "name"]
        if fields is not None:
            field_list = field_list + fields
        fields_str = ",".join(field_list)
        return self.service.files().get(
                fileId=file_id,
                fields=fields_str).execute()


    def get_public_dir(self):
        query = ["mimeType='%s'"%self.folder_mime,
                "name = '%s'"%self.public_folder,
                "'root' in parents",
                "trashed=false"]
        query_str = " and ".join(query)
        try:
            results = self.service.files().list(
                    q=query_str).execute()
        except Exception, e:
            print e
            raise
        folders = results["files"]
        if len(folders):
            return folders[0]["id"]
        else:
            return self.create_public_dir()

    def create_public_dir(self):
        body = {
            "mimeType": self.folder_mime,
            "title": self.public_folder,
            "name": self.public_folder,
            "description": "Public folder created by GAPI4Term",
            "parents": ["root"],
        }
        res = self.service.files().create(body=body).execute()
        print "Created directory in Google Drive:", self.public_folder
        return res["id"]



