# -*- coding: utf-8 -*

from django import forms
from django.utils.translation import ugettext_lazy as _

from utils.forms import CommaSeparatedIntegerField, SemicolonWithCommaSeparatedField
from userprofiles.models import TutorProfile


class ChoiceFieldNoValidation(forms.ChoiceField):
    def validate(self, value):
        pass


class TutorPermissionsForm(forms.Form):
    tutor = forms.ModelChoiceField(
        queryset=TutorProfile.objects.all(),
        required=True, empty_label=None,
        widget=forms.HiddenInput)

    allow_view_account_statement = forms.BooleanField(required=False)
    allow_view_voucher = forms.BooleanField(required=False)


TutorPermissionsFormset = forms.formset_factory(TutorPermissionsForm, extra=0)


class PaymentResponsableConfigurationForm(forms.Form):
    student_client_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    client_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    client_name = forms.CharField(required=True, label=_(u"ie. López Pérez"))
    client_ref = forms.CharField(required=False, label=_(u"Vacío para autogenerar"))
    comercial_id = forms.IntegerField(required=False, widget=forms.HiddenInput, initial=None)
    comercial_name = forms.CharField(required=True, label=_(u"ie. Juan López"))
    comercial_number = forms.CharField(required=True, label=_(u"ie. 11111111-1"))
    comercial_address = forms.CharField(required=True, label=_(u"ie. Ciudad"))
    comercial_email = forms.EmailField(required=True, label=_(u"ie. correo@email.com"))


class ContractForm(forms.Form):
    """
    Form used for Teacher Profiles data editing.
    """

    contract_id = ChoiceFieldNoValidation(
        label=_(u"Contrato"),
        required=True
    )

    products = CommaSeparatedIntegerField(
        dedup=True,
        widget=forms.widgets.HiddenInput,
        required=True)

    payments_responsible = ChoiceFieldNoValidation(
        label=_(u"Responsable"),
        required=True
    )

    name = forms.CharField(
        label=_(u"A Nombre de"),
        required=False,
        max_length=150)
    """ Contract name parameter. """

    nit = forms.CharField(
        label=_(u"NIT"),
        required=False,
        max_length=150)
    """ Contract NIT parameter. """

    phone = forms.CharField(
        label=_(u"Teléfono"),
        required=False,
        max_length=150)
    """ Contract phone parameter. """

    address = forms.CharField(
        label=_(u"Dirección"),
        required=False,
        max_length=500,
        widget=forms.Textarea)
    """ Contract address parameter. """

    tutors_visibility = SemicolonWithCommaSeparatedField(
        label=_(u"Visibilidad"),
        widget=forms.widgets.HiddenInput,
        required=False)
    """ Contract address parameter. """

    def __init__(self, *args, **kwargs):
        if 'contract' in kwargs:
            ch_contract = kwargs.pop('contract')
        if 'parents' in kwargs:
            ch_parents = kwargs.pop('parents')
        super(ContractForm, self).__init__(*args, **kwargs)
        if 'ch_contract' in locals():
            self.fields['contract_id'].choices = ch_contract
        if 'ch_parents' in locals():
            self.fields['payments_responsible'].choices = ch_parents
