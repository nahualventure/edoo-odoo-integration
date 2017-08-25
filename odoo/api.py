import requests
from django.conf import settings


class Odoo:
    # main URL of API
    BASE_URL = 'odoo.edoo.io'
    if hasattr(settings, 'ODOO_SETTINGS'):
        BASE_URL = settings.ODOO_SETTINGS['BASE_URL']

    CONTRACTS = "contracts"
    CLIENTS = "clients"
    DISCOUNTS = "discounts"
    ACCOUNT_STATEMENT = "account-statement"


STATIC_DATA = {}
if hasattr(settings, 'ODOO_SETTINGS'):
    STATIC_DATA = {
        'url': settings.ODOO_SETTINGS['URL'],
        'db': settings.ODOO_SETTINGS['DB'],
        'username': settings.ODOO_SETTINGS['USERNAME'],
        'password': settings.ODOO_SETTINGS['PASSWORD']
    }


def post_client(data):
    return requests.post("{0}{1}".format(Odoo.BASE_URL, Odoo.CLIENTS),
                         data=data.update(STATIC_DATA))


def get_client(client_id):
    url = "{0}{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id)
    print 'GET: <' + url + '>'
    return requests.get(url, data=STATIC_DATA)


def put_client(client_id, data):
    return requests.put("{0}{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id),
                        data=data.update(STATIC_DATA))


def get_contracts():
    return requests.get("{0}{1}".format(Odoo.BASE_URL, Odoo.CONTRACTS), data=STATIC_DATA)


def set_contract(client_id, data):
    return requests.put("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.CONTRACTS),
                        data=data.update(STATIC_DATA))


def get_discounts():
    return requests.get("{0}{1}".format(Odoo.BASE_URL, Odoo.DISCOUNTS), data=STATIC_DATA)


def set_discount(client_id, data):
    return requests.put("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.DISCOUNTS),
                        data=data.update(STATIC_DATA))


def get_account_statement(client_id, data):
    return requests.get("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.ACCOUNT_STATEMENT),
                        data=data.update(STATIC_DATA))
