from django.contrib import admin

from admin_view.admin import CustomAdmin, ModelViewAdmin
from admin_view.views.base import AdminTemplateView
from tests.models import ExampleModel


class ExampleView(AdminTemplateView):
    pass


class CustomExampleAdmin(CustomAdmin):
    app_label = 'tests'
    module_name = 'custom'

    verbose_name = 'Custom template admin'
    verbose_name_plural = verbose_name

    permissions = {
        'only_self': "Can view only self orders"
    }

    add_view = change_view = changelist_view = ExampleView

    def get_title(self, obj):
        return "A Example admin"


CustomExampleAdmin.register_at(admin.site)


@admin.register(ExampleModel)
class ExampleModelAdmin(admin.ModelAdmin):
    pass


class ExampleCloneAdmin(ModelViewAdmin):
    model = ExampleModel
    app_label = 'tests'
    module_name = 'example_model_clone'

    view_classes = {
        'add': AdminTemplateView
    }




ExampleCloneAdmin.register_at(admin.site)
