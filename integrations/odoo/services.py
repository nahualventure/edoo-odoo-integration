import requests

from .models import Odoo
from ._api import (
    get_contracts,
    post_client,
    get_discounts
)


def create_client(data):
    client = post_client(data=data)


def call_contracts():
    contracts = get_contracts()
    return contracts


def call_discounts():
    discounts = get_discounts()