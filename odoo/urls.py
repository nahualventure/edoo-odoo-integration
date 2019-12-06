# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^student/enroll-or-unenroll/$',
        views.enroll_or_unenroll_student,
        name='enroll_or_unenroll_student'
    ),
    url(
        r'^synchronization/account-statements/$',
        views.synchronization_account_statements,
        name='synchronization_account_statements'
    ),
    url(
        r'^synchronization/school-management-type/$',
        views.school_management_type,
        name='school_management_type'
    ),
    url(
        r'^(?P<student_id>[\w.@+-]+)/registration/$',
        views.registration,
        name='odoo-registration'
    ),
    url(
        r'^(?P<student_id>[\w.@+-]+)/client-edition/$',
        views.client_edition,
        name='odoo-client-edition'
    ),
    url(
        r'^search/clients/$',
        views.search_clients,
        name='odoo-search-clients'
    ),
    url(
        r'^ajax/tutor-invoice/$',
        views.tutor_invoice,
        name='odoo-tutor-invoice'
    )
]
