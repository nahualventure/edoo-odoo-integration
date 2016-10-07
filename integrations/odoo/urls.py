# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r'^(?P<username>[\w.@+-]+)/set_contract/$',
        views.set_contract,
        name='odoo_set_contract'
    )
]
