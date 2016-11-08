import requests
import api


def create_client(data):
    try:
        response = api.post_client(data)
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


def call_client(client_id):
    try:
        response = api.get_client(client_id)
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


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


def call_account_statement(client_id):
    try:
        response = api.get_account_statement(client_id)
        return response.status_code == requests.codes.ok, response.json()
    except requests.RequestException:
        print ("Error en el request")
        return False, {}


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
