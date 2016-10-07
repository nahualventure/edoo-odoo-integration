import requests

from .models import Odoo
from .api import get_contracts


def call_contracts():
    user_contracts = get_contracts()
