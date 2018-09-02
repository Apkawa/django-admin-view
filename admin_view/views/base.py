from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, FormView

from admin_view.mixins.views import AdminViewMixin


class AdminObjectView(AdminViewMixin):

    def get_queryset(self):
        if not hasattr(self.admin, 'get_queryset'):
            return super().get_queryset()

        return self.admin.get_queryset(self.request)

    def get_object_id(self):
        return self.kwargs[self.pk_url_kwarg]

    def get_object(self, queryset=None):
        if not hasattr(self.admin, 'get_object'):
            return super().get_object(queryset)
        obj = self.admin.get_object(self.request, self.get_object_id())
        if obj is None:
            raise ObjectDoesNotExist("Not found")
        return obj


class AdminTemplateView(AdminViewMixin, TemplateView):
    template_name = 'admin/custom_view/custom_view.html'


class AdminFormView(AdminViewMixin, FormView):
    pass
