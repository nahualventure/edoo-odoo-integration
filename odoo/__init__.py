import .services as services

NAME = 'odoo'

def get_account_statements(code=''):
    return services.get_account_statements(code)


def create_client(data):
    return services.create_client(data)


def call_client(client_id):
    return services.call_client(client_id)

def call_data_clients(client_ids, fields):
    return services.call_data_clients(client_ids, fields)


def update_client(client_id, data):
    return services.update_client(client_id, data)


def call_contracts():
    return services.call_contracts()


def call_discounts():
    return services.call_discounts()


def call_account_statement(clients, code):
    return services.call_account_statement(clients, code)

def call_account_statement_legacy(client_id, comercial_id, data):
    return services.call_account_statement_legacy(client_id, comercial_id, data)

def set_contract(client_id, data):
    return services.set_contract(client_id, data)


def set_discount(client_id, data):
    return services.set_discount(client_id, data)


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
