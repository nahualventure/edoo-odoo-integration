from . import services

NAME = 'odoo'


def shop_url(client_id):
    return services.shop_url(client_id)


def get_account_statements(code=''):
    return services.get_account_statements(code)


def call_account_statement(clients, code):
    return services.call_account_statement(clients, code)


def search_clients(query):
    return services.search_clients(query)


def get_payment_responsable_data(client_id):
    return services.get_payment_responsable_data(client_id)


def update_partner(client_id, data):
    return services.update_partner(client_id, data)


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
    return services.register_client(
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


def get_odoo_company():
    return services.get_odoo_company()
