import json
import os
from httplib2 import Http
import mimetypes
import hashlib

from apiclient import discovery, errors
from apiclient.http import MediaFileUpload

from oauth2client.client import OAuth2Credentials

class DirectorySync(object):
    def __init__(self, drive, path, folder_id, callback):
        self.drive = drive
        self.fs_path = path
        self.drive_folder_id = folder_id
        self.conflict_callback = callback

    def sync_dir(self, path=None, folder_id=None):
        import pdb; pdb.set_trace()
        if path is None:
            path = self.fs_path
        if folder_id is None:
            folder_id = self.drive_folder_id
        
        if folder_id is None:
            folder_id = self.drive.create_folder(os.path.basename(path))["id"]

        fs_entries = [os.stat(os.path.join(path, x)) for x in os.listdir(path)]
        fs_entry_map = {x.name: x for x in fs_entries}
        fs_files = [x.name for x in fs_entries if x.is_file()]
        fs_dirs = [x.name for x in fs_entries if x.is_dir()]

        drive_entries = list(self.search(parents=folder_id, trashed=True))
        drive_entry_map = {x["name"]: x for x in drive_entries }
        drive_files = [x["name"] for x in drive_entries if x["mimeType"] != self.folder_mime]
        drive_folders = [x["name"] for x in drive_entries if x["mimeType"] == self.folder_mime]

        

    def sync_file(self, fs_file, drive_file):
        if os.path.isfile(fs_file.path) and not drive_file["trashed"]: #Both exist
            if md5(fs_path) == drive_file["md5Checksum"]:
                return
            print "Both do not have the same time"
    
    def fs_get_info(self, path):
        stat = os.stat(path)
        return {
            "name": os.basename(path),
            "md5Checksum": self.md5(path),
            "lastModified": datetime.utcfromtimestamp(stat.st_mtime),
        }

    def md5(self, path):
        hash_md5 = hashlib.md5()
        with open(path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hash_md5.update(buf)
                buf = f.read(blocksize)
            return hash_md5.digest()


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
    
    def sync_dir(self, folder_id, path, callback):
        ds = DirectorySync(self, path, folder_id, callback)
        ds.sync_dir()

    def iterate_dir(self, dir_id, parents=None):
        if parents is None:
            parents = []
        for entry in self.list_dir(dir_id):
            yield entry, parents
            if entry["mimeType"] == self.folder_mime:
                parents.insert(0, dir_id)
                recur_res = self.iterate_dir(entry["id"], parents=parents)
                for child, parents in recur_res:
                    yield child, parents
                parents.pop(0)
    
    def list_dir(self, dir_id):
        for obj in self.search(parents=dir_id):
            yield obj

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
        field_list = ["id", "mimeType", "name", "createdTime", "modifiedTime",
                "version", "md5Checksum"]
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
            if isinstance(kwargs["parents"], basestring):
                kwargs["parents"] = [kwargs["parents"]]
            for parent in kwargs.pop("parents"):
                query.append("'{}' in parents".format(parent))

        for key, value in kwargs.items():
            if isinstance(value, basestring):
                query.append("{} = '{}'".format(key, value))
            elif type(value) == bool:
                query.append("{} = {}".format(key, str(value).lower()))
            elif type(value) == int:
                query.append("{} = {}".format(key, value))
        query_str = " and ".join(query)
        #TODO: Make this into a generator that automatically uses nextPageToken
        return self.service.files().list(q=query_str).execute()["files"]

    def share(self, file_id, **kwargs):
        return self.service.permissions().create(fileId=file_id, body=kwargs).execute()


