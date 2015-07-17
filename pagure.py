from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import threading
import urllib.parse
import logging
import libpagure
# the following two imports are currently not used
import hmac
import hashlib
try:
    import config
except "No such file or directory":
    import config_sample as config
    logging.critical("Configuration file not found.")
    exit()

# import configurations from config.py
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


def handle_edition(post_body):
    """
    Function to handle edited issue.
    """
    data = json.loads(post_body)  # parse web hook payload
    deleted_title = data['msg']['issue']['title']  # get fixed issue's title
    if data['msg']['issue']['status'] == 'Fixed':
        logging.info("An issue is marked as fixed on Pagure.")
        PR_id = int(deleted_title[1:deleted_title.find(' ')])  # get github PR id from the issue title
        r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}".format(githubUsername, githubRepo, PR_id),
                     headers=githubHeader)  # get PR info from github
        return_data = json.loads(r.text)  # parse PR info
        PR_sha = return_data['head']['sha']  # get PR sha from PR info
        # call github API to merge the PR
        merge_payload = json.dumps({"commit_message": "Merge pull request" + str(PR_id), "sha": PR_sha})
        r = requests.put('https://api.github.com/repos/{}/{}/pulls/{}/merge'.format(githubUsername, githubRepo, PR_id),
                     headers=githubHeader, data=merge_payload)
        # TODO: add a commment on github to remind to delete the branch


def handle_added(post_body):
    data = json.loads(post_body)  # parse web hook payload
    added_title = data['msg']['issue']['title']  # get added issue's title
    added_id = data['msg']['issue']['id']  # get added issue's id on pagure
    # TODO: handle issues added on pagure (sync to GitHub issue?)
    if added_title.startswith("#"):
        logging.info("An mirror issue is added on GitHub.")
        PR_id = int(added_title[1:added_title.find(' ')])  # get github PR id from the issue title
        # call github API to post a comment containing pagure issue link to github PR
        PR_Comment_Link = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, PR_id)
        PR_Comment_Body = "[Issue #{}](https://pagure.io/{}/issue/{}) created on Pagure.".format(added_id, pagureRepo,added_id)
        github_payload = {"body": PR_Comment_Body}
        r = requests.post(PR_Comment_Link, data=json.dumps(github_payload), headers=githubHeader)


def handle_comment(post_body):
    # TODO: need handle comment deletion
    logging.info("A comment is created on Paugre.")
    data = json.loads(post_body)  # parse web hook payload
    info = {'comment': data['msg']['issue']['comments'][-1]['comment'],
            'issue_title': data['msg']['issue']['title'],
            'username': data['msg']['issue']['comments'][-1]['user']['name'],
            'fullname': data['msg']['issue']['comments'][-1]['user']['fullname']}  # get info about the comment
    # avoid infinity loop
    if info['comment'].startswith("*Commented by"):
        return
    comment_body = """*Commented by {} ({})*

    {}""".format(info['fullname'], info['username'], info['comment'])  # generate comment body to be posted to github
    PR_id = int(info['issue_title'][1:info['issue_title'].find(' ')])  # get github PR id from pagure issue title
    # call github API to post the comment
    comment_payload = json.dumps({"body": comment_body})
    r = requests.post("https://api.github.com/repos/{}/{}/issues/{}/comments".format(githubUsername, githubRepo, PR_id),
                      headers=githubHeader, data=comment_payload)


# main server class
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        # get web hook post header and post body
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        self.send_response(200)
        self.end_headers()  # response to pagure

        # TODO: validate signature
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

        if self.headers['X-Pagure-Topic'] == "issue.edit":  # issue edit
            th = threading.Thread(target=handle_edition, args=(post_body,))
            th.start()
        if self.headers['X-Pagure-Topic'] == "issue.new":  # issue added
            th = threading.Thread(target=handle_added, args=(post_body,))
            th.start()
        if self.headers['X-Pagure-Topic'] == "issue.comment.added":  # issue comment
            th = threading.Thread(target=handle_comment, args=(post_body,))
            th.start()


myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Test Server")
logging.info('Server starts ay %s:%s.', listenAddr, listenPort)

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
logging.info('Server stops.')