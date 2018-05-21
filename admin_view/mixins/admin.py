from inspect import isclass

from django.conf.urls import url
from django.contrib.auth import get_permission_codename
from django.db import models
from django.views import View



class PermissionShortcutAdminMixin(object):
    opts = None

    def get_permission_name(self, perm_type='change', opts=None):
        opts = opts or self.opts
        if isinstance(opts, models.Model):
            opts = opts._meta
        codename = get_permission_codename(perm_type, opts)
        return '{}.{}'.format(opts.app_label, codename)

    def has_user_permission(self, request, perm_name, obj=None):
        perm_name = self.get_permission_name(perm_name, obj)
        # print self, perm_name
        return request.user.has_perm(perm_name)

    def has_user_negative_permission(self, request, perm_name, obj=None):
        """
        Права доступа, которые отключают функциональность.
        """
        return not request.user.is_superuser and self.has_user_permission(request, perm_name, obj)


class ClassViewAdminMixin(object):
    view_classes = {

    }
    template_name = None

    def get_template_name(self, view_name=None, view_class=None):
        return self.template_name

    def get_view_classes(self):
        return self.view_classes

    def _get_original_views(self):
        views = {
            'add': [
                r'^add/$', getattr(self, 'add_view', None)
            ],
            'change': [
                r'^(.+)/$', getattr(self, 'change_view', None)

            ],
            'changelist': [
                r'^$', getattr(self, 'changelist_view', None)

            ],
            'delete': [
                r'^(.+)/delete/$', getattr(self, 'delete_view', None)

            ],
            'history': [
                r'^(.+)/history/$', getattr(self, 'history_view', None)
            ],
        }
        return views

    def get_info(self):
        return (self.model._meta.app_label, self.model._meta.model_name)

    def build_url(self, pattern, view, name=None):
        if name:
            name %= self.get_info()

        return url(
            pattern, self.admin_site.admin_view(view), name=name
        )

    def get_extra_urls(self):
        return list()

    def get_urls(self):
        urlpatterns = self.get_extra_urls()
        original_views = self._get_original_views()
        view_classes = dict(original_views)
        view_classes.update(self.get_view_classes())
        for name, view in view_classes.items():
            pattern = None
            if isinstance(view, (list, tuple)):
                pattern, view = view

            if view is None:
                continue

            if isclass(view) and issubclass(view, View):

                view_kw = {}
                if getattr(view, 'template_name', None) is None:
                    view_kw['template_name'] = self.get_template_name(name)

                view = view.as_view(admin=self, view_type=name, **view_kw)

            if pattern is None:
                if name in original_views:
                    pattern = original_views[name][0]
                else:
                    pattern = r'^(.+)/%s/$' % name

            urlpatterns.append(self.build_url(pattern,
                                              view,
                                              name='%s_%s_' + name))

        return self.get_extra_urls() + urlpatterns

    def _get_urls(self):
        return self.get_urls()

    urls = property(_get_urls)


