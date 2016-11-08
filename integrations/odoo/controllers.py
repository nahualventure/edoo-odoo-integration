# -*- coding: utf-8 -*-

import json
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext as _

from userprofiles.models import (
    StudentTutorRelationship,
    TutorProfile,
    StudentProfile)

from utils.controllers import ControllerResponse
from utils import services as utilities

from integrations.models import get_integration_id

import services
from forms import ContractForm

"""
Business logic for the odoo module integration
"""

__version__ = '0.1.0'
__author__ = 'Oscar Gil <info@edoo.io>'
__date__ = '23 September 2016'
__copyright__ = 'Copyright (c) 2012-2016 Samuel Chávez'
__license__ = 'THE LICENSE'
__status__ = 'development'
__docformat__ = 'reStructuredText'

User = get_user_model()


def get_contract(request, username):

    # Get the user data and response
    user = User.objects.get(username=username)

    # Student profile
    student_profile = user.studentprofile

    # Get the student tutors
    student_tutors = [relationship.tutor
                      for relationship
                      in StudentTutorRelationship.objects.filter(student_profile=student_profile)]

    # Build response
    response = ControllerResponse(request, _(u"Mensaje de respuesta por defecto"))

    success, contracts_data = services.call_contracts()

    try:
        contracts = contracts_data['results']

        # Random default contract
        default_contract = contracts.keys()[0]
        products = contracts[default_contract]['products']

        # Set default_contract
        for pk, val in contracts.items():
            if val[u'default']:
                default_contract = pk
                products = val['products']

        contract_initial = {
            'contract_id': default_contract
        }

        if len(student_tutors) > 0:
            # Get integration object
            # client_id = get_integration_id(student_tutors[0].user)
            client_id = '47'
            success, client_info = services.call_client(client_id)

            for hash_key, tag in [
                    ('name', 'invoice_name'),
                    ('nit', 'invoice_identifier'),
                    ('phone', 'invoice_phone'),
                    ('address', 'invoice_address')]:
                contract_initial[hash_key] = client_info[tag] if tag in client_info else ''

        contract_form = ContractForm(
            initial=contract_initial,
            contract=((contract, contracts[contract]['name']) for contract in contracts.keys()),
            parents=((tutor.user.username, tutor.user.formal_name) for tutor in student_tutors)
        )

        response.sets({
            'user': user,
            'student_profile': student_profile,
            'contracts_json': json.dumps(contracts),
            'contracts': contracts,
            'products': products,
            'contract_form': contract_form,
            'student_tutors': student_tutors
        })
    except KeyError:

        contract_form = ContractForm(
            parents=((tutor.user.username, tutor.user.formal_name) for tutor in student_tutors)
        )

        response.sets({
            'user': user,
            'student_profile': student_profile,
            'contract_form': contract_form,
            'student_tutors': student_tutors
        })

    return response


def tutor_invoice(request):

    username = request.GET.get('username', None)

    user = User.objects.get(username=username)
    client_id = get_integration_id(user)


    client_id = "48"
    success, response = services.call_client(client_id)

    print (response)

    return JsonResponse(response)


def set_contract(request, username, request_data, redirect_url=None):
    """ Student registration manager. """

    # Validate permission
    request.user.can(
        'userprofiles.add_studentprofile',
        raise_exception=True)

    # Build redirect response
    redirect_response = HttpResponseRedirect(request.META['HTTP_REFERER'])
    if redirect_url:
        redirect_response = HttpResponseRedirect(redirect_url)

    # Retrieve from HTTP
    contract_form = ContractForm(
        data=request_data)

    if contract_form.is_valid():
        contract_id = contract_form.cleaned_data.get('contract_id')
        products = contract_form.cleaned_data.get('products')
        payments_responsible = contract_form.cleaned_data.get('payments_responsible')
        name = contract_form.cleaned_data.get('name')
        nit = contract_form.cleaned_data.get('nit')
        phone = contract_form.cleaned_data.get('phone')
        address = contract_form.cleaned_data.get('address')
        tutors_visibility = contract_form.cleaned_data.get('tutors_visibility')

        # Get users
        user = User.objects.get(username=username)
        tutor = User.objects.get(username=payments_responsible)

        # Get integration object
        # client_id = get_integration_id(user)
        # tutor_client_id = get_integration_id(tutor)

        contract_data = {
            'contract_id': contract_id,
            'products': products
        }

        tutor_client_data = {
            'invoice_identifier': nit,
            'invoice_name': name,
            'invoice_phone': phone,
            'invoice_address': address
        }

        client_data = {
            # 'super_client_id': tutor_client_id
        }

        client_id = '49'
        tutor_client_id = '50'

        u_success, u_response = services.set_contract(client_id, contract_data)

        # t_success, t_response = services.update_client(client_id, client_data)

        c_success, c_response = services.update_client(tutor_client_id, tutor_client_data)

        redirect_response = HttpResponseRedirect(reverse('registration_backend'))

        return ControllerResponse(
            request,
            _(u"Registro completado exitosamente"),
            message_position='default',
            redirect=redirect_response)

    # Else
    response = ControllerResponse(
        request,
        _(u"Se encontraron algunos problemas en el formulario de estudiante"),
        message_position='default',
        redirect=redirect_response)

    # Transport data and errors
    utilities.transport_form_through_session(
        request,
        contract_form,
        'contract_form')

    response.set_error()
    return response
