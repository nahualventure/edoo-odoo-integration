import requests
import api
from django.conf import settings
import xmlrpclib


def create_client(data):
    try:
        response = api.post_client(data)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


def call_client(client_id):
    try:
        response = api.get_client(client_id)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


def update_client(client_id, data):
    try:
        response = api.put_client(client_id, data=data)
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


def call_contracts():
    try:
        response = api.get_contracts()
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


def call_discounts():
    try:
        response = api.get_discounts()
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


def call_account_statement(client_id, comercial_id, data):
    try:
        response = api.get_account_statement(client_id, comercial_id, data)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


def set_contract(client_id, data):
    try:
        response = api.set_contract(client_id, data=data)
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


def set_discount(client_id, data):
    try:
        response = api.set_discount(client_id, data=data)
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


def authenticate_user(host, database, username, password):
    try:
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(host))

        return common.authenticate(database, username, password, {})
    except Exception as e:
        raise e
