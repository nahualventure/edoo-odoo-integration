import services

NAME = 'odoo'


def create_client(data):
    return services.create_client(data)


def call_client(client_id):
    return services.call_client(client_id)


def update_client(client_id, data):
    return services.update_client(client_id, data)


def call_contracts():
    return services.call_contracts()


def call_discounts():
    return services.call_discounts()


def call_account_statement(client_id, data):
    return services.call_account_statement(client_id, data)


def set_contract(client_id, data):
    return services.set_contract(client_id, data)


def set_discount(client_id, data):
    return services.set_discount(client_id, data)

