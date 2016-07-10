import json
import os
from httplib2 import Http
import mimetypes
import hashlib
from datetime import datetime

from apiclient import discovery, errors
from apiclient.http import MediaFileUpload

from oauth2client.client import OAuth2Credentials

import iso8601
import pytz

class DirectorySync(object):
    def __init__(self, drive, path, folder_id, callback):
        self.drive = drive
        self.fs_path = path
        self.drive_folder_id = folder_id
        self.conflict_callback = callback

    def sync(self, path=None, folder_id=None):
        if path is None:
            path = self.fs_path
        if folder_id is None:
            folder_id = self.drive_folder_id
        
        if folder_id is None:
            print "Creating folder:", path
            folder_id = self.drive.create_folder(os.path.basename(path))["id"]
        
        fs_entries = [self.fs_get_info(os.path.join(path, x)) for x in os.listdir(path)]
        fs_entry_map = {x["name"]: x for x in fs_entries}
        fs_files = {x["name"] for x in fs_entries if x["isFile"]}
        fs_dirs = {x["name"] for x in fs_entries if x["isDir"]}

        drive_entries = list(self.drive.search(parents=folder_id) + self.drive.search(
                                parents=folder_id, trashed=True))
        drive_entry_map = {x["name"]: x for x in drive_entries }
        drive_files = {x["name"] for x in drive_entries if x["mimeType"] != self.drive.folder_mime}
        drive_dirs = {x["name"] for x in drive_entries if x["mimeType"] == self.drive.folder_mime}
        
        for name in drive_files | fs_files:
            print "Syncing file:", os.path.join(path, name), "..",
            self.sync_file(path, folder_id, name,
                    fs_entry_map.get(name), drive_entry_map.get(name))

        for name in fs_dirs | drive_dirs: #Exists in FS, not in drive: Create
            child_dir = os.path.join(path, name)
            print "Syncing folder:", child_dir, "..",
            dir_id = self.sync_dir(path, folder_id, name,
                    fs_entry_map.get(name), drive_entry_map.get(name))
            self.sync(os.path.join(path, name), dir_id or drive_entry_map.get(name)["id"])
            
    def sync_dir(self, path, folder_id, name, fs_dir, drive_dir):
        if fs_dir is None and drive_dir:
            if drive_dir.get("trashed"):
                print "Was deleted on drive; untouched on FS"
                return
            os.mkdir(os.path.join(path, name))
            print "Created directory:", os.path.join(path, name)
        elif fs_dir and not drive_dir:
            res = self.drive.create_folder(name=name, parents=folder_id)
            print "Created folder on Drive"
            return res["id"]
        elif fs_dir and not drive_dir.get("trashed"):
            print "In Sync"
        else:
            print "[UNKNOWN]"


    def sync_file(self, path, folder_id, name, fs_file, drive_file):
        if fs_file is None and drive_file:
            if drive_file.get("trashed"):
                print "Was deleted on drive; untouched on FS"
                return
            print "TODO: Download:", os.path.join(path, name)
        elif fs_file and not drive_file:
            self.drive.create_file(fs_file["path"], parents=folder_id)
            print "Doesn't exist in drive; Uploaded."
        else: #Both exist
            if self.md5(fs_file["path"]) == drive_file["md5Checksum"] and not drive_file.get("trashed"):
                print "In Sync"
                return
            if drive_file["lastModified"] > fs_file["lastModified"]: #Drive file is newer
                if drive_file.get("trashed"):
                    print "Deleted on Drive; Deleted on FS"
                    os.remove(os.path.join(path, name))
                else:
                    print "TODO: Download:", os.path.join(path, name)
            else:
                self.drive.create_file(fs_file["path"], parents=folder_id)
                print "Newer version on FS; Uploaded."
    
    def fs_get_info(self, path):
        stat = os.stat(path)
        modifiedTime = datetime.utcfromtimestamp(stat.st_mtime)
        modifiedTime = pytz.utc.localize(modifiedTime)
        isDir = os.path.isdir(path)
        isFile = os.path.isfile(path)
        return {
            "isFile": isFile,
            "isDir": isDir,
            "name": os.path.basename(path),
            "path": path,
            "md5Checksum": self.md5(path) if isFile else None,
            "lastModified": modifiedTime,
        }

    def md5(self, path, blocksize=65536):
        hash_md5 = hashlib.md5()
        with open(path, 'rb') as f:
            buf = f.read(blocksize)
            while len(buf) > 0:
                hash_md5.update(buf)
                buf = f.read(blocksize)
            return hash_md5.hexdigest()


class Drive(object):
    public_folder = "GAPI4TermPublic"
    folder_mime = "application/vnd.google-apps.folder"
    default_fields = ["id", "mimeType", "name", "createdTime", "modifiedTime",
                "version", "md5Checksum"]

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
        ds.sync()

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
        cur_fields = self.default_fields
        if fields is not None:
            cur_fields = cur_fields + fields
        fields_str = ",".join(cur_fields)
        return self.service.files().get(fileId=file_id,fields=fields_str).execute()


    def search(self, trashed=False, fields=None, *args, **kwargs):
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

        cur_fields = self.default_fields + (fields or [])
        fields_str = ",".join("files/" + x for x in cur_fields)

        result = self.service.files().list(q=query_str, fields=fields_str).execute()["files"]
        for res in result:
            res["lastModified"] = iso8601.parse_date(res["modifiedTime"])
        return result

    def share(self, file_id, **kwargs):
        return self.service.permissions().create(fileId=file_id, body=kwargs).execute()


