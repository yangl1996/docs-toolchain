from datetime import date
from time import mktime
import json


class User:
    def __init__(self, username, fullname, default_email, emails=None):
        self.__username = username
        self.__fullname = fullname
        self.__default_email = default_email
        if not emails:
            self.__emails = [default_email]
        self.__emails = emails

    @classmethod
    def load(cls, json_dict):
        return cls(json_dict['name'], json_dict['fullname'], json_dict['default_email'],
                   emails=json_dict['emails'])

    def default_email(self, new_email=None):
        if not new_email:
            return self.__default_email
        else:
            self.__default_email = new_email

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

    def get_dict(self):
        result = {"fullname": self.__fullname, "username": self.__username, "default_email": self.__default_email,
                  "emails": self.__emails}
        return result


class Comment:

    def __init__(self, ui_id, creator, comment,
                 create_date=int(mktime(date.today().timetuple())), parent=None):
        self.__ui_id = ui_id
        self.__creator = creator
        self.__comment = comment
        self.__create_date = create_date
        self.__parent = parent

    @classmethod
    def load(cls, json_dict):
        ui_id = json_dict['id']
        creator = User.load(json_dict['user'])
        comment = json_dict['comment']
        create_date = json_dict['date_created']
        parent = cls.load(json_dict['parent'])
        return cls(ui_id, creator, comment, create_date=create_date, parent=parent)

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

    def get_dict(self):
        result = {'comment': self.__comment, 'date_created': self.__create_date, 'id': self.__ui_id}
        if self.__parent:
            result['parent'] = self.__parent.get_dict()
        else:
            result['parent'] = None
        result['user'] = self.__creator.get_dict()
        return result


class Issue:
    def __init__(self, ui_id, title, content, creator, tags=None, private=False, status="Open", depends=None,
                 create_date=int(mktime(date.today().timetuple())), comments=None, blocks=None, assignee=None):
        """
        :param ui_id:       [int] the id used in the UI
        :param title:       [str] the title of the issue
        :param content:     [str] the content fo the issue
        :param creator:     [class User] the creator of the issue
        :param tags:        [list of str] tags of the issue
        :param private:     [boolean] whether the issue is private
        :param status:      [str] the status of the issue
        :param depends:     UNKNOWN!
        :param create_date: [int] an UNIX style date
        :param comments:    [list of class Comment] comments of the issue
        :param blocks:      UNKNOWN!
        :param assignee:    [class User] the assignee of the issue
        :return:
        """

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
        self.__content = content

    @classmethod
    def load(cls, input_dict):
        assignee = User.load(input_dict['assignee'])
        blocks = []  # TODO: handle this
        comments = Comment.load(input_dict['comments'])
        content = input_dict['content']
        create_date = input_dict['date_created']
        depends = []  # TODO: handle this
        ui_id = input_dict['id']
        private = input_dict['private']
        status = input_dict['status']
        tags = input_dict['tags']
        title = input_dict['title']
        creator = User.load(input_dict['user'])

        return cls(ui_id, title, content, creator, tags=tags, private=private, status=status, depends=depends,
                   create_date=create_date, comments=comments, blocks=blocks, assignee=assignee)

    def content(self, new_content=None):
        if not new_content:
            return self.__content
        else:
            self.__content = new_content

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

    def tags(self, new_tag=None):
        if not new_tag:
            return self.__tags
        else:
            self.__tags.append(new_tag)

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

    def comments(self, new_comment=None):
        if not new_comment:
            return self.__comments
        else:
            self.__comments.append(new_comment)

    def blocks(self):
        return self.__blocks

    def assignee(self, new_assignee=None):
        if not new_assignee:
            return self.__assignee
        else:
            self.__assignee = new_assignee

    def get_dict(self):

        data = {}

        if not self.__assignee:
            data['assignee'] = None
        else:
            data['assignee'] = self.__assignee.get_dict()

        data['blocks'] = []  # TODO: implement this
        if not self.__comments:
            data['comments'] = []
        else:
            data['comments'] = [single_comment.get_dict() for single_comment in self.__comments]
        data['content'] = self.__content
        data['date_created'] = self.__create_date
        data['depends'] = []  # TODO: implement this
        data['id'] = self.__ui_id
        data['private'] = self.__private
        data['status'] = self.__status

        if not self.__tags:
            data['tags'] = []
        else:
            data['tags'] = self.__tags

        data['title'] = self.__title
        data['user'] = self.__creator.get_dict()
        return data

    def format_json(self):
        target = self.get_dict()
        return json.dumps(target)
