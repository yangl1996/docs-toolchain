from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import threading
import urllib.parse
import hmac
import hashlib
try:
    import config
except "No such file or directory":
    import config_sample as config
    print("Please set up your config.py file. Exiting.")
    exit()

listenAddr = config.listenAddr
listenPort = config.pagurePort
pagureRepo = config.pagureRepo
pagureToken = config.pagureToken
pagureHeader = {"Authorization": "token " + pagureToken}
pagureSecretKey = config.pagureSecretKey
githubToken = config.githubToken
githubHeader = {"Authorization": "token " + githubToken}
githubUsername = config.githubUsername
githubRepo = config.githubRepo

# TODO: how to handle merge conflict

r = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues", headers=pagureHeader)
init_file = r.text
init_json = json.loads(init_file)
last_issue_list = init_json['issues']


def handle_fixed(post_body):
    data = json.loads(post_body)
    deleted_title = data['msg']['issue']['title']
    print("Fixed: ", deleted_title)
    PR_id = int(deleted_title[1:deleted_title.find(' ')])
    r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}".format(githubUsername, githubRepo, PR_id),
                     headers=githubHeader)
    return_data = json.loads(r.text)
    PR_sha = return_data['head']['sha']
    merge_payload = json.dumps({"commit_message": "Merge pull request" + str(PR_id), "sha": PR_sha})
    r = requests.put('https://api.github.com/repos/{}/{}/pulls/{}/merge'.format(githubUsername, githubRepo, PR_id),
                     headers=githubHeader, data=merge_payload)
    print(r.text)


def handle_added(post_body):
    data = json.loads(post_body)
    added_title = data['msg']['issue']['title']
    print("Added: ", added_title)
    # TODO: handle added issue (sync to GitHub issue?)


def handle_comment(post_body):
    data = json.loads(post_body)
    info = {'comment': data['msg']['issue']['comments'][-1]['comment'],
            'issue_title': data['msg']['issue']['title'],
            'username': data['msg']['issue']['comments'][-1]['user']['name'],
            'fullname': data['msg']['issue']['comments'][-1]['user']['fullname']}
    comment_body = """*Commented by {}({})*
    {}""".format(info['fullname'], info['username'], info['comment'])
    PR_id = int(info['issue_title'][1:info['issue_title'].find(' ')])
    comment_payload = json.dumps({"body": comment_body})
    r = requests.post("https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, PR_id),
                      headers=githubHeader, data=comment_payload)
    print(comment_body)


# main server class
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global last_issue_list
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        self.send_response(200)
        self.end_headers()

        """
        # Validate signature
        signature = self.headers['X-Pagure-Signature']
        mac = hmac.new(pagureSecretKey.encode(), msg=post_body.encode(), digestmod=hashlib.sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            print("Invalid signature, ignoring this call")
            return
        """

        post_body = urllib.parse.parse_qs(post_body)
        post_body = post_body['payload'][0]
        print(post_body)

        if self.headers['X-Pagure-Topic'] == "issue.edit":
            th = threading.Thread(target=handle_fixed)
            th.start()
        if self.headers['X-Pagure-Topic'] == "issue.new":
            th = threading.Thread(target=handle_added)
            th.start()
        if self.headers['X-Pagure-Topic'] == "issue.comment.added":
            th = threading.Thread(target=handle_comment, args=(post_body,))
            th.start()


myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Test Server")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))