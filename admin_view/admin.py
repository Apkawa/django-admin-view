# coding: utf-8
from __future__ import unicode_literals

import six
from django import forms
from django.apps import apps
from django.conf import settings
from django.templatetags.static import static

from .mixins import (
    PermissionShortcutAdminMixin, ApiJsonContextMixin,
    AdminClassViewMixin
)

from .views import AdminTemplateView


class CustomAdmin(six.with_metaclass(
    forms.MediaDefiningClass,
    PermissionShortcutAdminMixin,
    AdminClassViewMixin,
    ApiJsonContextMixin
)):
    fields = fieldsets = exclude = ()
    date_hierarchy = ordering = None
    list_select_related = save_as = save_on_top = False

    app_label = None
    module_name = None

    verbose_name = u''
    verbose_name_plural = u''

    use_permission = True

    template_name = 'admin/custom_view/custom_view.html'

    change_view = changelist_view = add_view = AdminTemplateView

    def __init__(self, model, admin_site):
        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site

        assert self.app_label, 'app_label required'
        assert self.module_name, 'module_name required'

    def get_view_on_site_url(self, obj):
        return None

    @classmethod
    def _registration_args(cls, app_config=None):
        class Fake(object):
            pass

        model = Fake()
        model._meta = Fake()
        model._meta.app_label = cls.app_label
        model.__name__ = cls.module_name
        model._meta.module_name = cls.module_name

        model._meta.model_name = cls.module_name
        model._meta.object_name = cls.module_name.capitalize()

        model._meta.verbose_name = cls.verbose_name
        model._meta.verbose_name_plural = cls.verbose_name_plural

        if app_config is None:
            # Try get app config
            app_config = cls.__module__.split('.')[-2]

        if isinstance(app_config, six.string_types):
            app_config = apps.get_app_config(app_config)
        model._meta.app_config = app_config

        model._meta.abstract = False
        model._meta.swapped = False
        model._deferred = False
        return (model,), cls

    @classmethod
    def register_at(cls, admin_site, app_config=None):
        return admin_site.register(*cls._registration_args(app_config))

    @classmethod
    def check(cls, model=None):
        return []

    def has_change_permission(self, request, obj=None):
        if self.use_permission:
            return self.has_user_permission(request, 'change')
        return True

    def has_view_permission(self, request, obj=None):
        if self.use_permission:
            for perm_key in ['change', 'view']:
                if self.has_user_permission(request, perm_key):
                    return True
            return False
        return True

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return request.user.has_module_perms(self.opts.app_label)

    def get_model_perms(self, request, obj=None):
        """
        Returns a dict of all perms for this model. This dict has the keys
        ``add``, ``change``, and ``delete`` mapping to the True/False for each
        of those actions.
        """
        return {
            'view': self.has_view_permission(request, obj),
            'change': self.has_change_permission(request, obj),
            'add': self.has_add_permission(request),
            'delete': self.has_delete_permission(request, obj),
        }

    def get_title(self, obj):
        return self.verbose_name

    def get_extra_context(self, request, *args, **kwargs):
        return dict(
            self.admin_site.each_context(request),
            app_label=self.app_label,
            verbose_name=self.verbose_name,
            opts=self.model._meta,
            json_context=self.get_json_context(request, *args),
            title=self.get_title(None),
            media=self.media

        )

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        js = [
            'core.js?r=%s' % settings.STATIC_REV,
            'jquery%s.js%s' % (extra, settings.STATIC_REV),
            'jquery.init.js?r=%s' % settings.STATIC_REV,
            'admin/RelatedObjectLookups.js?r=%s' % settings.STATIC_REV,
        ]
        if self.actions is not None:
            js.append('actions%s.js%s' % (extra, settings.STATIC_REV))
        if self.prepopulated_fields:
            js.extend([
                'urlify.js?r=%s' % settings.STATIC_REV,
                'prepopulate%s.js%s' % (extra, settings.STATIC_REV)
            ])
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])
