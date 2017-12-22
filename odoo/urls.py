# -*- coding: utf-8 -*-
from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^(?P<student_id>[\w.@+-]+)/registration/$',
        views.registration,
        name='odoo-registration'
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
