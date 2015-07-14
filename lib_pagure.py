import requests
import json


class Pagure:
    # TODO: add error handling
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
            request_url = "{}/api/0/fork/{}/{}/pull-requests".format(self.InstanceURL, self.ForkUsername, self.Repository)
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
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}".format(self.InstanceURL, self.ForkUsername, self.Repository, request_id)
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
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/merge".format(self.InstanceURL, self.ForkUsername, self.Repository, request_id)
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
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/close".format(self.InstanceURL, self.ForkUsername, self.Repository, request_id)
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
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/comment".format(self.InstanceURL, self.ForkUsername, self.Repository, request_id)
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
            request_url = "{}/api/0/fork/{}/{}/pull-request/{}/flag".format(self.InstanceURL, self.ForkUsername, self.Repository, request_id)
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
