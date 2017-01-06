# -*- coding: utf-8 -*-
from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^(?P<username>[\w.@+-]+)/set_contract/$',
        views.get_contract,
        name='odoo-get-contract'
    ),
    url(
        r'^ajax/tutor-invoice/$',
        views.tutor_invoice,
        name='odoo-tutor-invoice'
    )
]
