# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError
import feedparser
import base64
import xml.etree.ElementTree as ET
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import Tag

import transaction
from twitter import *

import twittertoken


import sqlalchemy as sa
from .models import (
    DBSession,
    # Group,
    Category,
    User,
    Rss,
    Note,
    Bookmark,
    Mail,
    Setting,
)
from pprint import pprint
import imap_cli
from imap_cli import config

from imap_cli import fetch


# Helper

def import_xml():
    pass
    # user = DBSession.query(User).get(1)
    # category = DBSession.query(Category).get(5)
    # tree = ET.parse('pynews/__us_rss.xml')
    # root = tree.getroot()
    # for child in root[1]:
    #     print(child.attrib['title'])
    #     print(child.attrib['xmlUrl'])
    #     print('\n')
    #     flux = Flux(user=user, title=child.attrib['title'], text=child.attrib['xmlUrl'], category=[category,])
    #     DBSession.add(flux)
    # print('END XML IMPORT')    

def remove_tags(text):
    return ''.join(xml.etree.ElementTree.fromstring(text).itertext())


def get_user_by_username(username):
    user_id = DBSession.query(User.id).filter_by(username=username).first()
    user = DBSession.query(User).get(user_id)
    return user


def get_category_by_name(category):
    try:
        category_id = DBSession.query(Category.id).filter_by(name=category).first()
        category = DBSession.query(Category).get(category_id)
        return category
    except Exception, e:
        return False


def get_category_by_id(category):
    try:
        category_id = DBSession.query(Category.id).filter_by(id=category).first()
        category = DBSession.query(Category).get(category_id)
        return category
    except Exception, e:
        return False


def check_user_logged(request):
    # session = request.session
    try:
        user = request.session['username']
        return user
    except Exception, e:
        return False


def check_twitter_logged(request):
    user = check_user_logged(request)
    try:
        access_token = DBSession.query(User.access_token).filter_by(username=user).first()
        access_token_secret = DBSession.query(User.access_token_secret).filter_by(username=user).first()
        if access_token[0] is None or access_token_secret[0] is None:
            return False
        # session = request.session['end_auth']
        session = {'access_token': access_token[0], 'access_token_secret': access_token_secret[0]}
        return session
    except Exception, e:
        return False




def check_user_admin(request):
    session = request.session
    if session['username']:
        user_id = DBSession.query(User.id).filter_by(username=session['username']).first()
        session = request.session
        if user_id[0] == 1:
            session['status'] = "admin"
            return True
        else:
            session['status'] = "user"
            return False
    else:
        return False


def import_from_opml(opml_file):
    pass

@view_config(route_name='register_api_twitter', renderer='json')
def register_api_twitter_view(request):
    user = check_user_logged(request)
    if check_user_admin(request):
        twitter_api_key = request.matchdict.get('twitter_api_key')
        twitter_api_secret = request.matchdict.get('twitter_api_secret')
        DBSession.query(Setting).filter_by(id=1).update({"twitter_api_key": twitter_api_key, "twitter_api_secret": twitter_api_secret})
        return dict(
                status=1,
            )
    else:
        return dict(
                status=0,
            )

# ADMIN
@view_config(route_name='users_list', renderer='json')
def users_list_view(request):
    if check_user_admin(request):
        try:
            users = DBSession.query(User.username).all()
            return dict(
                users=users,
                message=str(len(users)) + " users",
            )
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain', status_int=500)
    else:
        Response(conn_err_msg, content_type='text/plain', status_int=500)


@view_config(route_name='users_add', renderer='json')
def users_add_view(request):
    if check_user_admin(request):
        username = request.matchdict.get('username')
        password = request.matchdict.get('password')
        same_username = DBSession.query(User).filter_by(username=username).first()
        if same_username:
            return dict(
                status=2,
            )
        else:
            user = User(
                username,
                password,
            )
            user.set_password(password)
            DBSession.add(user)
            DBSession.flush()
        return dict(
            status=1,
        )


# LOGIN
@view_config(route_name='login', renderer='json')
def login_view(request):
    status = 0
    username = request.matchdict.get('username')
    password = request.matchdict.get('password')
    user = DBSession.query(User).filter_by(username=username).first()
    if user is not None and user.validate_password(password):
        session = request.session
        cookie = request.cookies
        session['username'] = username
        cookie['username'] = username
        return dict(
            login=1,
        )
    else:
        return dict(
            login=0,
        )


@view_config(route_name='logout', renderer='json')
def logout_view(request):
    request.session.invalidate()
    return dict(
        status=0,
        login=0,
        logout=request.session,
    )


@view_config(route_name='status_login', renderer='json')
def status_login_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            status_login="not logged",
            status=0,
        )
    else:
        if check_user_admin(request):
            status = 2
        else:
            status = 1
        return dict(
            status_login=request.session['username'],
            status=status,
        )


# LIST
@view_config(route_name='categories_list', renderer='json')
def categories_list_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    try:
        categories = DBSession.query(Category.name, Category.id).filter_by(user=user).all()
        categories_list = []
        for category in categories:
            categories_list.append({'id': category.id, 'name': category.name})
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        categories= categories_list,
        project= 'PyNews'
    )


@view_config(route_name='rsses_list', renderer='json')
def rsses_list_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    try:
        rsses = DBSession.query(Rss.id, Rss.text, Rss.title).filter_by(user=user).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        rsses= rsses,
        project= 'PyNews'
    )


@view_config(route_name='rsses_list_by_category', renderer='json')
def rsses_list_by_category_view(request):
    user = check_user_logged(request)
    category = request.matchdict.get('category')
    category = get_category_by_id(category)
    if category is False:
        return dict(
            rsses= "not no such category",
            project= 'PyNews'
        )
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    try:
        rsses = DBSession.query(Rss.id, Rss.text, Rss.title).filter_by(user=user)
        rsses = rsses.filter(Rss.category.contains(category))
        rsses = rsses.all()
        rsses_list = []
        for rss in rsses:
            rsses_list.append({'id': rss.id, 'text': rss.text, 'title': rss.title})
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        rsses= rsses_list,
        project= 'PyNews'
    )


@view_config(route_name='notes_list', renderer='json')
def notes_list_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    try:
        notes = DBSession.query(Note.id, Note.text, Note.title).filter_by(user=user).all()
        notes_list = []
        for note in notes:
            notes_list.append({'id': note.id, 'text': note.text, 'title': note.title})
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        notes= notes_list,
        project= 'PyNews'
    )


@view_config(route_name='bookmarks_list', renderer='json')
def bookmarks_list_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    try:
        bookmark = DBSession.query(Bookmark.text, Bookmark.title).filter_by(user=user).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        rsses= bookmark,
        project= 'PyNews'
    )


# ADD
@view_config(route_name='categories_add', renderer='json')
def categories_add_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    name = request.matchdict.get('name')
    description = 'description'
    same_name = DBSession.query(Category).filter_by(user=user).filter_by(name=name).first()
    if same_name:
        return dict(
            status= 2,
            project= 'PyNews'
        )
    else:
        category = Category(
            user,
            name.capitalize(),
            description,
        )
        DBSession.add(category)
        DBSession.flush()
    return dict(
        status= 1,
        project= 'PyNews'
    )


@view_config(route_name='rsses_add', renderer='json')
def rsses_add_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    title = request.matchdict.get('title')
    text = request.matchdict.get('text')
    title = base64.b64decode(title)
    text = base64.b64decode(text)
    category = request.matchdict.get('category')
    user = get_user_by_username(user)
    if title == "1":
        try:
            feeds = feedparser.parse( text )
            title = feeds['feed']['title']
        except:
            pass
    if not user:
        return dict(
            status= 2,
            project= 'PyNews'
        )
    category = get_category_by_id(category)
    category_list = [category]
    if not category:
        return dict(
            status= 3,
            project= 'PyNews'
        )
    # same_rss = DBSession.query(Rss).filter(sa.and_(Rss.text==text, Rss.user==user)).first()
    # if same_rss:
    #     return dict(
    #         status= 4,
    #         project= 'PyNews'
    #     )
    rss = Rss(
        user,
        title,
        text,
        category_list,
    )
    DBSession.add(rss)
    DBSession.flush()
    return dict(
        status= 1,
        project= 'PyNews'
    )


@view_config(route_name='notes_add', renderer='json')
def notes_add_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    title = request.matchdict.get('title')
    text = request.matchdict.get('text')
    user = get_user_by_username(user)
    if not user:
        return dict(
            status= 2,
            project= 'PyNews'
        )
    title = base64.b64decode(title)
    text = base64.b64decode(text)
    same_note = DBSession.query(Rss).filter(sa.and_(Note.text==text, Note.user==user)).first()
    if same_note:
        return dict(
            status= 2,
            project= 'PyNews'
        )
    note = Note(
        user,
        title,
        text,
    )
    DBSession.add(note)
    DBSession.flush()
    return dict(
        status= 1,
        project= 'PyNews'
    )


@view_config(route_name='bookmarks_add', renderer='json')
def bookmarks_add_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    title = request.matchdict.get('title')
    text = request.matchdict.get('text')
    user = get_user_by_username(username)
    if not user:
        return dict(
            status= 2,
            project= 'PyNews'
        )
    same_bookmark = DBSession.query(bookmark).filter(sa.and_(Bookmark.text==text, Bookmark.user==user)).first()
    if same_bookmark:
        return dict(
            status= 2,
            project= 'PyNews'
        )
    bookmark = Bookmark(
        user,
        title,
        text,
    )
    DBSession.add(bookmark)
    DBSession.flush()
    return dict(
        status= 1,
        project= 'PyNews'
    )


# DELETE
@view_config(route_name='rsses_delete', renderer='json')
def rsses_delete_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    id = request.matchdict.get('id')
    user = get_user_by_username(user)
    rss = DBSession.query(Rss).filter_by(user=user).filter_by(id=id).first()
    DBSession.delete(rss)
    return dict(
        status= 1,
        project= 'PyNews'
    )


@view_config(route_name='categories_delete', renderer='json')
def categories_delete_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    cat_id = request.matchdict.get('id')
    user = get_user_by_username(user)
    category = DBSession.query(Category).filter_by(user=user).filter_by(id=cat_id).first()
    DBSession.delete(category)
    return dict(
        status= 1,
        project= 'PyNews'
    )


@view_config(route_name='notes_delete', renderer='json')
def notes_delete_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            rsses= "not logged",
            project= 'PyNews'
        )
    note_id = request.matchdict.get('id')
    user = get_user_by_username(user)
    category = DBSession.query(Note).filter_by(user=user).filter_by(id=note_id).first()
    DBSession.delete(category)
    return dict(
        status= 1,
        project= 'PyNews'
    )


# VIEW FEED
@view_config(route_name='view_feed', renderer='json')
def view_feed_view(request):
    feed_requested = request.matchdict.get('feed')
    rss = DBSession.query(Rss).filter_by(id=feed_requested).first()
    rss_id = rss.id
    url = rss.text
    count = rss.count
    title = rss.title
    url = rss.text
    count = 10
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    content = []
    try:
        feeds = feedparser.parse( url )
        title = feeds['feed']['title']
        feed_id = 0
        for items in feeds["items"]:
            text = items['summary_detail']['value']
            soup = BeautifulSoup(text, convertEntities=BeautifulSoup.HTML_ENTITIES)
            result = ""
            if count > 0:
                line = {
                    "head": items['title_detail']['value'],
                    "date": "sans date",
                    "feed": soup.getText(),
                    "link": items['link'],
                    "feed_id": count,
                }
                content.append(line)
                count -= 1
                feed_id += 1
        feed = {
            'url':url,
            'title':title,
            'count':count,
            'content': content,
            'id': rss_id,
        }
        return dict(
            feed= feed,
            title= feeds['feed']['title'],
            project= 'PyNews'
        )
    except:
        feed = {
            'url':url,
            'title':"",
            'count':"",
            'content': content,
            'id': rss_id,
        }
        return dict(
            feed= "error",
            title= "Error unable to fetch url: " + url,
            project= 'PyNews'
        )

# VIEW NOTE
@view_config(route_name='view_note', renderer='json')
def view_note_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    note_requested = request.matchdict.get('note')
    note = DBSession.query(Note).filter_by(user=user).filter_by(id=note_requested).first()
    return dict(
        note= note.text,
        id= note.id,
        project= 'PyNews'
    )


# UPDATE
@view_config(route_name='update_category', renderer='json')
def update_category_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    category_id = request.matchdict.get('category')

    name = request.matchdict.get('name')
    name = name.decode('utf-8')
    DBSession.query(Category).filter_by(user=user).filter_by(id=category_id).update({"name": name.capitalize()})
    return dict(
        name= name,
        project= 'PyNews'
    )


@view_config(route_name='update_rss_category', renderer='json')
def update_rss_category_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    category_id = request.matchdict.get('category')
    category = DBSession.query(Category).get(category_id)
    rss_id = request.matchdict.get('id')
    rss = DBSession.query(Rss).get(rss_id)
    rss.category = [category, ]
    return dict(
        response= rss.category[0].id,
        project= 'PyNews'
    )

@view_config(route_name='update_rss_url', renderer='json')
def update_rss_url_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    rss_id = request.matchdict.get('id_rss')
    rss_url = request.matchdict.get('url')
    rss_url = base64.b64decode(rss_url)
    rss = DBSession.query(Rss).get(rss_id)
    rss.text = rss_url
    return dict(
        response= rss.id,
        project= 'PyNews'
    )


@view_config(route_name='update_note', renderer='json')
def update_note_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    note_id = request.matchdict.get('note')

    text = request.matchdict.get('text')
    text = base64.b64decode(text)
    DBSession.query(Note).filter_by(user=user).filter_by(id=note_id).update({"text": text})
    return dict(
        note= text,
        id= note_id,
        project= 'PyNews'
    )

@view_config(route_name='auth_twitter', renderer='json')
def auth_twitter_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    app_twitter_auth = DBSession.query(Setting).all()
    user = get_user_by_username(user)
    token = twittertoken.GenerateToken(app_twitter_auth[0].twitter_api_key, app_twitter_auth[0].twitter_api_secret)
    


    return dict(
        twitter= token.getrequestTokenURL(),
        project= 'PyNews'
    )

@view_config(route_name='end_auth_twitter', renderer='json')
def end_auth_twitter_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    oauth_token = request.matchdict.get('oauth_token')
    oauth_token_secret = request.matchdict.get('oauth_token_secret')
    oauth_verifier = request.matchdict.get('oauth_verifier')

    app_twitter_auth = DBSession.query(Setting).all()
    token = twittertoken.GenerateToken(app_twitter_auth[0].twitter_api_key, app_twitter_auth[0].twitter_api_secret)
    end_auth = token.authRequest(oauth_token, oauth_token_secret, oauth_verifier)

    user = check_user_logged(request)
    if user:
        DBSession.query(User).filter_by(username=user).update({"access_token": end_auth['access_token']})
        DBSession.query(User).filter_by(username=user).update({"access_token_secret": end_auth['access_token_secret']})
    return dict(
        twitter= end_auth,
        project= 'PyNews'
    )

@view_config(route_name='twitter', renderer='json')
def twitter_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )

    session = check_twitter_logged(request)
    if session is False:
        return dict(
            feed= "no twitter",
            project= 'PyNews'
        )
    user = get_user_by_username(user)

    app_twitter_auth = DBSession.query(Setting).all()
    api_key = app_twitter_auth[0].twitter_api_key
    api_secret = app_twitter_auth[0].twitter_api_secret
    access_token =  session['access_token']
    access_token_secret = session['access_token_secret']
    auth = OAuth(
        consumer_key=api_key,
        consumer_secret=api_secret,
        token=access_token,
        token_secret=access_token_secret
    )
    t = Twitter(
            auth=auth
           )
    try:
        response = t.statuses.home_timeline(count=800)
        return dict(
            twitter= response,
            project= 'PyNews'
        )
    except Exception, e:
        return dict(
            feed= "no twitter",
            project= 'PyNews'
        )

@view_config(route_name='mail', renderer='json')
def mail_view(request):
    user = check_user_logged(request)
    if user is False:
        return dict(
            feed= "not logged",
            project= 'PyNews'
        )
    user = get_user_by_username(user)
    result = []
    mail_params = DBSession.query(Mail).filter_by(user=user)
    resultat = mail_params.all()
    for el in resultat:
        config_file = 'config-email.ini'
        connect_conf = config.new_context_from_file(config_file, section='imap')
        connect_conf['hostname'] = el.hostname
        connect_conf['password'] = el.password
        connect_conf['username'] = el.username
        connect_conf['ssl'] = el.ssl
        connect_conf['port'] = el.port
        try:
            imap_account =  imap_cli.connect(**connect_conf)
        except Exception, e:
            return dict(
                mails= ["Error while connecting to imap server"],
                project= 'PyNews'
            )

        count = int(imap_cli.change_dir(imap_account, 'INBOX')[0]) + 10
        response = []
        for ite in xrange(count -10, count):
            mail_response = dict()
            mail = fetch.read(imap_account, ite, directory="INBOX")
            mail_response['from'] = mail['headers']['From']
            mail_response['to'] = mail['headers']['To']
            mail_response['date'] = mail['headers']['Date']
            mail_response['subject'] = mail['headers']['Subject']
            mail_response['parts'] = mail['parts'][0]['as_string']
            response.append(mail_response)
        imap_cli.disconnect(imap_account)
        result.append({"mail_user": connect_conf['username'], "mail_box": response})
    return dict(
        mails= result,
        project= 'PyNews'
    )


@view_config(route_name='index', renderer='templates/angular.pt')
def index_view(request):
    return dict(status=True,
        title=u'Hello world',
        project= 'PyNews'
    )


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_PyNews_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

