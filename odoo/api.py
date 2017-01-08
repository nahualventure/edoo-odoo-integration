import requests
from django.conf import settings


class Odoo:
    # main URL of API
    BASE_URL = 'http://localhost:8069'
    if hasattr(settings, 'ODOO_SETTINGS'):
        BASE_URL = settings.ODOO_SETTINGS['BASE_URL']

    CONTRACTS = "contracts"
    CLIENTS = "clients"
    DISCOUNTS = "discounts"
    ACCOUNT_STATEMENT = "account-statement"


def post_client(data):
    return requests.post("{0}/{1}".format(Odoo.BASE_URL, Odoo.CLIENTS),
                         data=data)


def get_client(client_id):
    return requests.get("{0}/{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id))


def put_client(client_id, data):
    return requests.put("{0}/{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id),
                        data=data)


def get_contracts():
    return requests.get("{0}/{1}".format(Odoo.BASE_URL, Odoo.CONTRACTS))


def set_contract(client_id, data):
    return requests.put("{0}/{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS,
                                                 client_id, Odoo.CONTRACTS), data=data)


def get_discounts():
    return requests.get("{0}/{1}".format(Odoo.BASE_URL, Odoo.DISCOUNTS))


def set_discount(client_id, data):
    return requests.put("{0}/{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS,
                                                 client_id, Odoo.DISCOUNTS), data=data)


def get_account_statement(client_id):
    return requests.get("{0}/{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS,
                                                 client_id, Odoo.ACCOUNT_STATEMENT))


def test_request():
    return requests.get(Odoo.BASE_URL)
