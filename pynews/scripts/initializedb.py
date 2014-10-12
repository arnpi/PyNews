# -*- coding: utf-8 -*-

""" Database initialization script """

import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging

from pynews.models import Rss
from pynews.models import Base
from pynews.models import DBSession
# from pynews.models import Group
from pynews.models import User
from pynews.models import Note
from pynews.models import Category
from pynews.models import Bookmark
from pynews.models import Mail
from pynews.models import Setting

import xml.etree.ElementTree as ET

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

     # Populate table setting
    with transaction.manager:
        setting = Setting(twitter_api_key="", twitter_api_secret="")
        DBSession.add(setting)

     # Populate table users
    with transaction.manager:
        for name in [u'admin']:
            user = User(name, password=name, access_token="toto", access_token_secret="too")
            DBSession.add(user)

        user_list = []
        for i in range(1, 4):
            user_list.append("user" + str(i))
        for name in user_list:
            user = User(name, password=name, access_token="toto", access_token_secret="too")
            DBSession.add(user)
    # Populate category
    with transaction.manager:
        user = DBSession.query(User).get(1)
        for name in [u'general', u'divers', u'science', u'tech', u'us']:
            category = Category(user, name.capitalize(), u'{0} category description'.format(name))
            DBSession.add(category)

    # Populate table rsses
    with transaction.manager:
        user = DBSession.query(User).get(1)
        category = DBSession.query(Category).get(3)
        rss = Rss(user=user, title=u'Rss #1', text=u'http://www.techno-science.net/include/news.xml', category=[category,])
        DBSession.add(rss)
        category = DBSession.query(Category).get(1)
        rss = Rss(user=user, title=u'Rss #2', text=u'http://rss.lemonde.fr/c/205/f/3050/index.rss', category=[category,])
        DBSession.add(rss)
        category = DBSession.query(Category).get(1)
        rss = Rss(user=user, title=u'Rss #3', text=u'http://rss.liberation.fr/rss/9/', category = [category,])
        DBSession.add(rss)
        category = DBSession.query(Category).get(4)
        rss = Rss(user=user, title=u'Rss #4', text=u'http://feeds2.feedburner.com/LeJournalduGeek', category=[category,])
        DBSession.add(rss)

    # Populate table notes
    with transaction.manager:
        user = DBSession.query(User).get(1)
        for i in range(1, 10):
            note = Note(user=user, title=u'Note #%d' % i, text=u'Text of the note #%d' % i)
            DBSession.add(note)

    # Populate table bookmark
    with transaction.manager:
        user = DBSession.query(User).get(1)
        for i in range(1, 3):
            bookmark = Bookmark(user=user, title=u'Bookmark #%d' % i, text=u'http://www.site.com/bookmark/#%d' % i)
            DBSession.add(bookmark)


    # Populate table mail
    with transaction.manager:
        user = DBSession.query(User).get(1)
        mail = Mail(user=user, hostname=u'imap.gmx.com', username=u'user@gmx.com', password=u'password', ssl=True, port=993)
        DBSession.add(mail)
        mail = Mail(user=user, hostname=u'imap.gmail.com', username=u'user2@gmail.com', password=u'password2', ssl=True, port=993)
        DBSession.add(mail)
