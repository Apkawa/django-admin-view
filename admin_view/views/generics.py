from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, UpdateView, ListView

from .base import AdminObjectView


class AdminListView(AdminObjectView, ListView):
    permission_name = 'view'

    def get_context_data(self, **kwargs):
        context = AdminObjectView.get_context_data(self, **kwargs)
        context.update(ListView.get_context_data(self, **kwargs))
        return context

    def dispatch(self, request, object_id=None, form_url='', extra_context=None, **kwargs):
        self.kwargs = {
            'pk': object_id,
            'form_url': form_url,
            'extra_context': extra_context
        }
        self.kwargs.update(kwargs)
        return super(AdminListView, self).dispatch(request, **self.kwargs)


class AdminDetailView(AdminObjectView, DetailView):
    permission_name = 'view'

    def get_context_data(self, **kwargs):
        context = AdminObjectView.get_context_data(self, **kwargs)
        context.update(DetailView.get_context_data(self, **kwargs))
        return context

    def dispatch(self, request, object_id=None, form_url='', extra_context=None, **kwargs):
        self.kwargs = {
            'pk': object_id,
            'form_url': form_url,
            'extra_context': extra_context
        }
        self.kwargs.update(kwargs)
        return super(AdminDetailView, self).dispatch(request, **self.kwargs)


class AdminUpdateView(AdminObjectView, UpdateView):
    permission_name = 'change'
    success_url = ''

    def get_admin_context(self, **extra_context):
        context = super(AdminUpdateView, self).get_admin_context(**extra_context)
        context.update(self.admin.get_extra_context(self.request, object_id=None))
        return context

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context.update(self.get_admin_context())
        return context

    def form_invalid(self, form):
        return super(AdminUpdateView, self).form_invalid(form)

    def form_valid_response(self, form):
        if self.is_add():
            return self.admin.response_add(self.request, self.object)
        return self.admin.response_change(self.request, self.object)

    def form_valid(self, form):
        self.object = form.save()
        if hasattr(form, 'save_m2m'):
            form.save_m2m()
        return self.form_valid_response(form)

    @method_decorator(staff_member_required)
    def dispatch(self, request, object_id=None, form_url='', extra_context=None, **kwargs):
        self.kwargs = {
            'pk': object_id,
            'form_url': form_url,
            'extra_context': extra_context,
        }
        self.kwargs.update(**kwargs)
        return super(AdminUpdateView, self).dispatch(request, **self.kwargs)


class AdminAddFormView(AdminUpdateView):
    permission_name = 'add'

    def get_object(self, queryset=None):
        return None


class AdminChangeFormView(AdminUpdateView):
    permission_name = 'change'
    is_allow_add = True

    def get_admin_context(self, **extra_context):
        context = AdminObjectView.get_admin_context(self, **extra_context)
        if hasattr(self.admin, 'get_extra_context'):
            context.update(
                self.admin.get_extra_context(self.request, object_id=self.object and self.object.id))
        return context

    def get_object(self, queryset=None):
        try:
            return super(AdminChangeFormView, self).get_object(queryset)
        except ObjectDoesNotExist as e:
            if not self.is_allow_add:
                raise Http404("Not found")
