import datetime

from ajax_select.fields import AutoCompleteSelectMultipleField
from crispy_forms.bootstrap import FormActions, Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit
from django import forms
from django.db.models import Q
from django.forms.fields import SplitDateTimeField
from django.urls.base import reverse
from multiupload.fields import MultiFileField
from natural_duration import NaturalDurationField
from pagedown.widgets import PagedownWidget

from .models import ServiceAnnounce

class SrvAnnounceSendForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SrvAnnounceSendForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal container'
        self.helper.label_class = 'col-lg-1'
        self.helper.field_class = 'col-lg-12'
        self.helper.layout = Layout(
            'subject',
            'message',
            'email_to',
            FormActions(
                Submit('save', 'Save Changes'),
            )
        )

    def save(self, commit=True):
        self.instance = super(SrvAnnounceSendForm, self).save(commit=False)
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance

    class Meta:
        model = ServiceAnnounce
        fields = ('subject', 'message')
        widgets = {
            'message': PagedownWidget(),
        }
