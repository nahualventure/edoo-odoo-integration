# -*- coding: utf-8 -*-

import requests
from . import api
from django.conf import settings
from xmlrpclib import ServerProxy
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
        key__contains='account_statement_'.format(name), integration__key='odoo'
    ).order_by(RawSQL("data->>%s", ("ordinal",)))


def create_client(data):
    try:
        response = api.post_client(data)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


def call_client(client_id):
    try:
        response = api.get_client(client_id)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None

def call_data_clients(client_ids, fields):
    try:
        response = api.get_data_clients(client_ids, fields)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


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


def parse_account_statement_data(clients):
    account_statement_by_student = []

    for odoo_client in clients:
        # Prepare data for template.
        company_transactions = []
        transactions_by_company = odoo_client['transactions_by_company']
        for company_data in transactions_by_company:
            # Merge invoices and payments getting the respective info.
            insolvent_company = False
            for invoice in company_data.get('invoices', []):
                invoice_description = invoice['number']

                if (invoice['type'] == 'out_refund'):
                    invoice_description += ' - Devolución'

                insolvent_transaction = False
                if invoice['state'] == 'open' and datetime.now().strftime("%Y-%m-%d %H:%M:%S") > invoice['date_due']:
                    insolvent_transaction = True
                    insolvent_company = True

                trans = {
                    'code': invoice['id'],
                    'description': invoice_description,
                    'date': invoice['date_invoice'],
                    'expired': invoice['insolvent'] or False,
                    'date_due': invoice['date_due'],
                    'payment_method': invoice['journal_id'][1],
                    'amount': invoice['amount_total_signed'],
                    'details': invoice['invoice_lines'],
                    'reconciled': invoice['reconciled'],
                    'state': invoice['state'],
                    'insolvent_transaction': insolvent_transaction,
                    'payment_used': 0,
                    'balance_paid':  0
                }
                if invoice['balance_paid']:
                    trans['balance_paid'] = invoice['balance_paid'] * -1 if invoice['amount_total_signed'] > 0 else invoice['balance_paid']
                company_transactions.append(trans)

            # company_data['insolvent_company'] = insolvent_company or company_data['balance'] > 0.0
            company_data['insolvent_company'] = insolvent_company

            # It multiplies by -1 because they subtract the salary.
            for payment in company_data.get('payments', []):
                payment_description = payment['display_name']

                if (payment['payment_type'] == 'outbound'):
                    payment['amount'] *= -1
                    payment_description += ' - Reintegro'

                new_payment = {
                    'code': payment['id'],
                    'description': payment_description,
                    'date': payment['payment_date'],
                    'expired': False,
                    'date_due': '',
                    'payment_method': payment['journal_id'][1],
                    'amount': payment['amount'] * -1,
                    'details': None,
                    'reconciled': True if (payment['state'] == 'reconciled') else False,
                    'payment_used': payment['payment_used'] or 0,
                    'balance_paid': 0,
                    'state': payment['state']
                }
                company_transactions.append(new_payment)

            # Sort transactions by date
            company_transactions = sorted(
                company_transactions,
                key=lambda transaction: transaction['date']
            )

            # Calc balance and format dates.
            balance = company_data['balance']
            for transaction in company_transactions:
                date = datetime.strptime(transaction['date'], '%Y-%m-%d')
                transaction['date'] = date.strftime("%d/%m/%y")

                if transaction['date_due']:
                    date_due = datetime.strptime(transaction['date_due'], '%Y-%m-%d')
                    transaction['date_due'] = date_due.strftime("%d/%m/%y")

                transaction['balance'] = balance = balance + transaction['amount'] + transaction['payment_used'] + transaction['balance_paid']

            company_data['transactions'] = company_transactions

            # Free memory
            try:
                company_data.pop('invoices')
                company_data.pop('payments')
            except:
                pass

            # Clear this variable for the next company.
            company_transactions = []

        account_statement_by_student.append({
            'transactions_by_company': transactions_by_company,
            'client_info': {
                'invoice_identifier': odoo_client['vat'],
                'invoice_phone': odoo_client['phone'],
                'name': odoo_client['name'],
                'email': odoo_client['email'],
                'client_id': odoo_client['client_id']
            }
        })

    return account_statement_by_student


def call_account_statement(clients, code):
    try:
        response = api.get_account_statement(clients, code)
        all_data = {
            'data': parse_account_statement_data(response.get('data', [])),
            'configs': response.get('configs', {})
        }

        return all_data
    except requests.RequestException:
        print ("Error en el request")
        return None

def call_account_statement_legacy(client_id, comercial_id, data):
    try:
        response = api.get_account_statement_legacy(client_id, comercial_id, data)

        return response
    except requests.RequestException:
        print ("Error en el request")
        return None


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
