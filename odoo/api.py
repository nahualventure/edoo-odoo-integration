# -*- coding: utf-8 -*-

import requests
from django.conf import settings
try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy
import time
try:
    from . import services
except ImportError:
    import services

import json


if not hasattr(settings, 'ODOO_SETTINGS'):
    raise Exception('No settings found for Odoo.')


class Odoo:
    CONTRACTS = "contracts"
    CLIENTS = "clients"
    DISCOUNTS = "discounts"
    ACCOUNT_STATEMENT = "account-statement"
    DEFAULT_AVATAR = "https://www.drupal.org/files/issues/default-avatar.png"

    CONTEXT = {
        'host': settings.ODOO_SETTINGS['HOST'],
        'db': settings.ODOO_SETTINGS['DB'],
        'username': settings.ODOO_SETTINGS['USERNAME'],
        'password': settings.ODOO_SETTINGS['PASSWORD'],
    }

    CUSTOM_SETTINGS = {
        'instance_prefix': settings.ODOO_SETTINGS['INSTANCE_PREFIX'],
        'family_code_prefix': settings.ODOO_SETTINGS['FAMILY_CODE_PREFIX'],
        'comercial_code_sufix': settings.ODOO_SETTINGS['COMERCIAL_CODE_SUFIX'],
        'company_pk': settings.ODOO_SETTINGS['COMPANY_PK'],
    }


def post_client(data):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    partner = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'post_client', [{ 'name': data.get('name') }]
    )

    return partner


def get_client(client_id):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)

    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    client = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[['id', '=', client_id]]]
    )

    if not len(client):
        return None

    return client[0]

def get_data_clients(client_ids, fields):
    url, db, username, password = get_odoo_settings()
    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    fields.append('parent_id')
    comercial_clients = models.execute_kw(db, uid, password,
            'res.partner', 'search_read',
            [[['parent_id', 'in', client_ids], ['type', '=', 'invoice']]],
            {'fields': fields}
        )

    return comercial_clients


def put_client(client_id, data):
    return requests.put("{0}{1}/{2}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id),
                        data=data.update(CONTEXT))


def get_contracts():
    return requests.get("{0}{1}".format(Odoo.CONTEXT.get('HOST', ''), Odoo.CONTRACTS))


def set_contract(client_id, data):
    return requests.put("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.CONTRACTS),
                        data=data.update(CONTEXT))


def get_discounts():
    return requests.get("{0}{1}".format(Odoo.BASE_URL, Odoo.DISCOUNTS), data=CONTEXT)


def set_discount(client_id, data):
    return requests.put("{0}{1}/{2}/{3}".format(Odoo.BASE_URL, Odoo.CLIENTS, client_id, Odoo.DISCOUNTS),
                        data=data.update(CONTEXT))


def get_odoo_settings():
    return [
        Odoo.CONTEXT['host'],
        Odoo.CONTEXT['db'],
        Odoo.CONTEXT['username'],
        Odoo.CONTEXT['password'],
    ]


def get_allowed_invoice_journals():
    return settings.ODOO_SETTINGS['ALLOWED_INVOICE_JOURNALS']


def get_allowed_payment_journals():
    return settings.ODOO_SETTINGS['ALLOWED_PAYMENT_JOURNALS']


def get_account_statement(clients, code):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)

    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    transactions_by_client = models.execute_kw(db, uid, password,
            'edoo.api.integration', 'get_account_statement',
                [{
                    'clients': clients,
                    'code': code,
                    'company_id': Odoo.CUSTOM_SETTINGS['company_pk']
                }]
        )

    return transactions_by_client


def search_clients(query):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    company_id = Odoo.CUSTOM_SETTINGS['company_pk']

    partners = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'search_clients', [{ 'word': query, 'company_id': company_id }]
    )

    for partner in partners:
        partner.update({
            'display_as': 'user',
            'role': 'Cliente registrado',
            'profile_picture': Odoo.DEFAULT_AVATAR,
        })
    
    return partners


def register_client(
        student_client_id=False,
        student_profile=None,
        student_tutors=[],
        client_id=False,
        client_name='',
        client_ref=False,
        comercial_id=False,
        comercial_address='',
        comercial_number='',
        comercial_name='',
        comercial_email=''):
    """
    client_id: family id, odoo contact top level
    student_client_id: student id, odoo contact child level
    comercial_id: family comercial id, odoo contact child level
    """
    url, db, username, password = get_odoo_settings()

    student_client_id = student_client_id or False
    client_id = client_id or False
    comercial_id = comercial_id or False

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    company_id = Odoo.CUSTOM_SETTINGS['company_pk']

    family_code = client_ref or False

    data = {
        'company_id': company_id,
        'family': {
            'id': client_id,
            'emails': [tutor.user.email for tutor in student_tutors],
            'company_id': company_id,
            'name': client_name.encode('utf-8'),
            'ref': family_code
        },

        'commercial_contact': {
            'id': comercial_id,
            'address': comercial_address.encode('utf-8'),
            'vat': comercial_number,
            'name': comercial_name.encode('utf-8'),
            'email': comercial_email,
            'parent_id': client_id,
            'type': 'invoice',
            'company_id': company_id
        },

        'student': {
            'id': student_client_id,
            'ref': student_profile.code,
            'name': student_profile.user.formal_name.encode('utf-8'),
            'name': '{}, {}'.format(
                student_profile.user.last_name.encode('utf-8'),
                student_profile.user.first_name.encode('utf-8')
            ),
            'email': student_profile.user.email,
            'parent_id': client_id,
            'company_id': company_id,
            'level_id': student_profile.level.pk if student_profile.level else False
        }
    }

    res = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'register_client', [data]
    )

    if 'errors' in res:
        return (
            None,
            None,
            None,
            res.get('errors')
        )

    return (
        res.get('client_id'),
        res.get('payment_responsable_client_id'),
        res.get('student_ref'),
        None
    )


def get_payment_responsable_data(family_id):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    result = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'get_payment_responsable_data', [{
            'parent_id': family_id,
            'company_id': Odoo.CUSTOM_SETTINGS['company_pk']
        }]
    )

    role = result.get('errors') and 'Sin Cliente' or 'Cliente registrado'

    result.update({
        'display_as': 'user',
        'role': role,
        'profile_picture': Odoo.DEFAULT_AVATAR
    })

    return result


def update_partner(client_id, data):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    for key, value in data.items():
        if callable(value):
            try:
                data[key] = value(models, db, uid, password)
            except:
                print ('ERROR in key: ', key, 'value:', value)
                continue

    try:
        models.execute_kw(db, uid, password, 'res.partner', 'write', [[client_id], data])
        return True
    except:
        return False


def get_odoo_company():
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    company_id = Odoo.CUSTOM_SETTINGS['company_pk']

    companies = models.execute_kw(
        db, uid, password, 'res.company', 'search_read',
        [
            [
                ['id', '=', company_id]
            ],
        ],
        {'fields': ['id', 'name', 'school_financial_email'], 'limit': 1}
    )

    return len(companies) and companies[0] or None
