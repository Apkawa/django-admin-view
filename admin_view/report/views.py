# coding: utf-8
from __future__ import unicode_literals

import shutil
from tempfile import mktemp
import datetime

import mimetypes
from collections import OrderedDict

import tablib
from django.http import HttpResponse
from django.utils.encoding import smart_str, force_bytes

from django.views.generic.list import MultipleObjectMixin

from admin_view.utils.dt import to_aware
from admin_view.views.base import AdminTemplateView


class ReportFormViewMixin(MultipleObjectMixin):
    filter_class = None
    filename = 'Report.xlsx'

    def get_filter_class(self):
        return self.filter_class

    def get_filter(self, queryset=None):
        return self.get_filter_class()(
            self.request.GET or None,
            queryset=queryset or self.get_queryset(),
            view=self
        )

    def is_filtered(self):
        get = self.request.GET.copy()
        get.pop('_export', None)
        return bool(get)

    def get_queryset(self):
        if not self.is_filtered():
            return self.model.objects.none()
        return super().get_queryset()

    def get_columns(self, filter_form):
        fields = filter_form.get_enabled_fields()
        return fields

    def get_export_format(self):
        return self.request.GET.get('_export')

    def get_context_data(self, **kwargs):
        self.object_list = self.model.objects.none()

        context = super().get_context_data(**kwargs)

        filter_form = self.get_filter()
        filter_form.form.is_valid()
        columns = self.get_columns(filter_form)

        export_format = self.get_export_format()

        qs = filter_form.qs
        page = None

        if not export_format:
            paginator, page, qs, is_paginated = self.paginate_queryset(qs, page_size=100)

        export_data = self.get_export_data(qs, columns)

        context['form'] = filter_form
        context['export_data'] = export_data
        context['export_format'] = self.get_export_format()
        context['page'] = page
        return context

    def get_export_data(self, qs, columns):
        export_data = tablib.Dataset(headers=[label for key, label in columns] + ['_instance'])
        for instance in qs:
            export_data.append(self.get_export_data_row(instance, columns) + [instance])
        return export_data

    def get_export_data_row(self, instance, columns):
        row = [self.extract_field(instance, key) for key, label in columns]
        return row

    def extract_field(self, instance, key):
        func = getattr(self, 'extract_' + key, None)
        if func:
            value = func(instance)
        else:
            if hasattr(instance, 'get_%s_display' % key):
                value = getattr(instance, 'get_%s_display' % key)()
            else:
                value = getattr(instance, key)
        if value is None:
            value = ''
        if isinstance(value, datetime.datetime):
            value = to_aware(value).strftime('%Y-%m-%d %H:%M:%S')
        return value

    def get_xlsx_file(self, request, output_file, **kwargs):
        context = self.get_context_data(**kwargs)
        export_format = context['export_format']
        export_dataset = context['export_data']
        del export_dataset[export_dataset.headers[-1]]

        with open(output_file, 'wb') as f:
            f.write(getattr(export_dataset, export_format))

        return

    def get_filename(self):

        return self.filename

    def get(self, request, *args, **kwargs):
        export_format = self.get_export_format()
        if export_format:
            from multiprocessing import Process
            output_file = mktemp(suffix='.' + export_format)
            try:
                p = Process(target=self.get_xlsx_file,
                            args=(request,),
                            kwargs={'output_file': output_file}
                            )
                p.start()
                p.join()
                filename = self.get_filename()
                content_type = mimetypes.guess_type(filename)[0]
                response = HttpResponse(
                    open(output_file, 'rb').read(),
                    content_type=content_type)
                response['Content-Disposition'] = b'attachment; filename="%s"' % force_bytes(
                    filename)
                return response
            finally:
                shutil.rmtree(output_file, ignore_errors=True)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class ReportFormView(ReportFormViewMixin, AdminTemplateView):
    template_name = "admin/custom_view/report.html"
