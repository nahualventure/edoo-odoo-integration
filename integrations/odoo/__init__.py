import _services


def create_client(data):
    return _services.create_client(data=data)


def call_contracts():
    return _services.call_contracts()


def call_discounts():
    return _services.call_discounts()