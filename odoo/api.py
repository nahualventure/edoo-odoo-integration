# -*- coding: utf-8 -*-

import requests
from django.conf import settings
import xmlrpclib
import time
import services
import json
from pprint import pprint


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
        'password': settings.ODOO_SETTINGS['PASSWORD']
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
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    partner = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'post_client', [{ 'name': data.get('name') }]
    )

    return partner


def get_client(client_id):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

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
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

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
        Odoo.CONTEXT['password']
    ]


def get_allowed_invoice_journals():
    return settings.ODOO_SETTINGS['ALLOWED_INVOICE_JOURNALS']


def get_allowed_payment_journals():
    return settings.ODOO_SETTINGS['ALLOWED_PAYMENT_JOURNALS']

def get_account_statement(clients, filters):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    transactions_by_client = models.execute_kw(db, uid, password,
            'edoo.api.integration', 'get_account_statement',
                [{
                    'clients': clients,
                    'allowed_invoice_journals': get_allowed_invoice_journals(),
                    'allowed_payment_journals': get_allowed_payment_journals(),
                    'filters': filters
                }]
        )

    return transactions_by_client

def get_account_statement_legacy(client_id, comercial_id, filters):
    url, db, username, password = get_odoo_settings()
    comercial_id = int(comercial_id)
    client_id = int(client_id)

    allowed_invoice_journals = get_allowed_invoice_journals()
    allowed_payment_journals = get_allowed_payment_journals()

    uid = services.authenticate_user(url, db, username, password)

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    query_filters = [
        '|',
        ['partner_id', '=', comercial_id],
        ['commercial_partner_id', '=', comercial_id],
        ['journal_id', 'in', allowed_invoice_journals],
        ['state', 'in', ['open','paid']]
    ]

    if ('date_start' in filters):
        # Throw error if date_start does not match format '%Y-%m-%d'
        time.strptime(filters['date_start'], '%Y-%m-%d')

        query_filters.append(['date', '>=', filters['date_start']])

    if ('date_end' in filters):
        # Throw error if date_end does not match format '%Y-%m-%d'
        time.strptime(filters['date_end'], '%Y-%m-%d')

        query_filters.append(['date', '<=', filters['date_end']])

    """
    --------------------------------------------
    Invoices
    --------------------------------------------
    """

    # Get client invoices.
    account_invoices = models.execute_kw(db, uid, password,
        'account.invoice', 'search_read',
        [query_filters],
        {'order': 'company_id, date_invoice'}
    )

    account_invoice_line_ids = []

    transactions_by_company = []
    company_invoices = []
    prev_company_id = None
    prev_company_name = None

    # Get the information that interests us, grouping by company.
    for account_invoice in account_invoices:
        company_id = account_invoice['company_id'][0]
        company_name = account_invoice['company_id'][1]

        if (prev_company_id and prev_company_id != company_id):
            transactions_by_company.append({
                'company_id': prev_company_id,
                'company_name': prev_company_name,
                'invoices': company_invoices,
                'payments': [],
                'balance': 0
            })

            company_invoices = []

        invoice  = {
            'id': account_invoice['id'],
            'number': account_invoice['number'],
            'date_invoice': account_invoice['date_invoice'],
            'date_due': account_invoice['date_due'],
            'amount_total_signed': account_invoice['amount_total_signed'],
            'invoice_line_ids': account_invoice['invoice_line_ids'],
            'reconciled': account_invoice['reconciled'],
            'journal_id': account_invoice['journal_id'],
            'type': account_invoice['type']
        }

        account_invoice_line_ids.extend(account_invoice['invoice_line_ids'])

        company_invoices.append(invoice)
        prev_company_id = company_id
        prev_company_name = company_name

    # The algorithm of the previous loop does not add the last company_invoices.
    # Add it if the loop was entered.
    if prev_company_id:
        transactions_by_company.append({
            'company_id': prev_company_id,
            'company_name': prev_company_name,
            'invoices': company_invoices,
            'payments': [],
            'balance': 0
        })

    # Get the details of the invoices to get the descriptions.
    account_invoice_lines = models.execute_kw(db, uid, password,
        'account.invoice.line', 'search_read',
        [[['id', 'in', account_invoice_line_ids]]]
    )

    invoice_line_indexed = {}
    for account_invoice_line in account_invoice_lines:
        invoice_line_indexed[account_invoice_line['id']] = {
            'display_name': account_invoice_line['display_name'],
            'x_price_included': account_invoice_line['x_price_included']
        }

    # Include descriptions.
    for company_data in transactions_by_company:
        for invoice in company_data['invoices']:
            invoice['invoice_lines'] = map(
                lambda x: {
                    'id': x,
                    'display_name': invoice_line_indexed[x]['display_name'],
                    'x_price_included': invoice_line_indexed[x]['x_price_included']
                },
                invoice['invoice_line_ids']
            )

            # This key will no longer serve us.
            invoice.pop('invoice_line_ids')

    query_filters = [
        ['partner_id', '=', client_id],
        ['journal_id', 'in', allowed_payment_journals]
    ]

    if ('date_start' in filters):
        # Throw error if date_start does not match format '%Y-%m-%d'
        time.strptime(filters['date_start'], '%Y-%m-%d')

        query_filters.append(['payment_date', '>=', filters['date_start']])

    if ('date_end' in filters):
        # Throw error if date_end does not match format '%Y-%m-%d'
        time.strptime(filters['date_end'], '%Y-%m-%d')

        query_filters.append(['payment_date', '<=', filters['date_end']])


    """
    --------------------------------------------
    Payments
    --------------------------------------------
    """
    # Get client payments.
    account_payments = models.execute_kw(db, uid, password,
        'account.payment', 'search_read',
        [query_filters],
        {'order': 'company_id, payment_date'}
    )

    company_payments = [];
    prev_company_id = None
    prev_company_name = None

    # Get the information that interests us, grouping by company.
    for account_payment in account_payments:
        company_id = account_payment['company_id'][0]
        company_name = account_payment['company_id'][1]

        if (prev_company_id and prev_company_id != company_id):
            # Add payment info to the respective company.
            for company_data in transactions_by_company:
                if (company_data['company_id'] == company_id):
                    company_data['payments'] = company_payments
                    break

            company_payments = []

        payment = {
            'id': account_payment['id'],
            'display_name': account_payment['display_name'],
            'payment_date': account_payment['payment_date'],
            'amount': account_payment['amount'],
            'state': account_payment['state'],
            'journal_id': account_payment['journal_id'],
            'payment_type': account_payment['payment_type']
        }

        company_payments.append(payment)
        prev_company_id = company_id
        prev_company_name = company_name

    # The algorithm of the previous loop does not add the last company_payments.
    # Add it if the loop was entered.

    if prev_company_id:
        # Add payment info to the respective company.
        for company_data in transactions_by_company:
            if (company_data['company_id'] == prev_company_id):
                company_data['payments'] = company_payments
                break

    """
    --------------------------------------------
    Balance calc for each company
    --------------------------------------------
    """

    account_acount_ids = models.execute_kw(db, uid, password,
        'account.account', 'search',
        [[['internal_type', '=', 'receivable']]]
    )

    # Get invoice lines.
    account_move_lines = models.execute_kw(db, uid, password,
        'account.move.line', 'search_read',
        [[
            ['partner_id', '=', client_id],
            ['date', '<', filters['date_start']],
            ['account_id', 'in', account_acount_ids]
        ]],
        {'order': 'company_id'}
    )

    prev_company_id = None
    current_balance = 0

    for account_move_line in account_move_lines:
        company_id = account_move_line['company_id'][0]

        if (prev_company_id and prev_company_id != company_id):
            # Add balance to the respective company.
            for company_data in transactions_by_company:
                if (company_data['company_id'] == company_id):
                    company_data['balance'] = current_balance
                    break

            current_balance = 0

        current_balance += account_move_line['balance']
        prev_company_id = company_id


    if prev_company_id:
        # Add balance to the respective company.
        for company_data in transactions_by_company:
            if (company_data['company_id'] == prev_company_id):
                company_data['balance'] = current_balance
                break


    return transactions_by_company

def search_clients(query):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    partners = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'search_clients', [{ 'word': query }]
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
        client_ref='',
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
    student_client_id = student_client_id or False
    client_id = client_id or False
    comercial_id = comercial_id or False

    url, db, username, password = get_odoo_settings()
    uid = services.authenticate_user(url, db, username, password)
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    company_id = Odoo.CUSTOM_SETTINGS['company_pk']

    instance_prefix = Odoo.CUSTOM_SETTINGS['instance_prefix']
    family_code_prefix = Odoo.CUSTOM_SETTINGS['family_code_prefix']
    comercial_code_sufix = Odoo.CUSTOM_SETTINGS['comercial_code_sufix']

    family_code = instance_prefix + family_code_prefix + client_ref
    comercial_code = instance_prefix + family_code_prefix + client_ref + comercial_code_sufix

    res = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'register_client', [{
            'family': {
                'id': client_id,
                'emails': [tutor.user.email for tutor in student_tutors],
                'company_id': company_id,
                'name': client_name.encode('utf-8'),
                'ref': family_code
            },

            'commercial_contact': {
                'id': comercial_id,
                'ref': comercial_code,
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
                'ref': '{}{}'.format(instance_prefix, student_profile.code),
                'name': '{} {}'.format(
                    student_profile.user.first_name.encode('utf-8'),
                    student_profile.user.last_name.encode('utf-8')
                ),
                'email': student_profile.user.email,
                'parent_id': client_id,
                'company_id': company_id
            }
        }]
    )

    return (
        res.get('client_id'),
        res.get('payment_responsable_client_id'),
        res.get('payment_responsable_comercial_id')
    )

def get_payment_responsable_data(family_id):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    result = models.execute_kw(
        db, uid, password, 'edoo.api.integration',
        'get_payment_responsable_data', [{ 'parent_id': family_id }]
    )

    result.update({
        'display_as': 'user',
        'role': 'Cliente registrado',
        'profile_picture': Odoo.DEFAULT_AVATAR
    })

    return result
