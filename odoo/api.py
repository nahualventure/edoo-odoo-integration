# -*- coding: utf-8 -*-

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

def get_account_statement(client_id, comercial_id, filters):
    url, db, username, password = get_odoo_settings()
    comercial_id = int(comercial_id)
    client_id = int(client_id)

    uid = services.authenticate_user(url, db, username, password)

    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    transactions_by_company = models.execute_kw(db, uid, password,
            'edoo.api.integration', 'get_account_statement',
                [{'comercial_id': comercial_id,
                'client_id': client_id,
                'allowed_invoice_journals': get_allowed_invoice_journals(),
                'allowed_payment_journals': get_allowed_payment_journals(),
                'filters': filters}]
        )

    return transactions_by_company

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

    print query_filters

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

    partners = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[
            '|',
            ['ref', 'ilike', query],
            ['name', 'ilike', query],
            ['child_ids', '!=', False]
        ]]
    )

    partner_ids = list(map(lambda x: int(x['id']), partners))

    comercial_partners = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[['parent_id', 'in', partner_ids], ['type', '=', 'invoice']]]
    )

    result = []

    for partner in partners:
        # Look for comercial partner

        # Logic 1
        cm = next((x for x in comercial_partners if x['parent_id'][0] == partner['id']), None)

        # Logic 2
        # cm = None
        # for comercial_partner in comercial_partners:
        #     if comercial_partner['parent_id'][0] == partner['id']:
        #         cm = comercial_partner
        #         break

        addresses = [cm['street'], cm['street2'], cm['city']] if cm else []

        client_object = {
            'display_as': 'user',
            'client_id': partner['id'],
            'client_name': partner['name'],
            'client_ref': partner['ref'],
            'comercial_id': cm['id'] if cm else None,
            'comercial_name': cm['name'] if cm else None,
            'comercial_number': cm['vat'] if (cm and cm['vat']) else None,
            'comercial_address': " ".join(address for address in addresses if address),
            'comercial_email': cm['email'] if (cm and cm['email']) else None,
            'profile_picture': Odoo.DEFAULT_AVATAR,
            'first_name': partner['name'],
            'role': "Cliente registrado"
        }

        result.append(client_object)

    return result


def register_client(
        student_client_id='',
        student_profile=None,
        student_tutors=[],
        client_id='',
        client_name='',
        client_ref='',
        comercial_id='',
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

    uid = services.authenticate_user(url, db, username, password)
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    # Setup codes
    instance_prefix = Odoo.CUSTOM_SETTINGS['instance_prefix']
    family_code_prefix = Odoo.CUSTOM_SETTINGS['family_code_prefix']
    comercial_code_sufix = Odoo.CUSTOM_SETTINGS['comercial_code_sufix']

    family_code = instance_prefix + family_code_prefix + client_ref
    family_name = client_name
    comercial_code = instance_prefix + family_code_prefix + client_ref + comercial_code_sufix

    tutors_emails = map(lambda x: x.user.email, student_tutors) if student_tutors else []

    # Fallback for None type
    student_profile.user.first_name = student_profile.user.first_name or ''
    student_profile.user.last_name = student_profile.user.last_name or ''

    # -------- Family contact --------

    # Update family contact
    if client_id:
        family_id = client_id
        models.execute_kw(db, uid, password, 'res.partner', 'write', [
            [family_id],
            {
                'email': ",".join(tutors_emails)
            }
        ])
    # Create family contact
    else:
        family_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
            'ref': family_code.encode('utf-8'),
            'name': family_name.encode('utf-8'),
            'email': ",".join(tutors_emails),
            'company_id': Odoo.CUSTOM_SETTINGS['company_pk']
        }])

    # -------- Family comercial contact --------

    # Update family comercial contact
    if comercial_id:
        family_comercial_id = comercial_id
        models.execute_kw(db, uid, password, 'res.partner', 'write', [
            [family_comercial_id],
            {
                'street': comercial_address.encode('utf-8'),
                'vat': comercial_number,
                'name': comercial_name.encode('utf-8'),
                'email': comercial_email,
                'parent_id': family_id,
                'type': 'invoice'
            }
        ])
    # Create family comercial contact
    else:
        family_comercial_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
            'ref': comercial_code,
            'street': comercial_address.encode('utf-8'),
            'vat': comercial_number,
            'name': comercial_name.encode('utf-8'),
            'email': comercial_email,
            'parent_id': family_id,
            'type': 'invoice',
            'company_id': Odoo.CUSTOM_SETTINGS['company_pk']
        }])

    # Update 'vat' separately because it is not set during creation.
    # TODO: Fix this issue in Odoo.
    models.execute_kw(db, uid, password, 'res.partner', 'write', [
        [family_comercial_id],
        { 'vat': comercial_number }
    ])

    # -------- Student contact --------

    # Reasign family if student_client_id exists
    if student_client_id:
        student_id = student_client_id
        student = models.execute_kw(db, uid, password,
            'res.partner', 'search_read',
            [[['id', '=', student_id]]],
            {'limit': 1}
        )

        if len(student) != 1:
            raise Exception('No client found for id ' + str(student_id))

        student = student[0]

        # Check if family has changed for the student
        if student['parent_id'][0] != family_id:
            # Get family partner because we need its current 'ref'.
            old_family = models.execute_kw(db, uid, password,
                'res.partner', 'search_read',
                [[['id', '=', student['parent_id'][0]]]],
                {'limit': 1, 'fields': ['ref']}
            )
            old_family = old_family[0]

            # Get family comercial partner because we need its current 'ref'.
            old_comercial_partner = models.execute_kw(db, uid, password,
                'res.partner', 'search_read',
                [[['parent_id', '=', old_family['id']], ['type', '=', 'invoice']]],
                {'limit': 1, 'fields': ['ref']}
            )

            if len(old_comercial_partner) != 1:
                raise Exception('No comercial partner found for client ' + str(old_family['id']))

            old_comercial_partner = old_comercial_partner[0]

            # If student_id was used, it will have associated invoices
            invoice_count = models.execute_kw(db, uid, password,
                'account.invoice', 'search_count',
                [[['partner_shipping_id', '=', student_id], ['state', 'in', ['open','paid']]]]
            )

            # Archive student
            if invoice_count:
                models.execute_kw(db, uid, password, 'res.partner', 'write', [
                    [student_id],
                    {
                        'ref': (student['ref'] or '') + 'INACTIVE',
                        'active': False
                    }
                ])
            # Unlink student
            else:
                models.execute_kw(db, uid, password, 'res.partner', 'unlink', [
                    [student_id]
                ])

            family_students_count = models.execute_kw(db, uid, password,
                'res.partner', 'search_count',
                [[['parent_id', '=', old_family['id']], ['type', '=', 'contact']]]
            )

            # Family doesn't have more students
            if not family_students_count:
                account_move_lines_count = models.execute_kw(db, uid, password,
                    'account.move.line', 'search_count',
                    [[['partner_id', '=', old_family['id']]]]
                )

                # Archive family and comercial partner
                if account_move_lines_count:
                    # Disable family partner
                    models.execute_kw(db, uid, password, 'res.partner', 'write', [
                        [old_family['id']],
                        {
                            'ref': (old_family['ref'] or '') + 'INACTIVE',
                            'active': False
                        }
                    ])

                    # Disable family comercial partner
                    models.execute_kw(db, uid, password, 'res.partner', 'write', [
                        [old_comercial_partner['id']],
                        {
                            'ref': (old_comercial_partner['ref'] or '') + 'INACTIVE',
                            'active': False
                        }
                    ])
                # Unlink family and comercial partner
                else:
                    models.execute_kw(db, uid, password, 'res.partner', 'unlink', [
                        [old_family['id'], old_comercial_partner['id']]
                    ])

            # Create new student with new family
            student_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
                'ref': instance_prefix + student_profile.code,
                'name': '{0}, {1}'.format(
                    student_profile.user.first_name.encode('utf-8'),
                    student_profile.user.last_name.encode('utf-8')
                ),
                'email': student_profile.user.email,
                'parent_id': family_id,
                'company_id': Odoo.CUSTOM_SETTINGS['company_pk']
            }])
        # Update student contact
        else:
            models.execute_kw(db, uid, password, 'res.partner', 'write', [
                [student_id],
                {
                    'ref': student_profile.code,
                    'name': '{0}, {1}'.format(
                        student_profile.user.first_name.encode('utf-8'),
                        student_profile.user.last_name.encode('utf-8')
                    ),
                    'email': student_profile.user.email
                }
            ])
    # Create student contact
    else:
        student_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
            'ref': instance_prefix + student_profile.code,
            'name': '{0}, {1}'.format(
                student_profile.user.first_name.encode('utf-8'),
                student_profile.user.last_name.encode('utf-8')
            ),
            'email': student_profile.user.email,
            'parent_id': family_id,
            'company_id': Odoo.CUSTOM_SETTINGS['company_pk']
        }])


    # Response
    client_id = student_id
    payment_responsable_client_id = family_id
    payment_responsable_comercial_id = family_comercial_id

    return (
        client_id,
        payment_responsable_client_id,
        payment_responsable_comercial_id
    )


def get_payment_responsable_data(client_id):
    url, db, username, password = get_odoo_settings()

    uid = services.authenticate_user(url, db, username, password)
    models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

    partner = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[['id', '=', client_id]]],
        {'limit': 1}
    )

    if len(partner) != 1:
        raise Exception('No client found for id ' + str(client_id))

    partner = partner[0]

    comercial_partners = models.execute_kw(db, uid, password,
        'res.partner', 'search_read',
        [[['parent_id', '=', partner['id']], ['type', '=', 'invoice']]]
    )

    # A client must have one comercial partner
    if len(comercial_partners) == 0:
        raise Exception('No comercial partner found for client ' + str(client_id))
    elif len(comercial_partners) > 1:
        raise Exception('More than one comercial partner found for client ' + str(client_id))

    comercial_partner = comercial_partners[0]

    addresses = [
        comercial_partner['street'],
        comercial_partner['street2'],
        comercial_partner['city']
    ]

    payment_responsable_client_id = client_id
    payment_responsable_comercial_id = comercial_partner['id']
    payment_responsable_comercial_name = comercial_partner['name']
    payment_responsable_comercial_number = comercial_partner['vat'] or ''
    payment_responsable_comercial_address = " ".join(address for address in addresses if address)
    payment_responsable_comercial_email = comercial_partner['email'] or ''

    return {
        'display_as': 'user',
        'client_id': payment_responsable_client_id,
        'client_name': partner['name'],
        'client_ref': partner['ref'],
        'comercial_id': payment_responsable_comercial_id,
        'comercial_name': payment_responsable_comercial_name,
        'comercial_number': payment_responsable_comercial_number,
        'comercial_address': payment_responsable_comercial_address,
        'comercial_email': payment_responsable_comercial_email,
        'profile_picture': Odoo.DEFAULT_AVATAR,
        'first_name': partner['name'],
        'role': "Cliente registrado"
    }
