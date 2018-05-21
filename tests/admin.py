from django.contrib import admin

from admin_view.admin import CustomAdmin
from admin_view.views.base import AdminTemplateView


class ExampleView(AdminTemplateView):
    pass


class ReportOrderAdmin(CustomAdmin):
    app_label = 'tests'
    module_name = 'example'

    verbose_name = 'Example admin'
    verbose_name_plural = verbose_name

    add_view = change_view = changelist_view = ExampleView

    def get_title(self, obj):
        return "A Example admin"


ReportOrderAdmin.register_at(admin.site)
