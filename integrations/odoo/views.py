# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

import controllers
from utils import services as utilities


@csrf_protect
@require_http_methods(['GET', 'POST'])
def get_contract(request, username):
    """
    Require: GET, POST

    **GET**: renders the contract selection page.
    **POST**: process the form submission.
    """

    if request.method == 'GET':
        cr = controllers.get_contract(request, username)

        utilities.place_message(request, cr)

        if cr.should_redirect():
            return cr.redirect

        return render(request, 'backends/contract.html', cr.gets())

    elif request.method == 'POST':
        print ('entra al post')
        cr = controllers.set_contract(request, username, request.POST)

        utilities.place_message(request, cr)

        return cr.redirect


@csrf_protect
@require_http_methods(['GET'])
def tutor_invoice(request):
    """
    Require: GET

    **GET**: returns a JSON with the tutor invoice information.
    """

    cr = controllers.tutor_invoice(request)

    return cr

