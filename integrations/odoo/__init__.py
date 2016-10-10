import services


def create_client(data):
    return services.create_client(data=data)


def call_contracts():
    return services.call_contracts()


def call_discounts():
    return services.call_discounts()