from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from wsgicors import CORS
from .models import (
    DBSession,
    Base,
)

from pyramid.session import SignedCookieSessionFactory


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('fonts', 'static', cache_max_age=3600)

# INDEX HTML
    config.add_route('index', '/')

# ADMIN
    config.add_route('users_add', '/users/add/{username}/{password}')
    config.add_route('users_list', '/users/list')
    config.add_route('users_delete', '/users/delete/{username}/{password}')

# LOGIN
    config.add_route('login', '/login/{username}/{password}')
    config.add_route('logout', '/logout')
    config.add_route('status_login', '/status_login')

# CATEGORIES
    config.add_route('categories_add', '/categories/add/{name}')
    config.add_route('update_category', '/category/update/{category}/{name}')
    config.add_route('categories_delete', '/categories/delete/{id}')
    config.add_route('categories_list', '/categories/list')

# RSSES
    config.add_route('rsses_add', '/rsses/add/{title}/{text}/{category}')
    config.add_route('view_feed', '/feed/{feed}')
    config.add_route('update_rss_url', '/rss/update/url/{id_rss}/{url}')
    config.add_route('update_rss_category', '/rss/update/category/{category}/{id}')
    config.add_route('rsses_delete', '/rsses/delete/{id}')
    config.add_route('rsses_list', '/rsses/list')
    config.add_route('rsses_list_by_category', '/rsses_by_category/{category}')

# NOTES
    config.add_route('notes_add', '/notes/add/{title}/{text}')
    config.add_route('update_note', '/note/update/{note}/{text}')
    config.add_route('notes_delete', '/notes/delete/{id}')
    config.add_route('notes_list', '/notes/list')
    config.add_route('view_note', '/note/{note}')

# BOOKMARKS
    config.add_route('bookmarks_add', '/bookmarks/add/{title}/{text}')
    config.add_route('bookmarks_delete', '/bookmarks/delete/{id}')
    config.add_route('bookmarks_list', '/bookmarks/list')

# TWITTER
    config.add_route('register_api_twitter', '/register_api_twitter/{twitter_api_key}/{twitter_api_secret}')
    config.add_route('end_auth_twitter', '/end_auth_twitter/{oauth_token}/{oauth_token_secret}/{oauth_verifier}')
    config.add_route('auth_twitter', '/auth_twitter')
    config.add_route('twitter', '/twitter')

# MAIL
    config.add_route('mail', '/mail')

# IMPORT
    config.add_route('import_xml', '/import_xml')

# STARTING
    config.scan()

    my_session_factory = SignedCookieSessionFactory('itsaseekreet')

    config.set_session_factory(my_session_factory)
    # return config.make_wsgi_app()
    return CORS(config.make_wsgi_app(),header="*", methods="*", maxage="180", origin = "*")
