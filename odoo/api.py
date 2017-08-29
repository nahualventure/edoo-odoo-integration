import requests
from django.conf import settings
import xmlrpclib
import services

if not hasattr(settings, 'ODOO_SETTINGS'):
    raise Exception('No settings found for Odoo.')


class Odoo:
    CONTRACTS = "contracts"
    CLIENTS = "clients"
    DISCOUNTS = "discounts"
    ACCOUNT_STATEMENT = "account-statement"

    CONTEXT = {
        'host': settings.ODOO_SETTINGS['HOST'],
        'db': settings.ODOO_SETTINGS['DB'],
        'username': settings.ODOO_SETTINGS['USERNAME'],
        'password': settings.ODOO_SETTINGS['PASSWORD']
    }


def post_client(data):
    return requests.post("{0}{1}".format(Odoo.BASE_URL, Odoo.CLIENTS),
                         data=data.update(CONTEXT))


def get_client(client_id):
    url = "{0}{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id)
    return requests.get(url, data=CONTEXT)


def put_client(client_id, data):
    return requests.put("{0}{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id),
                        data=data.update(CONTEXT))


def get_contracts():
    return requests.get("{0}{1}".format(Odoo.BASE_URL, Odoo.CONTRACTS), data=CONTEXT)


def set_contract(client_id, data):
    return requests.put("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.CONTRACTS),
                        data=data.update(CONTEXT))


def get_discounts():
    return requests.get("{0}{1}".format(Odoo.BASE_URL, Odoo.DISCOUNTS), data=CONTEXT)


def set_discount(client_id, data):
    return requests.put("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.DISCOUNTS),
                        data=data.update(CONTEXT))


def get_account_statement(client_id, filters):
    url, db, username, password = \
    Odoo.CONTEXT['host'], Odoo.CONTEXT['db'], Odoo.CONTEXT['username'], Odoo.CONTEXT['password']

    common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    clietAccountMoves = models.execute_kw(db, uid, password,
        'account.move.line', 'search_read',
        [[
            ['partner_id', '=', client_id],
            ['reconciled', '=', False],
            # '|',
            # ['account_id.type', '=', 'receivable'],
            # ['account_id.type', '=', 'liquidity'],
        ]],
        {
            'limit': 10
        }
    )

    accountState = []

    for record in clietAccountMoves:
        move = {
            "id": record['id'],
            "date": str(record['date']),
            "name": str(record['name']),
            "description": "Descripcion pendiente de definir!",
            "reference": "Referencia pendiente de definir!",
        }

        debit = record['debit']
        credit = record['credit']

        if (debit > 0):
            move["amount"] = debit

        if (credit > 0):
            move["amount"] = credit

        accountState.append(move)

    return accountState
