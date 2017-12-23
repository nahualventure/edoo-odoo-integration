# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

import controllers
from utils import services as utilities


@csrf_protect
@require_http_methods(['GET', 'POST'])
def registration(request, student_id):
    """
    Require: GET, POST

    **GET**: renders the contract selection page.
    **POST**: process the form submission.
    """
    if request.method == 'POST':
        cr = controllers.register_student(request, request.POST, student_id)
        utilities.place_message(request, cr)

        if cr.should_redirect():
            return cr.redirect
    elif request.method == 'GET':
        cr = controllers.registration(request, student_id)

    return render(request, 'odoo/registration.html', cr.gets())


@csrf_protect
@require_http_methods(['GET', 'POST'])
def client_edition(request, student_id):
    """
    Require: GET, POST

    **GET**: renders the contract selection page.
    **POST**: process the form submission.
    """
    if request.method == 'POST':
        cr = controllers.register_student(request, request.POST, student_id, edition=True)
        utilities.place_message(request, cr)

        if cr.should_redirect():
            return cr.redirect
    elif request.method == 'GET':
        cr = controllers.registration(request, student_id)

    return render(request, 'odoo/edition.html', cr.gets())


@csrf_protect
@require_http_methods(['GET'])
def tutor_invoice(request):
    """
    Require: GET

    **GET**: returns a JSON with the tutor invoice information.
    """

    cr = controllers.tutor_invoice(request)

    return cr


@csrf_protect
@require_http_methods(['GET'])
def search_clients(request):
    query = request.GET.get('query', "")
    return controllers.search_clients(request, query)
