import requests
import json


class Pagure:
    # TODO: add error handling
    # TODO: write some unit tests
    def __init__(self, pagure_token, pagure_repository, fork_username=None, instance_url="https://pagure.io"):
        """
        Create an instance.
        :param pagure_token: pagure API token
        :param pagure_repository: pagure project name
        :param fork_username: if this is a fork, it's the username of the fork creator
        :param instance_url: the URL of pagure instance name
        :return:
        """
        self.Token = pagure_token
        self.Repository = pagure_repository
        self.ForkUsername = fork_username
        self.InstanceURL = instance_url
        self.Header = {"Authorization": "token " + self.Token}

    def api_version(self):
        """
        Get Pagure API version.
        :return:
        """
        request_url = "{}/api/0/version".format(self.InstanceURL)
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value['version']

    def list_users(self, pattern=None):
        """
        List all users registered on this Pagure instance.
        :param pattern: filters the starting letters of the return value
        :return:
        """
        request_url = "{}/api/0/users".format(self.InstanceURL)
        if pattern is None:
            r = requests.get(request_url, headers=self.Header)
        else:
            r = requests.get(request_url, params={'pattern': pattern})
        return_value = json.loads(r.text)
        return return_value['users']

    def list_tags(self, pattern=None):
        """
        List all tags made on this project.
        :param pattern: filters the starting letters of the return value
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/tags".format(self.InstanceURL, self.Repository)
        else:
            request_url = "{}/api/0/fork/{}/{}/tags".format(self.InstanceURL, self.ForkUsername, self.Repository)
        if pattern is None:
            r = requests.get(request_url, headers=self.Header)
        else:
            r = requests.get(request_url, headers=self.Header, params={'pattern': pattern})
        return_value = json.loads(r.text)
        return return_value['tags']

    def list_groups(self, pattern=None):
        """
        List all groups on this Pagure instance.
        :param pattern: filters the starting letters of the return value
        :return:
        """
        request_url = "{}/api/0/groups".format(self.InstanceURL)
        if pattern is None:
            r = requests.get(request_url, headers=self.Header)
        else:
            r = requests.get(request_url, headers=self.Header, params={'pattern': pattern})
        return_value = json.loads(r.text)
        return return_value['groups']

    def error_codes(self):
        """
        Get a dictionary of all error codes.
        :return:
        """
        request_url = "{}/api/0/error_codes"
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value

    def list_requests(self, status=None, assignee=None, author=None):
        """
        Get all pull requests of a project.
        :param status: filters the status of the requests
        :param assignee: filters the assignee of the requests
        :param author: filters the author of the requests
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/pull-requests".format(self.InstanceURL, self.Repository)
        else:
            request_url = "{}/api/0/fork/{}/{}/pull-requests".format(self.InstanceURL, self.ForkUsername,
                                                                     self.Repository)
        payload = {}
        if status is not None:
            payload['status'] = status
        if assignee is not None:
            payload['assignee'] = assignee
        if author is not None:
            payload['author'] = author
        r = requests.get(request_url, headers=self.Header, params=payload)
        return_value = json.loads(r.text)
        return return_value['requests']

    def request_info(self, request_id):
        """
        Get information of a single pull request.
        :param request_id: the id of the request
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/pull-request/{}".format(self.InstanceURL, self.Repository, request_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}".format(self.InstanceURL, self.ForkUsername,
                                                                       self.Repository, request_id)
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value

    def merge_request(self, request_id):
        """
        Merge a pull request.
        :param request_id: the id of the request
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/pull-request/{}/merge".format(self.InstanceURL, self.Repository, request_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/merge".format(self.InstanceURL, self.ForkUsername,
                                                                             self.Repository, request_id)
        r = requests.post(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'] == "Changes merged!":
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def close_request(self, request_id):
        """
        Close a pull request.
        :param request_id: the id of the request
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/pull-request/{}/close".format(self.InstanceURL, self.Repository, request_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/close".format(self.InstanceURL, self.ForkUsername,
                                                                             self.Repository, request_id)
        r = requests.post(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'] == "Pull-request closed!":
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def comment_request(self, request_id, body, commit=None, filename=None, row=None):
        """
        Create a comment on the request.
        :param request_id: the id of the request
        :param body: the comment body
        :param commit: which commit to comment on
        :param filename: which file to comment on
        :param row: which line of code to comment on
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/pull-request/{}/comment".format(self.InstanceURL, self.Repository, request_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/comment".format(self.InstanceURL, self.ForkUsername,
                                                                               self.Repository, request_id)
        payload = {'comment': body}
        if commit is not None:
            payload['commit'] = commit
        if filename is not None:
            payload['filename'] = filename
        if row is not None:
            payload['row'] = row
        r = requests.post(request_url, data=payload, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'] == "Comment added":
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def flag_request(self, request_id, username, percent, comment, url, uid=None, commit=None):
        """
        Add or edit a flag of the request.
        :param request_id: the id of the request
        :param username: the name of the application to be displayed
        :param percent: the percentage of completion to be displayed
        :param comment: a short message summarizing the flag
        :param url: a relevant URL
        :param uid: a unique id used to identify the flag. If not provided, pagure will generate one
        :param commit: which commit to flag on
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/pull-request/{}/flag".format(self.InstanceURL, self.Repository, request_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/flag".format(self.InstanceURL, self.ForkUsername,
                                                                            self.Repository, request_id)
        payload = {'username': username, 'percent': percent, 'comment': comment, 'url': url}
        if commit is not None:
            payload['commit'] = commit
        if uid is not None:
            payload['uid'] = uid
        r = requests.post(request_url, data=payload, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'] == "Flag added" or return_value['message'] == "Flag updated":
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def create_issue(self, title, content, private=None):
        """
        Create a new issue.
        :param title: the title of the issue
        :param content: the description of the issue
        :param private: whether create this issue as private
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/new_issue".format(self.InstanceURL, self.Repository)
        else:
            request_url = "{}/api/0/fork/{}/{}/new_issue".format(self.InstanceURL, self.ForkUsername, self.Repository)
        payload = {'title': title, 'issue_content': content}
        if private is not None:
            payload['private'] = private
        r = requests.post(request_url, data=payload, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'] == "Issue created":
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def list_issues(self, status=None, tags=None, assignee=None, author=None):
        """
        List all issues of a project.
        :param status: filters the status of the issues
        :param tags: filers the tags of the issues
        :param assignee: filters the assignee of the issues
        :param author: filters the author of the issues
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/issues".format(self.InstanceURL, self.Repository)
        else:
            request_url = "{}/api/0/fork/{}/{}/issues".format(self.InstanceURL, self.ForkUsername, self.Repository)
        payload = {}
        if status is not None:
            payload['status'] = status
        if tags is not None:
            payload['tags'] = tags
        if assignee is not None:
            payload['assignee'] = assignee
        if author is not None:
            payload['author'] = author
        r = requests.get(request_url, params=payload, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value['issues']

    def issue_info(self, issue_id):
        """
        Get info about a single issue.
        :param issue_id: the id of the issue
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/issue/{}".format(self.InstanceURL, self.Repository, issue_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/issue/{}".format(self.InstanceURL, self.ForkUsername, self.Repository, issue_id)
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value

    def get_list_comment(self, issue_id, comment_id):
        """
        Get a specific comment of an issue.
        :param issue_id: the id of the issue
        :param comment_id: the id of the comment
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/issue/{}/comment/{}".format(self.InstanceURL, self.Repository, issue_id,
                                                                   comment_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/issue/{}/comment/{}".format(self.InstanceURL, self.ForkUsername,
                                                                           self.Repository, issue_id, comment_id)
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value

    def change_issue_status(self, issue_id, new_status):
        """
        Change the status of an issue.
        :param issue_id: the id of the issue
        :param new_status: the new status fo the issue
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/issue/{}/status".format(self.InstanceURL, self.Repository, issue_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/issue/{}/status".format(self.InstanceURL, self.ForkUsername,
                                                                       self.Repository, issue_id)
        payload = {'status': new_status}
        r = requests.post(request_url, data=payload, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'].startswith("Successfully"):
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def comment_issue(self, issue_id, body):
        """
        Comment to an issue.
        :param issue_id: the id of the comment
        :param body: the comment body
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/issue/{}/comment".format(self.InstanceURL, self.Repository, issue_id)
        else:
            request_url = "{}/api/0/fork/{}/{}/issue/{}/comment".format(self.InstanceURL, self.ForkUsername,
                                                                        self.Repository, issue_id)
        payload = {'comment': body}
        r = requests.post(request_url, data=payload, headers=self.Header)
        return_value = json.loads(r.text)
        if return_value['message'] == 'Comment added':
            result = (True, return_value['message'])
        else:
            result = (False, return_value['message'])
        return result

    def project_tags(self):
        """
        List all git tags made to the project.
        :return:
        """
        if self.ForkUsername is None:
            request_url = "{}/api/0/{}/git/tags".format(self.InstanceURL, self.Repository)
        else:
            request_url = "{}/api/0/fork/{}/{}/git/tags".format(self.InstanceURL, self.ForkUsername, self.Repository)
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value['tags']

    def list_projects(self, tags=None, username=None, fork=None):
        """
        Lisk all projects on this Pagure instance.
        :param tags: filters the tags of the project
        :param username: filters the username of the project administrators
        :param fork: filters whether it is a fork (True) or not (False)
        :return:
        """
        request_url = "{}/api/0/projects".format(self.InstanceURL)
        payload = {}
        if tags is not None:
            payload['tags'] = tags
        if username is not None:
            payload['username'] = username
        if fork is not None:
            payload['fork'] = fork
        r = requests.get(request_url, params=payload, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value['projects']

    def user_info(self, username):
        """
        Get info of a specific user.
        :param username: the username of the user to get info about
        :return:
        """
        request_url = "{}/api/0/user/{}".format(self.InstanceURL, username)
        r = requests.get(request_url, headers=self.Header)
        return_value = json.loads(r.text)
        return return_value
