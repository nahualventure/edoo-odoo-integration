# -*- coding: utf-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path(
        'student/enroll-or-unenroll/',
        views.enroll_or_unenroll_student,
        name='enroll_or_unenroll_student'
    ),
    path(
        'synchronization/account-statements/',
        views.synchronization_account_statements,
        name='synchronization_account_statements'
    ),
    path(
        'synchronization/school-management-type/',
        views.school_management_type,
        name='school_management_type'
    ),
    path(
        '(<str:student_id>/registration/',
        views.registration,
        name='odoo-registration'
    ),
    path(
        '(<str:student_id>/client-edition/',
        views.client_edition,
        name='odoo-client-edition'
    ),
    path(
        'search/clients/',
        views.search_clients,
        name='odoo-search-clients'
    ),
    path(
        'ajax/tutor-invoice/',
        views.tutor_invoice,
        name='odoo-tutor-invoice'
    )
]
