import pymongo
from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_from_directory,
    send_file
)
from bson.objectid import ObjectId
import api
import os
import sentry_sdk
from waitress import serve
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from sentry_sdk.integrations.flask import FlaskIntegration

# from meinheld import server
NOW = datetime.today().strftime('%Y-%m-%d')

# DATABASE

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["api_platform"]

app = Flask(__name__)
app.secret_key = 'somesecretkeythatonlyishouldknow'

sentry_sdk.init(
    dsn="https://cb15bf47dbf84812a698a1d23ef0a527:16d5b523c6db4071ba2d61927438850c@sentry.nextify.vn/12",

    integrations=[FlaskIntegration()]
)


@app.template_filter('shorten_id')
def shorten_id(value):
    return abs(hash(value)) % (10 ** 8)


@app.context_processor
def check_service_registered():
    def _check_service_registered(client_id, service_id):
        if not isinstance(client_id, ObjectId):
            client_id = ObjectId(client_id)
        find_client = mydb.clients.find_one({"_id": client_id})
        register_services = find_client.get('services')
        for x in register_services:
            if x['service_id'] == service_id:
                return 1
        return 0
    return dict(check_service_registered=_check_service_registered)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.before_request
def before_request():
    g.user = None

    if 'user_name' in session:
        if mydb.users.find_one({'username': session['user_name']}):
            g.user = mydb.users.find_one({'username': session['user_name']})
        elif mydb.supporters.find_one({'email': session['user_name']}):
            g.user = mydb.supporters.find_one({'email': session['user_name']})
        elif mydb.partners.find_one({'email': session['user_name']}):
            g.user = mydb.partners.find_one({'email': session['user_name']})
        elif mydb.clients.find_one({'email': session['user_name']}):
            g.user = mydb.clients.find_one({'email': session['user_name']})


@app.route('/', methods=['GET', 'POST'])
def home():
    if not g.user:
        return redirect(url_for('login'))

    return render_template('dashboard.html', user_name=session['user_name'], role=session['role'], id=session['id'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_name', None)

        username = request.form['username']
        password = request.form['password']

        if mydb.users.find_one({'username': username, 'password': password}):
            session['user_name'] = username
            session['id'] = str(mydb.users.find_one(
                {'username': username, 'password': password}).get('_id'))
            print(1111111111)
            session['role'] = 'admin'
            return redirect(url_for('dashboard'))
        elif mydb.supporters.find_one({'email': username}):
            print(222222222222)
            if (api.verify_password(password, mydb.supporters.find_one({'email': username}).get('password'))):
                session['user_name'] = username
                session['id'] = str(mydb.supporters.find_one(
                    {'email': username}).get('_id'))
                session['role'] = 'supporter'
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html')
        elif mydb.partners.find_one({'email': username}):
            print(3333333333)
            if (api.verify_password(password, mydb.partners.find_one({'email': username}).get('password'))):
                session['user_name'] = username
                session['id'] = str(mydb.partners.find_one(
                    {'email': username}).get('_id'))
                session['role'] = 'partner'
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html')
        elif mydb.clients.find_one({'email': username}):
            print(444444444444)
            if (api.verify_password(password, mydb.clients.find_one({'email': username}).get('password'))):
                session['user_name'] = username
                session['id'] = str(mydb.clients.find_one(
                    {'email': username}).get('_id'))
                session['role'] = 'client'
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/index', methods=['GET'])
def index():
    if not g.user:
        return redirect(url_for('login'))

    return render_template('index.html', user_name=session['user_name'])


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not g.user:
        return redirect(url_for('login'))

    return render_template('dashboard.html', user_name=session['user_name'], role=session['role'], id=session['id'])


# CLIENT


@app.route('/manage_clients', methods=['GET'])
def manage_clients():
    if not g.user:
        return redirect(url_for('login'))
    if session['role'] == 'client':
        return redirect(url_for('dashboard'))
    if session['role'] == 'admin' or session['role'] == 'supporter':
        clients = mydb.clients.find()
    else:
        clients = api.get_partner_client(session['id'])
    return render_template('manage_clients.html', user_name=session['user_name'], id=session['id'], role=session['role'], clients=clients)


@app.route('/client_add', methods=['GET', 'POST'])
def client_add():
    if not g.user:
        return redirect(url_for('login'))
    if session['role'] == 'client':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        inputName = request.form['inputName']
        inputEmail = request.form['inputEmail']
        inputPassword = request.form['inputPassword']
        # inputCompany = request.form['inputCompany']
        inputPhoneNumber = request.form['inputPhoneNumber']
        inputPartner = request.form['inputPartner']
        inputActiveStatus = (request.form.getlist(
            'inputActiveStatus')) and 1 or 0
        inputAPIKey = request.form['inputAPIKey']
        if inputPartner and len(inputPartner) > 0:
            if not isinstance(inputPartner, ObjectId):
                inputPartner = ObjectId(inputPartner)
        else:
            inputPartner = ""
        inputService = request.form.getlist('inputService')
        services = []
        for service_id in inputService:
            service = {}
            service['service_id'] = service_id
            service['register_date'] = NOW
            services.append(service)

        target = '/static/img/'
        filename = request.files['face_image']
        inputAvatar = target + filename.filename
        if inputAvatar == target:
            inputAvatar = '/static/img/undraw_profile.svg'

        insert_data = {
            'name': inputName,
            'avatar': inputAvatar,
            'email': inputEmail,
            'password': api.get_password_hash(inputPassword),
            'phone': inputPhoneNumber,
            'partner_id': inputPartner,
            # 'company': inputCompany,
            'active': inputActiveStatus,
            'api_key': inputAPIKey,
            'services': services,
            'timestamp': NOW
        }

        mydb.clients.insert_one(insert_data)
        return redirect(url_for('manage_clients'))

    else:
        if session['role'] == "partner":
            partners = mydb.partners.find({'_id': ObjectId(session['id'])})
            services = api.get_service_registered_partner(session['id'])
        else:
            partners = mydb.partners.find()
            services = mydb.services.find()
        return render_template('client_add.html', user_name=session['user_name'], role=session['role'], id=session['id'], clients=mydb.clients.find(), partners=partners, services=services)


@app.route('/client_edit/<client_id>', methods=['GET', 'POST'])
def client_edit(client_id):
    if not g.user:
        return redirect(url_for('login'))
    if session['role'] == 'client':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        inputName = request.form['inputName']
        inputEmail = request.form['inputEmail']
        inputPassword = request.form['inputPassword']
        # inputCompany = request.form['inputCompany']
        inputPhoneNumber = request.form['inputPhoneNumber']
        inputActiveStatus = (request.form.getlist(
            'inputActiveStatus')) and 1 or 0
        inputPartner = request.form['inputPartner']
        inputAPIKey = request.form['inputAPIKey']

        find_by_id = api.get_client_info(client_id)
        target = '/static/img/'
        filename = request.files['face_image']
        inputAvatar = target + filename.filename
        if inputAvatar == target:
            inputAvatar = find_by_id.get('avatar')

        if inputPartner and len(inputPartner) > 0:
            if not isinstance(inputPartner, ObjectId):
                inputPartner = ObjectId(inputPartner)
        else:
            inputPartner = ""

        inputService = request.form.getlist('inputService')
        services = []
        for service_id in inputService:
            service = {}
            if service_id in api.get_id_service_registered(client_id):
                service = api.get_service_in_client(client_id, service_id)
                services.append(service)
            else:
                service['service_id'] = service_id
                service['register_date'] = NOW
                services.append(service)

        myquery = {"_id": ObjectId(client_id)}
        newvalues = {"$set": {'name': inputName,
                              'avatar': inputAvatar,
                              'email': inputEmail,
                              'password': api.get_password_hash(inputPassword),
                              'phone': inputPhoneNumber,
                              #   'company': inputCompany,
                              'partner_id': inputPartner,
                              'active': inputActiveStatus,
                              'api_key': inputAPIKey,
                              'services': services,
                              'timestamp': NOW}}

        mydb.clients.update_one(myquery, newvalues)
        return redirect(url_for('manage_clients'))
    else:
        if session['role'] == "partner":
            partners = mydb.partners.find({'_id': ObjectId(session['id'])})
            services = api.get_service_registered_partner(session['id'])
        else:
            partners = mydb.partners.find()
            services = mydb.services.find()
        find_by_id = api.get_client_info(client_id)
        return render_template('client_edit.html', user_name=session['user_name'], role=session['role'], id=session['id'], client=find_by_id, partners=partners, services=services, service_ids=api.get_id_service_registered(client_id))


@app.route('/client_delete/<client_id>', methods=['GET'])
def client_delete(client_id):
    if not g.user:
        return redirect(url_for('login'))
    if session['role'] == 'client':
        return redirect(url_for('dashboard'))
    find_by_id = api.get_client_info(client_id)
    return render_template('client_delete.html', user_name=session['user_name'], id=session['id'], role=session['role'], client=find_by_id)


@app.route('/remove_client/<client_id>', methods=['GET'])
def remove_client(client_id):
    find_by_id = api.get_client_info(client_id)
    mydb.clients.delete_one({'_id': ObjectId(client_id)})
    return redirect(url_for('manage_clients'))


# SERVICE
@app.route('/my_services/<client_id>', methods=['GET', 'POST'])
def my_services(client_id):
    if not g.user:
        return redirect(url_for('login'))
    if session['role'] == 'client':
        find_service = api.get_service_registered(client_id)
    elif session['role'] == 'partner':
        find_service = api.get_service_registered_partner(client_id)
    return render_template('my_services.html', user_name=session['user_name'], role=session['role'], services=find_service, id=session['id'])


@app.route('/my_services/<client_id>/register_service', methods=['GET', 'POST'])
def register_service(client_id):
    if not g.user:
        return redirect(url_for('login'))
    if session['role'] == 'client':
        find_service = api.get_services_not_registered(client_id)
    elif session['role'] == 'partner':
        find_service = api.get_services_not_registered_partner(client_id)
    return render_template('register_service.html', user_name=session['user_name'], id=session['id'], role=session['role'], services=find_service)


@app.route('/blank', methods=['GET'])
def blank():
    if not g.user:
        return redirect(url_for('login'))

    return render_template('blank.html', user_name=session['user_name'], role=session['role'])


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_name', None)
    return redirect('/login')


if __name__ == "__main__":
    # app.run(host='127.0.0.1', port=8099, debug=True)
    serve(app, host='0.0.0.0', port=9197)
