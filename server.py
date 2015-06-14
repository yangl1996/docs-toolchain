from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests

listenAddr = "128.199.82.190"
listenPort = 7654
secretKey = ""  # TODO:implement the secure feature of GitHub web hook (verify SHA1 signature)
pagureToken = "token L984SSW08QBFVEHF5IXVVWT9HNQJTX8HNSUM2XL6ECV7KUFKD7HHCYROIG0ZGGEJ"
# TODO: this is a test propose token
pagureRepo = "docs-test"


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        # TODO: send a response to github after receiving the request
        global pagureToken
        global pagureRepo

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
                if info['content'] == '':
                    info['content'] = "*No description provided.*"
                pagure_payload = {'title': pagure_title, 'issue_content': info['content'],
                                  'status': "Open"}
                pagure_URL = "https://pagure.io/api/0/" + pagureRepo + "/new_issue"
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