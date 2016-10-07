import requests

from .models import Odoo


def get_contracts():
    return requests.get(Odoo.CONTRACT)


def get_discounts():
    return requests.get(Odoo.DISCOUNT)


def test_request():
    return requests.get(Odoo.DISCOUNT)