import datetime
import hashlib
import random
import string
import transaction

from sqlalchemy import engine_from_config

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relation
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.schema import Column
from sqlalchemy.schema import Table
from sqlalchemy.schema import ForeignKey

from sqlalchemy.types import DateTime
from sqlalchemy.types import Enum
from sqlalchemy.types import Integer
from sqlalchemy.types import Text
from sqlalchemy.types import Unicode
from sqlalchemy.types import Boolean

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

RANDOM_STRING = string.letters + string.digits
def random_string(self, length=10):
    return u''.join(
        random.choice(RANDOM_STRING)
        for i in range(0, length)
    )

# rss/category
rss_category_associations = Table('rss_category_associations', Base.metadata,
    Column('rsses_id', Integer, ForeignKey('rsses.id')),
    Column('category_id', Integer, ForeignKey('category.id')),
)

class Setting(Base):
    __tablename__ = 'setting'

    id = Column(Integer, primary_key=True)
    twitter_api_key = Column(Unicode(255))
    twitter_api_secret = Column(Unicode(255))
 
    def __init__(self, twitter_api_key, twitter_api_secret):
        self.twitter_api_key = twitter_api_key
        self.twitter_api_secret = twitter_api_secret

    def to_json(self):
        return dict(
            twitter_api_key=self.twitter_api_key,
            twitter_api_secret=self.twitter_api_secret,
        )


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relation('User', backref='category')
 
    def __init__(self, user, name, description):
        self.user = user
        self.name = name
        self.description = description

    def to_json(self):
        return dict(
            name=self.name,
            description=self.description,
        )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(Unicode(255), unique=True)
    password = Column(Unicode(32))
    access_token = Column(Unicode(255), unique=False)
    access_token_secret = Column(Unicode(255), unique=False)
    # firstname = Column(Unicode(255))
    # lastname = Column(Unicode(255))
    # groups = relation('Group', secondary=user_groups_associations)
    
    def __init__(self, username, password=None, groups=[], access_token=None, access_token_secret=None):
        self.username = username
        # self.access_token = access_token
        # self.access_token_secret = access_token_secret
        # self.groups = groups
        if password is not None:
            self.set_password(password)

    def __get_salted_hash(self, password, salt=None):
        if salt is None:
            salt = random_string(10)
        sha256 = hashlib.sha256(password)
        sha256.update(salt)
        return '%s:%s' % (salt, sha256.hexdigest())

    def to_json(self):
        return dict(
            username=self.username,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            # firstname=self.firstname,
            # lastname=self.lastname,
            groups=[group.to_json() for group in self.groups]
        )

    def set_password(self, password):
        self.password = self.__get_salted_hash(password)

    def validate_password(self, password):
        if self.password is None:
            return False
        salt, salted = self.password.split(':')
        return self.password == self.__get_salted_hash(password, salt=salt)

# rsses
class Rss(Base):
    __tablename__ = 'rsses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relation('User', backref='rsses')
    creation_date = Column(DateTime)
    title = Column(Unicode(1024))
    text = Column(Unicode(1024))
    # status = Column(Enum(u'draft', u'published', u'refused'))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relation('Category', secondary=rss_category_associations)
    count = Column(Integer)

    def __init__(self, user, title, text, category, count=20):
        self.user = user
        self.creation_date = datetime.datetime.utcnow()
        self.title = title
        self.text = text
        # self.status = status
        self.category = category
        self.count = count

    def to_json(self):
        return dict(
            user=self.user.to_json(),
            creation_date=self.creation_date.isoformat(),
            title=self.title,
            text=self.text,
            # status=self.status,
            category=self.category,
            count=self.count,
        )


# note
class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relation('User', backref='notes')
    creation_date = Column(DateTime)
    title = Column(Unicode(255), unique=True)
    text = Column(Text)

    def __init__(self, user, title, text):
        self.user = user
        self.creation_date = datetime.datetime.utcnow()
        self.title = title
        self.text = text

    def to_json(self):
        return dict(
            user=self.user.to_json(),
            creation_date=self.creation_date.isoformat(),
            title=self.title,
            text=self.text,
        )

# note
class Twitter(Base):
    __tablename__ = 'twitter'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    user = relation('User', backref='twitter')
    creation_date = Column(DateTime)
    access_token = Column(Unicode(255), unique=False)
    access_token_secret = Column(Unicode(255), unique=False)

    def __init__(self, user, title, text):
        self.user = user
        self.creation_date = datetime.datetime.utcnow()
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    def to_json(self):
        return dict(
            user=self.user.to_json(),
            creation_date=self.creation_date.isoformat(),
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
        )

# note
class Bookmark(Base):
    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relation('User', backref='bookmarks')
    creation_date = Column(DateTime)
    title = Column(Unicode(255), unique=True)
    text = Column(Text)

    def __init__(self, user, title, text):
        self.user = user
        self.creation_date = datetime.datetime.utcnow()
        self.title = title
        self.text = text

    def to_json(self):
        return dict(
            user=self.user.to_json(),
            creation_date=self.creation_date.isoformat(),
            title=self.title,
            text=self.text,
        )


#mail
class Mail(Base):
    __tablename__ = 'mails'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relation('User', backref='mails')
    creation_date = Column(DateTime)
    hostname = Column(Unicode(255), unique=False)
    username = Column(Unicode(255), unique=False)
    password = Column(Unicode(255), unique=False)
    ssl = Column(Boolean, unique=False)
    port = Column(Integer, unique=False)

    def __init__(self, user, hostname, username, password, ssl, port):
        self.user = user
        self.creation_date = datetime.datetime.utcnow()
        self.hostname = hostname
        self.username = username
        self.password = password
        self.ssl = ssl
        self.port = port

    def to_json(self):
        return dict(
            user=self.user.to_json(),
            creation_date=self.creation_date.isoformat(),
            hostname=self.hostname,
            username=self.username,
            password=self.password,
            ssl=self.ssl,
            port=self.port,
        )


def initialize_model(settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
