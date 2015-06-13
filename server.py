from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json

listenAddr = "128.199.82.190"
listenPort = 7654
secretKey = ""  # TODO:implement the secure feature of GitHub webhook


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        if self.headers['X-Github-Event'] == 'pull_request':
            data = json.loads(post_body)

            # new PR opened
            if data['action'] == 'opened':
                print("New Pull Request opened")
                info = {'title': data['pull_request']['title'], 'creator': data['pull_request']['user']['login'],
                        'id': data['pull_request']['id'], 'link': data['pull_request']['html_url'],
                        'content': data['pull_request']['body']}
                to_print = json.dumps(info, sort_keys=True, indent=2)
                print(to_print)
                print("======================================")


myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool prototype")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))