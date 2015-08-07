from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
import requests
import os
import hmac
import hashlib
import threading
import markdown
from urllib.request import urlopen
import libpagure
import logging
import git_interface as git
import sqlite3
try:
    import config
except ImportError:
    import config_sample as config
    logging.critical("Configuration file not found.")
    exit()

# import configurations from config.py

githubHeader = {"Authorization": "token " + config.githubToken}

pagure = libpagure.Pagure(config.pagureToken, config.pagureRepo)

gitRepository = git.Repository(config.localRepoPath, "origin", "pagure")  # remote 1 github, remote 2 is pagure


def ci_build(pull_request_id, patch_url):
    r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}/files".format(config.githubUsername,
                                                                                config.githubRepo,
                                                                                pull_request_id),
                     headers=githubHeader)
    data = json.loads(r.text)
    patch_data = urlopen(patch_url)
    patch_file = '{}.patch'.format(pull_request_id)
    patch_path = '{}/{}/'.format(config.patchFolderPath, pull_request_id)

    if not os.path.exists(os.path.dirname(patch_path)):
        os.makedirs(os.path.dirname(patch_path))

    f = open(patch_path + patch_file, 'w')
    f.write(patch_data.read().decode('utf-8'))
    f.close()
    gitRepository.apply("{}/{}".format(patch_path, patch_file))
    filelist = []
    for changed_file in data:
        this_file = {'filename': changed_file['filename'],
                     'status': changed_file['status'],
                     'built': False,
                     'built_path': ''}
        try:
            if this_file['status'] != 'removed':
                filename = this_file['filename']
                if not os.path.exists(os.path.dirname(config.ciRepoPath + '/' + str(pull_request_id) + '/' + filename)):
                    os.makedirs(os.path.dirname(config.ciRepoPath + '/' + str(pull_request_id) + '/' + filename))
                markdown.markdownFromFile(input=config.localRepoPath + '/' + changed_file['filename'],
                                          output="{}/{}/{}.html".format(config.ciRepoPath,
                                                                        pull_request_id,
                                                                        filename),
                                          output_format="html5")
                this_file['built_path'] = "{}/{}.html".format(pull_request_id, filename)
                this_file['built'] = True
        finally:
            filelist.append(this_file)
    gitRepository.stash()
    filelist_name = "filelist-pr-{}.json".format(pull_request_id)
    with open(patch_path + '/' + filelist_name, 'w') as f:
        json.dump(filelist, f)


# handle new pull request on github
def handle_pull_request(post_body):
    data = json.loads(post_body)  # parse web hook payload

    # new PR opened
    if data['action'] == 'opened':
        logging.info("New pull request opened on GitHub.")
        info = {'title': data['pull_request']['title'],
                'creator': data['pull_request']['user']['login'],
                'id': data['pull_request']['number'],
                'link': data['pull_request']['html_url'],
                'content': data['pull_request']['body'],
                'patch_url': data['pull_request']['patch_url']}  # get github PR info
        pagure_title = "#{} {} by {}".format(str(info['id']),
                                             info['title'],
                                             info['creator'])  # generate pagure issue title
        if not info['content']:  # empty PR description
            info['content'] = "*No description provided.*"

        ci_build(info['id'], info['patch_url'])

        filelist = '<code>'

        patch_path = '{}/{}/'.format(config.patchFolderPath, info['id'])
        filelist_name = "filelist-pr-{}.json".format(info['id'])
        file_list_json = open(patch_path + '/' + filelist_name, 'r')
        changed_file_list = json.loads(file_list_json.read())
        file_list_json.close()
        preview_html = ""
        for changed_file in changed_file_list:
            filelist += "{}\n".format(changed_file['filename'])
            if changed_file['built']:
                preview_html += """<tr>
                                     <th></th>
                                     <td><a href="{}" target="_blank">{}</a></td>
                                   </tr>""".format("{}/{}".format(config.ciServer, changed_file['built_path']),
                                                   changed_file['filename'])

        if len(changed_file_list) == 0:
            built_time_tag = "No preview available."
        else:
            built_time_tag = "Built at " + datetime.datetime.utcnow().strftime("%m/%d/%Y %H:%M UTC")

        filelist += "</code>"
        pr_html_link = "https://github.com/{}/{}/pull/{}".format(config.githubUsername, config.githubRepo, info['id'])
        pagure_content = """<table>
                                <tr>
                                    <th>Creator</th>
                                    <td>{}</td>
                                </tr>
                                <tr>
                                    <th>PR Link</th>
                                    <td><a href="{}" target="_blank">{}</a></td>
                                </tr>
                                <tr>
                                    <th>Modified File</th>
                                    <td>{}</td>
                                </tr>
                                <tr>
                                    <th>Preview</th>
                                    <td>{}</td>
                                </tr>
                                {}
                                </table><hr>\n\n{}""".format(info['creator'], pr_html_link, pr_html_link,
                                                             filelist, built_time_tag, preview_html, info['content'])

        conn = sqlite3.connect(config.issueDatabasePath)
        c = conn.cursor()
        c.execute("INSERT INTO Requests VALUES (?, ?, ?, ?)", (info['title'],
                                                               pagure_title,
                                                               info['id'],
                                                               0,))  # first use 0 as pagure issue id
        conn.commit()
        conn.close()
        # call pagure API to post the corresponding issue
        pagure.create_issue(pagure_title, pagure_content)

    elif data['action'] == 'synchronize':
        logging.info("New commits pushed to existing pull request.")
        info = {'id': data['pull_request']['number'], 'patch_url': data['pull_request']['patch_url']}
        ci_build(info['id'], info['patch_url'])
        pagure_content = "*Commented by the toolchain*\n\n```\n"
        pagure_content += "New commits pushed to tracked branch. Preview has been updated.\n```\n\n"

        patch_path = '{}/{}/'.format(config.patchFolderPath, info['id'])
        filelist_name = "filelist-pr-{}.json".format(info['id'])
        file_list_json = open(patch_path + '/' + filelist_name, 'r')
        changed_file_list = json.loads(file_list_json.read())
        file_list_json.close()
        for changed_file in changed_file_list:
            if changed_file['built']:
                pagure_content += "* [{}]({}/{})\n".format(changed_file['filename'],
                                                           config.ciServer,
                                                           changed_file['built_path'])

        conn = sqlite3.connect(config.issueDatabasePath)
        c = conn.cursor()
        c.execute('SELECT * FROM Requests WHERE GitHubID=?', (info['id'],))
        entry = c.fetchone()
        conn.close()
        try:
            pagure_id = int(entry[3])
            pagure.comment_issue(pagure_id, pagure_content)
        except TypeError:
            logging.warning("Can't find corresponding pagure issue.")

    # PR closed
    elif data['action'] == 'closed':
        # not merged
        if not data['pull_request']['merged']:
            conn = sqlite3.connect(config.issueDatabasePath)
            c = conn.cursor()
            c.execute('SELECT * FROM Requests WHERE GitHubID=?', (data['pull_request']['number'],))
            entry = c.fetchone()
            conn.close()
            try:
                pagure_id = int(entry[3])  # get pagure issue id from the first comment
                pagure.change_issue_status(pagure_id, "Invalid")
                logging.info("Pull request closed without being merged on GitHub.")
            except TypeError:
                logging.warning("A PR was closed but has no corresponding Pagure issue.")

        # merged
        else:
            logging.info("Pull request merged on GitHub.")

            # let Python use shell commands to pull the changes from github, then push changes to pagure
            gitRepository.pull(1)
            gitRepository.push(2)


def handle_pull_request_comment(post_body):

    data = json.loads(post_body)  # parse web hook payload

    # currently github are not providing comment deletion web hook, so only handle creation
    if data['action'] == 'created':
        info = {'issue_name': data['issue']['title'],
                'issue_id': data['issue']['number'],
                'comment': data['comment']['body'],
                'username': data['comment']['user']['login']}  # get comment info
        # we auto create an comment pointing to pagure when new PR is opened, should ignore this one
        if info['comment'].startswith("[Issue #"):
            return
        # avoid infinity loop
        if info['comment'].startswith("*Commented by"):
            return

        # prepare pagure comment body
        comment_body = """*Commented by {}*\n\n{}""".format(info['username'], info['comment'])

        conn = sqlite3.connect(config.issueDatabasePath)
        c = conn.cursor()
        c.execute('SELECT * FROM Requests WHERE GitHubID=?', (info['issue_id'],))
        entry = c.fetchone()
        conn.close()
        try:
            pagure_id = int(entry[3])  # get pagure issue id from the first comment
            # call pagure API to sync the comment
            pagure.comment_issue(pagure_id, comment_body)
            logging.info("New comment created on GitHub.")
        except TypeError:
            logging.warning("A comment was created on github but has no relevant Pagure issue.")


# main server class
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()

        # Validate signature
        sha_name, signature = self.headers['X-Hub-Signature'].split('=')

        if sha_name != 'sha1':
            return
        mac = hmac.new(config.githubSecretKey.encode(), msg=post_body.encode(), digestmod=hashlib.sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            logging.warning("Ignoring a web hook call due to incorrect signature.")
            return

        # Handle post body
        if self.headers['X-Github-Event'] == 'pull_request':
            th = threading.Thread(target=handle_pull_request, args=(post_body,))
            th.start()

        elif self.headers['X-Github-Event'] == 'issue_comment':
            th = threading.Thread(target=handle_pull_request_comment, args=(post_body,))
            th.start()


myServer = HTTPServer((config.listenAddr, config.githubPort), MyServer)
print("Syncing tool")
logging.basicConfig(filename='github.log', level=logging.INFO)
logging.info('Server starts ay %s:%s.', config.listenAddr, config.githubPort)

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
logging.info('Server stops.')
