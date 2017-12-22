import requests
from django.conf import settings
import xmlrpclib
import time
import services
import json


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
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)

    odoo_client_id = models.execute_kw(db, uid, password,
        'res.partner', 'create',
        [{
            'name': data['name'],
        }]
    )

    odoo_client = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[['id', '=', odoo_client_id]]]
    )

    return odoo_client[0]


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

import time

def search_clients(query):
    url, db, username, password = get_odoo_settings()

    # TODO: xmlshit
    # uid = services.authenticate_user(url, db, username, password)
    # 
    # TODO: transform into the following shape

    return [
        {
            'display_as': 'user',
            'client_id': 1,
            'comercial_id': 1,
            'comercial_name': "Cliente S. A.",
            'comercial_number': "111111111111111111111-1",
            'comercial_address': "Ciudad 1",
            'profile_picture': "http://lh3.googleusercontent.com/-zhYZ2MAkVfQ/AAAAAAAAAAI/AAAAAAAAAAA/RDrrSIIg9Jw/photo.jpg",
            'first_name': "Cliente S. A.",
            'role': "Cliente registrado"
        },
        {
            'display_as': 'user',
            'client_id': 2,
            'billing_id': 2,
            'billing_name': "Cliente 2 S. A.",
            'billing_number': "2222222222222222222222-2",
            'billing_address': "Ciudad 2",
            'profile_picture': "https://i.pinimg.com/736x/4a/84/7c/4a847c6438c10238461a47a45edbeb0c--redhead-funny-redhead-men.jpg",
            'first_name': "Cliente 2 S. A.",
            'role': "Cliente registrado"
        }
    ]

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

def get_account_statement(client_id, comercial_id, filters):
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
        ['journal_id', 'in', allowed_invoice_journals]
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
            'amount_total': account_invoice['amount_total'],
            'invoice_line_ids': account_invoice['invoice_line_ids'],
            'reconciled': account_invoice['reconciled'],
            'journal_id': account_invoice['journal_id']
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
            'price_subtotal': account_invoice_line['price_subtotal']
        }

    # Include descriptions.
    for company_data in transactions_by_company:
        for invoice in company_data['invoices']:
            invoice['invoice_lines'] = map(
                lambda x: {
                    'id': x,
                    'display_name': invoice_line_indexed[x]['display_name'],
                    'price_subtotal': invoice_line_indexed[x]['price_subtotal']
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
            'journal_id': account_payment['journal_id']
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
