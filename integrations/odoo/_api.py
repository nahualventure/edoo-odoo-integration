import requests
import json


class Odoo:
    # main URL of API
    BASE_URL = "https://api.github.com"
    CONTRACT = "/contract"
    CLIENT = "/client"
    DISCOUNT = "/discount"
    TEST = "https://api.github.com/orgs/edoo-project/repos"


def post_client(data):
    return requests.post(Odoo.BASE_URL + Odoo.CLIENT, data=json.dumps(data))


def get_contracts():
    return requests.get(Odoo.BASE_URL + Odoo.CONTRACT)


def set_contract(id, data):
    return requests.put(Odoo.BASE_URL + Odoo.CLIENT +
                        "/" + id + Odoo.CONTRACT,
                        data=json.dumps(data))


def get_discounts():
    return requests.get(Odoo.BASE_URL + Odoo.DISCOUNT)


def test_request():
    return requests.get(Odoo.BASE_URL + Odoo.TEST)
