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
        res = self.share(file_id, role="reader", type="anyone")
        fields = ["webContentLink"]
        file_obj = self.get_file(file_id, fields=fields)
        return file_obj["webContentLink"]
    
    def public_upload(self, path):
        parent_id = self.get_public_dir()
        return self.create_file(path, parents=parent_id)

    def get_public_dir(self):
        folders = self.search(parents="root", isFolder=True, name=self.public_folder)
        if len(folders):
            return folders[0]["id"]
        else:
            return self.create_public_dir()

    def create_public_dir(self):
        opts = {
            "parents": ["root"],
            "description": "Public folder created by GAPI4Term"
        }
        return self.create_folder(self.public_folder, **opts)["id"]



    ###########################
    # CORE FUNCTIONALITY BELOW
    #

    def create_folder(self, name, **kwargs):
        kwargs["mimeType"] = self.folder_mime
        kwargs["name"] = name
        return self.create_file(None, **kwargs)

    def create_file(self, path, **kwargs):
        if "mimeType" not in kwargs and path:
            mime, encoding = mimetypes.guess_type(path)
            if not mime and not encoding:
                mime = "application/octet-stream"
            kwargs["mimeType"] = mime

        if "name" not in kwargs and path:
            kwargs["name"] = os.path.basename(path)

        if "title" not in kwargs and "name" in kwargs:
            kwargs["title"] = kwargs["name"]

        if "parents" in kwargs and isinstance(kwargs["parents"], basestring):
            kwargs["parents"] = [kwargs["parents"]]
        
        if path:
            media = MediaFileUpload(path, mimetype=kwargs["mimeType"])
            return self.service.files().create(media_body=media, body=kwargs).execute()
        else:
            return self.service.files().create(body=kwargs).execute()

    def get_file(self, file_id, fields=None):
        field_list = ["id", "mimeType", "name"]
        if fields is not None:
            field_list = field_list + fields
        fields_str = ",".join(field_list)
        return self.service.files().get(fileId=file_id,fields=fields_str).execute()


    def search(self, trashed=False, *args, **kwargs):
        query = list(args)
        kwargs["trashed"] = trashed

        if "isFolder" in kwargs:
            if kwargs.pop("isFolder"):
                kwargs["mimeType"] = self.folder_mime

        if "parents" in kwargs:
            if type(kwargs["parents"]) == str:
                kwargs["parents"] = [kwargs["parents"]]
            for parent in kwargs.pop("parents"):
                query.append("'{}' in parents".format(parent))

        for key, value in kwargs.items():
            if type(value) == str:
                query.append("{} = '{}'".format(key, value))
            elif type(value) == bool:
                query.append("{} = {}".format(key, str(value).lower()))
            elif type(value) == int:
                query.append("{} = {}".format(key, value))
        query_str = " and ".join(query)
        print "Query:", query_str
        return self.service.files().list(q=query_str).execute()["files"]

    def share(self, file_id, **kwargs):
        return self.service.permissions().create(fileId=file_id, body=kwargs).execute()


