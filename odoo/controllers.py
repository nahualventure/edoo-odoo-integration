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
from integrations.services import get_integration_id

import services
from forms import (
    ContractForm,
    TutorPermissionsFormset,
    PaymentResponsableConfigurationForm
)
from integrations.services import (
    set_integration_configuration,
    get_integration_configuration
)

from userprofiles.models import StudentProfile

import utils.services as utilities

'''
integration configurations keys:

client_id
payment_responsable_client_id
payment_responsable_comercial_id
allow_view_account_statement
allow_view_voucher


'''


def registration(request, student_id):

    # Get the student profile
    student_profile = StudentProfile.objects.get(id=student_id)

    # Get the student tutors
    relationships = StudentTutorRelationship.objects.filter(student_profile=student_profile)
    student_tutors = [relationship.tutor for relationship in relationships]

    response = ControllerResponse(request, _(u"Mensaje de respuesta por defecto"))

    # Initial data
    student_client_id = get_integration_configuration(
        integration_key='odoo',
        object_instance=student_profile,
        key='client_id',
        default=False
    )

    payment_responsable_client_id = get_integration_configuration(
        integration_key='odoo',
        object_instance=student_profile,
        key='payment_responsable_client_id',
        default=False
    )

    payment_configuration_form = PaymentResponsableConfigurationForm()
    res_data = None
    if payment_responsable_client_id != False:
        res_data = services.get_payment_responsable_data(payment_responsable_client_id)
        payment_configuration_form = PaymentResponsableConfigurationForm(initial={
            'student_client_id': student_client_id,
            'client_id': res_data['client_id'],
            'comercial_id': res_data['comercial_id'],
            'comercial_name': res_data['comercial_name'],
            'comercial_number': res_data['comercial_number'],
            'comercial_address': res_data['comercial_address']
        })

    permissions_formset = TutorPermissionsFormset(initial=[
        {
            'tutor': relationaship.tutor,
            'allow_view_account_statement': get_integration_configuration(
                integration_key='odoo',
                object_instance=relationship,
                key='allow_view_account_statement',
                default=True
            ),
            'allow_view_voucher': get_integration_configuration(
                integration_key='odoo',
                object_instance=relationship,
                key='allow_view_voucher',
                default=True
            )
        }
        for relationaship in relationships
    ], )

    response.sets({
        'student_profile': student_profile,
        'student_tutors': student_tutors,
        'payment_configuration_form': payment_configuration_form,
        'permissions_formset': permissions_formset,
        'prefilled_result': res_data,
        'studentprofile': student_profile,
        'user': student_profile.user,
        'current_view': 'odoo'
    })

    return response


def register_student(request, request_data, student_id, edition=False):
    # Get the student profile
    student_profile = StudentProfile.objects.get(id=student_id)

    # Get the student tutors
    relationships = StudentTutorRelationship.objects.filter(student_profile=student_profile)
    student_tutors = [relationship.tutor for relationship in relationships]

    response = ControllerResponse(request, _(u"Mensaje de respuesta por defecto"))

    payment_configuration_form = PaymentResponsableConfigurationForm(request_data)
    permissions_formset = TutorPermissionsFormset(request_data)

    if payment_configuration_form.is_valid() and permissions_formset.is_valid():

        # Billing data
        student_client_id = payment_configuration_form.cleaned_data.get('student_client_id', None)
        comercial_id = payment_configuration_form.cleaned_data.get('comercial_id', None)
        comercial_address = payment_configuration_form.cleaned_data.get('comercial_address')
        comercial_number = payment_configuration_form.cleaned_data.get('comercial_number')
        client_id = payment_configuration_form.cleaned_data.get('client_id', None)
        comercial_name = payment_configuration_form.cleaned_data.get('comercial_name')
        comercial_email = payment_configuration_form.cleaned_data.get('comercial_email')

        # Register client service consumption
        (
            client_id,
            payment_responsable_client_id,
            payment_responsable_comercial_id
        ) = services.register_client(
            student_client_id,
            student_profile,
            student_tutors,
            client_id,
            comercial_id,
            comercial_address,
            comercial_number,
            comercial_name,
            comercial_email
        )

        set_integration_configuration(
            integration_key='odoo',
            object_instance=student_profile,
            key='client_id',
            value='{}'.format(client_id)
        )

        set_integration_configuration(
            integration_key='odoo',
            object_instance=student_profile,
            key='payment_responsable_client_id',
            value='{}'.format(payment_responsable_client_id)
        )

        set_integration_configuration(
            integration_key='odoo',
            object_instance=student_profile,
            key='payment_responsable_comercial_id',
            value='{}'.format(payment_responsable_comercial_id)
        )

        # Save configuration for each tutor
        for tutor_configuration in permissions_formset.cleaned_data:
            tutor = tutor_configuration['tutor']
            allow_view_account_statement = tutor_configuration['allow_view_account_statement']
            allow_view_voucher = tutor_configuration['allow_view_voucher']

            set_integration_configuration(
                integration_key='odoo',
                object_instance=relationships.filter(tutor=tutor).first(),
                key='allow_view_account_statement',
                value='{}'.format(allow_view_account_statement)
            )

            set_integration_configuration(
                integration_key='odoo',
                object_instance=relationships.filter(tutor=tutor).first(),
                key='allow_view_voucher',
                value='{}'.format(allow_view_voucher)
            )

        # Redirect where it comes from
        redirect = utilities.deduct_redirect_response(request, None)

        # Return a redirect
        return ControllerResponse(
            request,
            _(u"Cliente registrado exitosamente en Odoo"),
            message_position='default',
            redirect='registration_backend_register_student' if not edition else redirect
        )

    response.sets({
        'student_profile': student_profile,
        'student_tutors': student_tutors,
        'payment_configuration_form': payment_configuration_form,
        'permissions_formset': permissions_formset
    })

    return response


def tutor_invoice(request):

    username = request.GET.get('username', None)

    user = User.objects.get(username=username)
    client_id = get_integration_id(user)

    success, response = services.call_client(client_id)

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
        # tutors_visibility = contract_form.cleaned_data.get('tutors_visibility')

        # Get users
        user = User.objects.get(username=username)
        tutor = User.objects.get(username=payments_responsible)

        # Get integration object
        client_id = get_integration_id(user)
        tutor_client_id = get_integration_id(tutor)

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
            'super_client_id': tutor_client_id
        }

        u_success, u_response = services.set_contract(client_id, contract_data)

        t_success, t_response = services.update_client(client_id, client_data)

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


def search_clients(request, query):
    return JsonResponse(services.search_clients(query), safe=False)
