# -*- coding: utf-8 -*-

import requests
try:
    from . import api
except ImportError:
    import api

from django.conf import settings
try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy
from datetime import datetime

class OdooAuthentication(object):
    __instance = None

    uid = host = database = username = password = None

    def __init__(self, host, database, username, password):
        self.host = host
        self.database = database
        self.username = username
        self.password = password

    def __new__(args, host, database, username, password):
        if OdooAuthentication.__instance is None:
            try:
                common = ServerProxy('{}/xmlrpc/2/common'.format(host))
                OdooAuthentication.uid = common.authenticate(database, username, password, {})
                OdooAuthentication.__instance = object.__new__(args)
            except Exception as e:
                raise e
        return OdooAuthentication.__instance


def get_account_statements(name=''):
    from integrations.models import Integration, IntegrationConfig
    from django.db.models.expressions import RawSQL

    return IntegrationConfig.objects.filter(
        key__contains='account_statement_{}'.format(name), integration__key='odoo'
    ).order_by(RawSQL("data->>%s", ("ordinal",)))


def portal_url(client_id):
    try:
        return api.get_portal_url(client_id)
    except requests.RequestException:
        print ("Error en el request")
        return None


def call_account_statement(clients, code):
    try:
        response = api.get_account_statement(clients, code)
        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


def get_odoo_company():
    try:
        return api.get_odoo_company()
    except:
        return None


def authenticate_user(host, database, username, password):
    try:
        auth = OdooAuthentication(host, database, username, password)
        return auth.uid
    except Exception as e:
        raise e


def search_clients(query):
    try:
        return api.search_clients(query)
    except requests.RequestException:
        print ("Error en el request")
        return None


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
    try:
        return api.register_client(
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
            comercial_email
        )
    except requests.RequestException:
        return (None, None, None, None)


def update_partner(client_id, data):
    return api.update_partner(client_id, data)


def get_payment_responsable_data(client_id):
    try:
        return api.get_payment_responsable_data(client_id)
    except requests.RequestException:
        print ("Error en el request")
        return None


odoo_versions_updated = [
    '10.0',
    '12.0',
]


def _validate_version(version):
    return version in odoo_versions_updated
