# coding: utf-8
from __future__ import unicode_literals

from collections import OrderedDict

import django_filters as filters

from django import forms
from django_filters.widgets import RangeWidget
from django.contrib.admin.widgets import AdminDateWidget


class ReportForm(forms.Form):
    def clean(self):
        data = self.cleaned_data
        fields = {key[len('on_'):]: val for key, val in data.items() if key.startswith('on_')}
        self._enabled_fields = enabled_fields = [key for key, val in fields.items() if val]

        new_data = dict.fromkeys(fields, None)
        for e_field in enabled_fields:
            e_value = data.get(e_field)
            if e_value:
                new_data[e_field] = e_value
        return new_data


class DateRangeWidget(RangeWidget):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs.update({'data-datetimepicker': 'date'})
        date_widget_class = attrs.get('date_widget', AdminDateWidget)
        widgets = (date_widget_class(attrs=attrs.copy()), date_widget_class(attrs=attrs.copy()))
        forms.MultiWidget.__init__(self, widgets, attrs)


class BaseReportFilter(filters.FilterSet):
    class Meta:
        form = ReportForm

    def __init__(self, *args, **kwargs):
        self.view = kwargs.pop('view', None)
        super().__init__(*args, **kwargs)
        self.filters = OrderedDict(self.get_filters())

        initial_enabled = set(self.get_initial_enabled_fields())
        for name, f in self.get_filters().items():
            bound_field = self.form[name]
            field = bound_field.field
            field.required = False
            field.widget.attrs.update({
                'disabled': 'disabled',
                'class': 'form-control'
            })
            field.help_text = None
            if isinstance(f, filters.RangeFilter) \
                or f.field_class == filters.RangeFilter.field_class:
                bound_field.wrap_class = 'form-inline'
                field.widget.attrs.update({
                    "style": "width: 49%"
                })

            self.form.fields['on_' + name] = forms.BooleanField(required=False, label=f.label,
                                                                widget=forms.CheckboxInput,
                                                                initial=name in initial_enabled,
                                                                )
            self.form.fields['on_' + name].widget.attrs['to_field'] = name

    def get_form_fields(self):
        fields = []
        for name in self._meta.fields:
            if not name.startswith('on_'):
                fields.append([self.form[name], self.form['on_' + name]])
        return fields

    @classmethod
    def get_filters(cls):
        fields = cls._meta.fields
        filters = super().get_filters()
        return dict([(name, f) for name, f in filters.items() if name in fields])

    def get_initial_enabled_fields(self):
        return []

    def get_enabled_fields(self):
        form_fields = getattr(self.form, '_enabled_fields',
                              None) or self.get_initial_enabled_fields()
        fields = [(e, self.filters[e].label) for e in form_fields]
        return sorted(fields, key=lambda f: self._meta.fields.index(f[0]))
