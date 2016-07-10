import json

from httplib2 import Http

from apiclient import discovery, errors
from oauth2client.client import OAuth2Credentials

class URLShortener(object):
    def __init__(self, cred):
        credentials = OAuth2Credentials.from_json(json.dumps(cred))
        http = credentials.authorize(Http())
        self.service = discovery.build('urlshortener', 'v1', http=http)

    def shorten(self, arg):
        _, longUrl = arg
        request = {"longUrl": longUrl}
        return self.service.url().insert(body=request).execute()
