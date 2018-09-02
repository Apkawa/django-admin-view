from inspect import isclass

import six
from django.apps import apps
from django.conf.urls import url
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_migrate
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
                r'^([^/]+)/$', getattr(self, 'change_view', None)

            ],
            'changelist': [
                r'^$', getattr(self, 'changelist_view', None)

            ],
            'delete': [
                r'^([^/]+)/delete/$', getattr(self, 'delete_view', None)

            ],
            'history': [
                r'^([^/]+)/history/$', getattr(self, 'history_view', None)
            ],
        }
        return views

    def get_info(self):
        app_label = getattr(self, 'app_label', self.model._meta.app_label)
        module_name = getattr(self, 'module_name', self.model._meta.model_name)
        return (app_label, module_name)

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


class FakeModelAdminMixin(object):
    model = None
    app_label = None
    module_name = None

    verbose_name = None
    verbose_name_plural = None

    def __init__(self, model, admin_site):
        if self.__class__.model:
            model = self.__class__.model

        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site

        assert self.app_label, 'app_label required'
        assert self.module_name, 'module_name required'

    @classmethod
    def _build_fake_model(cls, app_config=None):
        class Fake(object):
            pass

        model = Fake()
        model._meta = Fake()
        model._meta.app_label = cls.app_label
        model.__name__ = cls.module_name
        model._meta.module_name = cls.module_name

        model._meta.model_name = cls.module_name
        model._meta.object_name = cls.module_name.capitalize()

        model._meta.verbose_name = cls.verbose_name or cls.module_name
        model._meta.verbose_name_plural = cls.verbose_name_plural or cls.module_name

        if app_config is None:
            # Try get app config
            app_config = cls.__module__.split('.')[-2]

        if isinstance(app_config, six.string_types):
            app_config = apps.get_app_config(app_config)
        model._meta.app_config = app_config

        model._meta.abstract = False
        model._meta.swapped = False
        model._deferred = False
        return model

    @classmethod
    def create_permissions(cls, model):
        opts = model._meta
        ctype = ContentType.objects.get_for_model(model, for_concrete_model=False)

        permissions = dict(cls.default_permissions)
        permissions.update(dict(cls.permissions or {}))

        for action, name in permissions.items():
            if name is None:
                name = 'Can %s %s' % (action, opts.verbose_name)
            perm, created = Permission.objects.get_or_create(
                codename=get_permission_codename(action, opts),
                content_type=ctype,
                defaults=dict(name=name)
            )
            if not created and perm.name != name:
                perm.name = name
                perm.save(update_fields=['name'])

    @classmethod
    def _create_permissions(cls, *args, **kwargs):
        model = cls._build_fake_model()
        cls.create_permissions(model)

    @classmethod
    def connect_signals(cls):
        post_migrate.connect(
            cls._create_permissions,
            dispatch_uid=cls.__module__ + '.' + cls.__name__ + '.create_permissions')

    @classmethod
    def register_at(cls, admin_site, app_config=None):
        assert cls.app_label, 'app_label required'
        assert cls.module_name, 'module_name required'
        model = cls._build_fake_model(app_config)

        return admin_site.register([model], cls)

    @classmethod
    def check(cls, model=None):
        return []
