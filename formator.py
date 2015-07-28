from datetime import date
from time import mktime
from time import strftime

# This file includes JSON file templates for Pagure

template_issue = """{
  "assignee": null,
  "blocks": [],
  "comments": [],
  "content": "This issue needs attention",
  "date_created": "1431414800",
  "depends": [],
  "id": 1,
  "private": false,
  "status": "Open",
  "tags": [],
  "title": "test issue",
  "user": {
    "fullname": "PY C",
    "name": "pingou"
  }
}"""

template_comment = """{
  "avatar_url": "https://seccdn.libravatar.org/avatar/...",
  "comment": "9",
  "comment_date": "2015-07-01 15:08",
  "date_created": "1435756127",
  "id": 464,
  "parent": null,
  "user": {
    "fullname": "P.-Y.C.",
    "name": "pingou"
  }
}"""


class User:
    def __init__(self, username, fullname, avatar_url=None):
        self.__username = username
        self.__fullname = fullname
        self.__avatar_url = avatar_url

    def username(self, username=None):
        if not username:
            return self.__username
        else:
            self.__username = username

    def fullname(self, fullname=None):
        if not fullname:
            return self.__fullname
        else:
            self.__fullname = fullname

    def avatar(self, new_avatar=None):
        if not new_avatar:
            return self.__avatar_url
        else:
            self.__avatar_url = new_avatar


class Comment:
    def __init__(self, ui_id, creator, comment,
                 create_time=strftime("%Y-%m-%d %H:%M"),
                 create_date=int(mktime(date.today().timetuple())), parent=None):
        self.__ui_id = ui_id
        self.__creator = creator
        self.__comment = comment
        self.__create_time = create_time
        self.__create_date = create_date
        self.__parent = parent

    def create_date(self, new_date=None):
        if not new_date:
            return self.__create_date
        else:
            if new_date is date:
                self.__create_date = int(mktime(new_date.timetuple()))
            elif new_date is int:
                self.__create_date = new_date

    def parent(self, new_parent=None):
        if not new_parent:
            return self.__parent
        else:
            self.__parent = new_parent

    def create_time(self, new_time=None):
        if not new_time:
            return self.__create_time
        else:
            if new_time is not str:
                raise Exception("String expected here, format: %Y-%m-%d %H:%M")
            else:
                self.__create_time = new_time

    def comment(self, new_comment=None):
        if not new_comment:
            return self.__comment
        else:
            self.__comment = new_comment

    def ui_id(self, new_id=None):
        if not new_id:
            return self.__ui_id
        else:
            self.__ui_id = new_id

    def creator(self, new_creator=None):
        if not new_creator:
            return self.__creator
        else:
            self.__creator = new_creator


class Issue:
    def __init__(self, ui_id, title,
                 creator,
                 tags=None,
                 private=False,
                 status="Open",
                 depends=None,
                 create_date=int(mktime(date.today().timetuple())),
                 comments=None,
                 blocks=None,
                 assignee=None):
        self.__ui_id = ui_id
        self.__creator = creator
        self.__title = title
        self.__tags = tags
        self.__private = private
        self.__status = status
        self.__depends = depends
        self.__create_date = create_date
        self.__comments = comments
        self.__blocks = blocks
        self.__assignee = assignee

    def ui_id(self, new_id=None):
        if not id:
            return self.__ui_id
        else:
            self.__ui_id = int(new_id)

    def title(self, new_title=None):
        if not new_title:
            return self.__title
        else:
            self.__title = new_title

    def creator(self, new_creator=None):
        if not new_creator:
            return self.__creator
        else:
            self.__title = new_creator

    def private(self, new_private=None):
        if not new_private:
            return self.__private
        else:
            self.__private = new_private

    def tags(self):
        return self.__tags

    def status(self, new_status=None):
        if not new_status:
            return self.__status
        else:
            self.__status = new_status

    def depends(self):
        return self.__depends

    def create_date(self, new_date=None):
        if not new_date:
            return self.__create_date
        else:
            if new_date is date:
                self.__create_date = int(mktime(new_date.timetuple()))
            elif new_date is int:
                self.__create_date = new_date

    def comments(self):
        return self.__comments

    def blocks(self):
        return self.__blocks

    def assignee(self, new_assignee=None):
        if not new_assignee:
            return self.__assignee
        else:
            self.__assignee = new_assignee