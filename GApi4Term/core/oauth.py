import webbrowser
import json
from urlparse import parse_qs
from threading import Thread
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer


from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import OAuth2Credentials

class OAuthWorkflow(object):
    def __init__(self, client_id, secret, redirect, callback):
	self.flow =  OAuth2WebServerFlow(
                client_id=client_id,
                client_secret=secret,
                scope='https://mail.google.com/',
                redirect_uri=redirect,
                prompt="consent")
        self.callback = callback

    def start(self):
        redirect_url = self.flow.step1_get_authorize_url()
        webbrowser.open_new(redirect_url)
        
    def on_code(self, code):
        print "Code:", code
        credentials = self.flow.step2_exchange(code)
        obj = json.loads(credentials.to_json())
        self.callback(obj)

class OAuthServer(object):

    def __init__(self, callback):
        self.callback = callback
        self.host = ""
        self.port = 9632
        self.url = "http://{}:{}/".format(
                self.host if self.host else "localhost",
                self.port)

    def run(self):
        oauthServer = self
        class OAuthServerHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if not self.path.startswith("/authCallback"):
                    self.send_response(404)
                    return
                path, query = self.path.split("?")
                code = parse_qs(query)["code"][0]
                self.send_response(301)
                self.send_header('Location','http://www.google.com')
                self.wfile.write("You can close this window.")
                self.wfile.close()
                Thread(target=oauthServer.callback, args=(code,)).start()

        server = HTTPServer((self.host, self.port), OAuthServerHandler)
        print "OAuth Server running"
        server.handle_request()
    

class GoogleAccounts(object):
    def __init__(self, config):
        self.client_id = config["APP"]["client_id"]
        self.secret = config["APP"]["secret"]
        self.config = config

    def add(self, *args):
        def on_credentials(cred):
            self.config.config["ACCOUNTS"] = cred
            self.config.update()

        server = OAuthServer(lambda code: oauth.on_code(code))
        Thread(target=server.run).start()
        url = server.url + "authCallback"
        oauth = OAuthWorkflow(self.client_id, self.secret, url, on_credentials)
        oauth.start()
        return 0

