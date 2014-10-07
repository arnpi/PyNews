from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    Group,
    Category,
    User,
    Flux,
    )


@view_config(route_name='users', renderer='json')
def users_view(request):
    try:
        users = DBSession.query(User.username).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        users= users,
        project= 'PyNews'
    )


@view_config(route_name='categories', renderer='json')
def categories_view(request):
    try:
        categories = DBSession.query(Category.name).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        categories= categories,
        project= 'PyNews'
    )


@view_config(route_name='groups', renderer='json')
def groups_view(request):
    try:
        groups = DBSession.query(Group.name).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        groups= groups,
        project= 'PyNews'
    )


@view_config(route_name='fluxes', renderer='json')
def fluxes_view(request):
    try:
        fluxes = DBSession.query(Flux.text, Flux.title).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=500)
    return dict(
        fluxes= fluxes,
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

