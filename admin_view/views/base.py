from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, FormView

from admin_view.mixins.views import AdminViewMixin


class AdminObjectView(AdminViewMixin):

    def get_queryset(self):
        return self.admin.get_queryset(self.request)

    def get_object_id(self):
        return self.kwargs[self.pk_url_kwarg]

    def get_object(self, queryset=None):
        obj = self.admin.get_object(self.request, self.get_object_id())
        if obj is None:
            raise ObjectDoesNotExist("Not found")
        return obj


class AdminTemplateView(AdminViewMixin, TemplateView):
    template_name = None


class AdminFormView(AdminViewMixin, FormView):
    pass
