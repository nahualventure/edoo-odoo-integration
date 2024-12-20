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


def get_odoo_settings():
    return (
        Odoo.CONTEXT['host'],
        Odoo.CONTEXT['db'],
        Odoo.CONTEXT['username'],
        Odoo.CONTEXT['password'],
    )


def get_account_statement(clients, code):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)

    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    transactions_by_client = models.execute_kw(db, uid, password,
            'edoo.api.integration', 'get_account_statement',
                [{
                    'clients': [int(s) for s in clients or [] if s],
                    'code': code or '',
                    'company_id': int(Odoo.CUSTOM_SETTINGS['company_pk'])
                }]
    )

    return transactions_by_client


def search_clients(query):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    partners = models.execute_kw(db, uid, password,
            'edoo.api.integration', 'search_clients',
                [{
                    'word': query or '',
                    'company_id': int(Odoo.CUSTOM_SETTINGS['company_pk'])
                }]
    )

    for partner in partners:
        partner.update({
            'display_as': 'user',
            'role': 'Cliente registrado',
            'profile_picture': Odoo.DEFAULT_AVATAR,
        })
    
    return partners


def register_client(
        student_client_id,
        student_profile,
        student_tutors,
        client_id,
        client_name,
        client_ref,
        comercial_id,
        comercial_address,
        comercial_number,
        comercial_name,
        comercial_email):
    """
    client_id: family id, odoo contact top level
    student_client_id: student id, odoo contact child level
    comercial_id: family comercial id, odoo contact child level
    """
    url, db, username, password = get_odoo_settings()

    student_client_id = student_client_id or False
    emails = [tutor.user.email or '' for tutor in student_tutors or []]

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    data = {
        'company_id': int(Odoo.CUSTOM_SETTINGS['company_pk']),
        'family': {
            'id': client_id and int(client_id) or 0,
            'emails': emails,
            'name': client_name or '',
            'ref': client_ref or ''
        },

        'commercial_contact': {
            'id': comercial_id and int(comercial_id) or 0,
            'address': comercial_address or '',
            'vat': comercial_number or '',
            'name': comercial_name or '',
            'email': comercial_email or '',
        },

        'student': {
            'id': student_client_id and int(student_client_id) or 0,
            'ref': student_profile.code or '',
            'first_name': student_profile.user.first_name,
            'last_name': student_profile.user.last_name,
            'name': '{}, {}'.format(
                student_profile.user.last_name,
                student_profile.user.first_name
            ),
            'email': student_profile.user.email or '',
            'level_id': student_profile.level and student_profile.level.pk or 0,
            'cycle_id': student_profile.current_cycle and student_profile.current_cycle.pk or 0,
            'section_name': student_profile.main_section
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
            'parent_id': family_id and int(family_id) or 0,
            'company_id': int(Odoo.CUSTOM_SETTINGS['company_pk'])
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


def get_shop_url(client_id):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = ServerProxy('{}/xmlrpc/2/object'.format(url))

    response = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'get_shop_url_with_token', [{'client_id': client_id}]
    )

    return response
