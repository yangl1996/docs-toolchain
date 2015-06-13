from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests

listenAddr = "128.199.82.190"
listenPort = 7654
secretKey = ""  # TODO:implement the secure feature of GitHub web hook (verify SHA1 signature)
pagureToken = "token 21HEK7SCCDNT12APRN00YJIY4AIYZM3DLXPNT8NP1275FA9MRWJZDM2ICWT8MYJX"
# TODO: this is a test propose token


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global pagureToken

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
                pagure_title = '[' + str(info['id']) + ']: ' + info['title'] + ' by ' + info['creator']
                # TODO: now containing all the metadata in the title, should use a more elegant solution
                pagure_payload = {'title': pagure_title, 'issue_content': info['content'],
                                  'status': "Open"}
                pagure_URL = "https://pagure.io/api/0/doc-test/new_issue"
                pagure_head = {"Authorization": pagureToken}
                r = requests.post(pagure_URL, data=pagure_payload, headers=pagure_head)
                print(r.text)




myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Syncing tool prototype")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))