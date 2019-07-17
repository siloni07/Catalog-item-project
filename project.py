import requests
from flask import make_response
import json
import httplib2
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from database_setup import Base, Catalog, CatalogItem, User
from flask_httpauth import HTTPBasicAuth
from sqlalchemy.orm import sessionmaker,joinedload
from sqlalchemy import create_engine, asc, desc
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, session as login_session, g
import random
import string
app = Flask(__name__)


auth = HTTPBasicAuth()

# Connect to Database and create database session
engine = create_engine(
    'sqlite:///catalogitem.db',
    connect_args={
        'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog WebApp"


@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    print("entered in gconnect")
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Show all catalogs
@app.route('/')
@app.route('/catalog')
def showCatalogs():

    catalog = session.query(Catalog).order_by(asc(Catalog.name))
    catalogItem = session.query(CatalogItem).order_by(desc(CatalogItem.id))
    if 'username' not in login_session:
        return render_template(
            'publiccatalogs.html',
            catalog=catalog,
            catalogitem=catalogItem)
    else:
        return render_template(
            'catalogs.html',
            catalog=catalog,
            catalogitem=catalogItem)

#Create new Item in specific catalog
@app.route('/catalog/<int:catalog_id>/newItem/', methods=['GET', 'POST'])
def newCatalog(catalog_id):

    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized to create Catalog');}</script><body "
    if request.method == 'POST':
        newCatalog = CatalogItem(
            title=request.form['title'],
            description=request.form['description'],
            catalog_id=catalog_id)
        session.add(newCatalog)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newCatalog.title))
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newItem.html', catalog=catalog)

#Show all menu items for specific catalog
@app.route('/catalog/<int:catalog_id>/MenuItem', methods=['GET'])
def showMenuItem(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    catalogItem = session.query(CatalogItem).filter_by(
        catalog_id=catalog_id).all()
    creator = getUserInfo(catalog.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template(
            'publicmenuitem.html',
            catalogItem=catalogItem,
            catalog=catalog)
    else:
        return render_template(
            'showmenuitem.html',
            catalogItem=catalogItem,
            catalog=catalog)

#Edit menu Item for specific catalog
@app.route(
    '/catalog/<int:menu_id>/<int:catalog_id>/EditItem',
    methods=[
        'GET',
        'POST'])
def editMenuItem(menu_id, catalog_id):
    if 'username' not in login_session:
        return redirect('/catalog')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    catalogItem = session.query(CatalogItem).filter_by(id=menu_id).one()
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized to edit Catalog');}</script><body "

    if request.method == 'POST':
        if request.form['title']:
            catalogItem.title = request.form['title']
        if request.form['description']:
            catalogItem.description = request.form['description']
        if request.form['category']:
            catalogItem.price = request.form['category']
        session.add(catalogItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(
            url_for(
                'showMenuItem',
                catalog_id=catalogItem.catalog_id))
    else:
        return render_template(
            'editmenuitem.html',
            catalogItem=catalogItem,
            catalog=catalog)

#Delete menu item for specific catalog
@app.route(
    '/catalog/<int:menu_id>/<int:catalog_id>/DeleteItem',
    methods=[
        'GET',
        'POST'])
def deleteMenuItem(menu_id, catalog_id):
    if 'username' not in login_session:
        return redirect('/catalog')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    catalogItem = session.query(CatalogItem).filter_by(id=menu_id).one()
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized to delete Catalog');}</script> "

    if request.method == 'POST':
        session.delete(catalogItem)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(
            url_for(
                'showMenuItem',
                catalog_id=catalogItem.catalog_id))
    else:
        return render_template(
            'deletemenuitem.html',
            catalogItem=catalogItem,
            catalog=catalog)

#JSON endpoints 
@app.route('/catalog.json')
def catalogMenuItemJSON():
    categories = session.query(Catalog).options(joinedload(Catalog.catalog_items)).all()
    return jsonify(Catalog=[dict(c.serialize, items=[i.serialize
                                                     for i in c.catalog_items])
                         for c in categories])


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.menu_id
    except BaseException:
        return None

#To logout from gmail account
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalogs'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalogs'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.Debug = True
    app.run(host='0.0.0.0', port=8000)
