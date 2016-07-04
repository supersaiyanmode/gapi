from httplib2 import Http
import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate
from time import mktime
from datetime import datetime
import mimetypes
import os
import json

from apiclient import discovery, errors
from oauth2client.client import OAuth2Credentials

class GMailMessage(object):
    def __init__(self, gmail, frm, to, subject):
        self.gmail = gmail
        self.message = MIMEMultipart()
        self.message["to"] = ", ".join(to)
        self.message["from"] = frm
        self.message["subject"] = subject
    
    def text(self, txt):
        msg = MIMEText(txt)
        self.message.attach(msg)
        return self

    def file(self, path):
	print "Attaching:", path
	content_type, encoding = mimetypes.guess_type(path)

	if content_type is None or encoding is not None:
	    content_type = 'application/octet-stream'

	main_type, sub_type = content_type.split('/', 1)

	if main_type == 'text':
	    fp = open(path, 'rb')
	    msg = MIMEText(fp.read(), _subtype=sub_type)
	    fp.close()
	elif main_type == 'image':
	    fp = open(path, 'rb')
	    msg = MIMEImage(fp.read(), _subtype=sub_type)
	    fp.close()
	elif main_type == 'audio':
	    fp = open(path, 'rb')
	    msg = MIMEAudio(fp.read(), _subtype=sub_type)
	    fp.close()
	else:
	    fp = open(path, 'rb')
	    msg = MIMEBase(main_type, sub_type)
	    msg.set_payload(fp.read())
	    fp.close()

	filename = os.path.basename(path)
	msg.add_header('Content-Disposition', 'attachment', filename=filename)
	self.message.attach(msg)
	return self
    
    def html(self, html):
	msg = MIMEText(html, 'html')
	self.message.attach(msg)
	return self

    def send(self):
        return self.gmail.send({'raw': base64.urlsafe_b64encode(self.message.as_string())})
 

class GMail(object):
    def __init__(self, cred):
        credentials = OAuth2Credentials.from_json(json.dumps(cred))
        http = credentials.authorize(Http())
        self.service = discovery.build('gmail', 'v1', http=http)
        self.profile = self.service.users().getProfile(userId="me").execute()

    def create_message(self, to, subject):
	frm = self.profile["emailAddress"]
        return GMailMessage(self, frm, to, subject)

    def send(self, obj):
	try:
	    print "sending:", obj["raw"]
	    message = (self.service.users().messages()
                    .send(userId="me", body=obj)
                    .execute())
            return message['id']
	except errors.HttpError, e:
	    return None

    def detail(self, message_id):
	def parse_message(msg):
	    headers = {obj["name"].lower(): obj["value"] for obj in msg["payload"]["headers"]}
	    subject = headers.get("subject", "(no subject)")
	    snippet = msg["snippet"]
	    author = headers["from"]
	    if "date" in headers:
		time = datetime.fromtimestamp(mktime(parsedate(headers["date"])))
	    else:
		time = datetime.fromtimestamp(int(msg["internalDate"])/1000)
	    return {
		"headers": headers, "subject": subject, "snippet": snippet,
		"author": author, "time": time}

	response = (self.service.users().threads().get(
		userId="me", id=message_id).execute())
	messages = map(parse_message, response["messages"])
	return {
	    "id": response["id"],
	    "subject": messages[0]["subject"],
	    "messages": messages
	}

    def list(self, page=0, count=10, labels=None, query=""):
	response = (self.service.users().threads().list(
		userId="me", maxResults=count, q=query).execute())
	if "threads" in response:
	    for x in response["threads"]:
		yield x



