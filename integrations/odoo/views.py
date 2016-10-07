# -*- coding: utf-8 -*-

import time
from integrations import odoo
from django.utils.translation import ugettext_lazy as _

from django import template
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model
from utils import services as utilities
import controllers



"""
Presentation layer for the userprofiles application.

Python module that provides the interface (API) to all the logic regarding to
Edoo user profile management.
"""

__version__ = '0.1.0'
__author__ = 'Oscar Gil <me@samuelchavez.com>'
__date__ = '07 October 2016'
__copyright__ = 'Copyright (c) 2012-2014 Samuel Chávez'
__license__ = 'THE LICENSE'
__status__ = 'development'
__docformat__ = 'reStructuredText'

@csrf_protect
@require_http_methods(['GET'])
def set_contract(request, username):
    """
    Require: GET

    **GET**: renders the contract selection page.
    """

    cr = controllers.set_contract(request, username)

    utilities.place_message(request, cr)

    if cr.should_redirect():
        return cr.redirect

    return render(request, 'set_contract.html', cr.gets())

