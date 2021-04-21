import pymongo
from bson.objectid import ObjectId
from passlib.context import CryptContext
import requests

myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
mydb = myclient["api_platform"]

# PASSWORD
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_client_info(client_id):
    if not isinstance(client_id, ObjectId):
        client_id = ObjectId(client_id)

    return mydb.clients.find_one({'_id': client_id})


def get_partner_info(partner_id):
    if not isinstance(partner_id, ObjectId):
        partner_id = ObjectId(partner_id)

    return mydb.partners.find_one({'_id': partner_id})


def get_supporter_info(supporter_id):
    if not isinstance(supporter_id, ObjectId):
        supporter_id = ObjectId(supporter_id)

    return mydb.supporters.find_one({'_id': supporter_id})


def get_service_info(service_id):
    if not isinstance(service_id, ObjectId):
        service_id = ObjectId(service_id)

    return mydb.services.find_one({'_id': service_id})


def get_voiceid_info(voiceid_id):
    if not isinstance(voiceid_id, ObjectId):
        voiceid_id = ObjectId(voiceid_id)

    return mydb.voiceids.find_one({'_id': voiceid_id})


# lấy id dịch vụ đã đăng kí của client qua client id
def get_id_service_registered(client_id):
    if not isinstance(client_id, ObjectId):
        client_id = ObjectId(client_id)
    register_services = mydb.clients.find_one(
        {"_id": client_id}).get('services')
    if (register_services) is None:
        return []
    service_ids = []
    for x in register_services:
        id = x['service_id']
        service_ids.append(id)
    return service_ids

    # lấy id dịch vụ đã đăng kí của partner qua partner id


def get_id_service_registered_parter(partner_id):
    if not isinstance(partner_id, ObjectId):
        partner_id = ObjectId(partner_id)
    register_services = mydb.partners.find_one(
        {"_id": partner_id}).get('services')
    if (register_services) is None:
        return []
    service_ids = []
    for x in register_services:
        id = x['service_id']
        service_ids.append(id)
    return service_ids

# print(get_id_service_registered("60652517096a934d9a8c877d"))

# lấy thông tin chi tiết dịch vụ đã đăng ký thông qua client id


def get_service_registered(client_id):
    if not isinstance(client_id, ObjectId):
        client_id = ObjectId(client_id)
    find_client = mydb.clients.find_one({"_id": client_id})
    if find_client is None:
        return []
    register_services = find_client.get('services')
    services = []
    for x in register_services:
        service = (get_service_info(x['service_id']))
        if service is None:
            continue
        service['register_date'] = x["register_date"]
        services.append(service)
    return services

# lấy thông tin chi tiết dịch vụ đã đăng ký thông qua partner id


def get_service_registered_partner(partner_id):
    if not isinstance(partner_id, ObjectId):
        partner_id = ObjectId(partner_id)
    find_partner = mydb.partners.find_one({"_id": partner_id})
    if find_partner is None:
        return []
    register_services = find_partner.get('services')
    services = []
    for x in register_services:
        service = (get_service_info(x['service_id']))
        if service is None:
            return []
        service['register_date'] = x["register_date"]
        services.append(service)
    return services


def check_service_registered(client_id, service_id):
    if not isinstance(client_id, ObjectId):
        client_id = ObjectId(client_id)
    find_client = mydb.clients.find_one({"_id": client_id})
    register_services = find_client.get('services')
    # return register_services
    for x in register_services:
        if x['service_id'] == service_id:
            return 1
    return 0

# print(check_service_registered("60652517096a934d9a8c877d","60696c999cc5bf79aeb6983e"))

# lấy thông tin khách hàng của đối tác qua partner id


def get_partner_client(partner_id):
    if not isinstance(partner_id, ObjectId):
        partner_id = ObjectId(partner_id)
    clients = mydb.clients.find({"partner_id": partner_id})
    list = []
    for x in clients:
        list.append(x)
    return list

# print(get_partner_client("6069d680481c5cb101ddec73"))

# lấy thông tin dịch vụ chưa đăng ký


def get_services_not_registered(client_id):
    if not isinstance(client_id, ObjectId):
        client_id = ObjectId(client_id)
    register_services = mydb.clients.find_one(
        {"_id": client_id}).get('services')
    id_register = []
    for id in register_services:
        id_register.append(id.get('service_id'))
    if (register_services) is None:
        return []
    service_ids = []
    services = mydb.services.find()
    # print(services)
    for x in services:
        if str(x.get('_id')) not in id_register:
            service_ids.append(x)
    return service_ids

# lấy thông tin dịch vụ chưa đăng ký PARTNER


def get_services_not_registered_partner(partner_id):
    if not isinstance(partner_id, ObjectId):
        partner_id = ObjectId(partner_id)
    register_services = mydb.partners.find_one(
        {"_id": partner_id}).get('services')
    id_register = []
    for id in register_services:
        id_register.append(id.get('service_id'))
    if (register_services) is None:
        return []
    service_ids = []
    services = mydb.services.find()
    # print(services)
    for x in services:
        if str(x.get('_id')) not in id_register:
            service_ids.append(x)
    return service_ids

# print(get_services_not_registered_partner("6065437a49cd3d61d0f74065"))
# print(get_services_not_registered("6069d37a4bfb1286ef07bd54"))

# print(get_services_not_registered("60652517096a934d9a8c877d"))

# lấy service_id và ngày đăng ký của dịch vụ trong client


def get_service_in_client(client_id, service_id):
    if not isinstance(client_id, ObjectId):
        client_id = ObjectId(client_id)
    services = mydb.clients.find_one({'_id': client_id}).get('services')
    for service in services:
        if service.get('service_id') == service_id:
            return service

# lấy service_id và ngày đăng ký của dịch vụ trong partner


def get_service_in_partner(partner_id, service_id):
    if not isinstance(partner_id, ObjectId):
        partner_id = ObjectId(partner_id)
    services = mydb.partners.find_one({'_id': partner_id}).get('services')
    for service in services:
        if service.get('service_id') == service_id:
            return service
# print(get_service_in_client("60652517096a934d9a8c877d","60696c999cc5bf79aeb6983e"))

# lấy thông tin api routing


def get_api_routing(service_id):
    if not isinstance(service_id, ObjectId):
        service_id = ObjectId(service_id)
    find = mydb.services.find_one({"_id": service_id})
    if find is None:
        return []
    api_routing = find.get('api_routing')
    if api_routing is None:
        return []
    api_routings = []
    for x in api_routing:
        api_routings.append(x)
    return api_routings


def get_token_voicebio():
    url = "http://103.141.140.189:8050/api/voicebio/auth"
    payload = {'username': "vnpt_test",
               "password": "vnpt@123"}
    files = [
    ]
    headers = {}

    response = requests.request(
        "POST", url, headers=headers, data=payload, files=files).json()
    return response["token"]

# print(get_token_voicebio())
