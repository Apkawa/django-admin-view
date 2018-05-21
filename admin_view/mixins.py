from __future__ import unicode_literals

import copy
import itertools
from inspect import isclass

from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_permission_codename
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import View

from easy_thumbnails.fields import ThumbnailerField
from easy_thumbnails.widgets import ImageClearableFileInput
from modeltranslation.utils import get_translation_fields

try:
    from pymorphy2 import MorphAnalyzer
except ImportError:
    MorphAnalyzer = None

from django_object_actions import BaseDjangoObjectActions


class AdminFilteredSelectMultiple(FilteredSelectMultiple):
    pass


class PerPageChangeList(ChangeList):
    per_page_param_name = 'per_page'

    per_page_choices = [25, 50, 100, 200]

    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields, list_select_related,
                 list_per_page, list_max_show_all, list_editable, model_admin
                 ):
        self.show_per_page = model_admin.show_per_page
        if self.show_per_page:
            try:
                list_per_page = int(request.GET.get(self.per_page_param_name) or list_per_page)
            except ValueError:
                pass
        super(PerPageChangeList, self).__init__(
            request, model, list_display, list_display_links,
            list_filter, date_hierarchy, search_fields, list_select_related,
            list_per_page, list_max_show_all, list_editable, model_admin
        )

    def get_filters_params(self, params=None):
        params = super(PerPageChangeList, self).get_filters_params(params)
        params.pop(self.per_page_param_name, None)
        return params

    def per_page_links(self):

        return [(per_page, self.get_query_string({self.per_page_param_name: per_page}))
                for per_page in self.per_page_choices]


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


class ApiJsonContextMixin(object):
    def get_json_context(self, request, object_id=None, form_url='', ):
        add = object_id is None

        json_context = {
            'object_id': object_id,
            'add': add,
            'change': not add,
            'admin': {
                'app_label': self.opts.app_label,
                'model_name': self.opts.model_name,
                'object_name': self.opts.object_name,
            },

        }
        if hasattr(self, 'has_readonly_permission'):
            json_context['has_readonly_permission'] = self.has_readonly_permission(request, None)
        return json_context


class AdminClassViewMixin(object):
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


class MyModelAdmin(AdminClassViewMixin, PermissionShortcutAdminMixin, ApiJsonContextMixin,
                   BaseDjangoObjectActions,
                   admin.ModelAdmin):
    # formfield_overrides = {
    #     models.ManyToManyField: {'widget': FilteredSelectMultiple("verbose name", is_stacked=False)},
    # }
    formfield_overrides = {
        ThumbnailerField: {'widget': ImageClearableFileInput},
    }

    change_actions = []
    readonly_view_template = None

    show_per_page = False

    def get_view_on_site_url(self, obj=None):
        if obj is None or not self.view_on_site:
            return None

        if callable(self.view_on_site):
            return self.view_on_site(obj)
        elif self.view_on_site and hasattr(obj, 'get_absolute_url'):
            # use the ContentType lookup if view_on_site is True
            return reverse('admin:view_on_site', kwargs={
                'content_type_id': get_content_type_for_model(obj).pk,
                'object_id': obj.pk
            }, current_app=self.admin_site.name)

    def get_changelist(self, request, **kwargs):
        return PerPageChangeList

    def has_readonly_permission(self, request, obj=None):
        if '_readonly' in request.GET:
            return True
        return (not super(MyModelAdmin, self).has_change_permission(request, obj)
                and self.has_view_permission(request, obj))

    def has_view_permission(self, request, obj=None):
        for perm_key in ['view', 'change']:
            if self.has_user_permission(request, perm_key):
                return True
        return False

    def has_change_permission(self, request, obj=None):
        change_perm = super(MyModelAdmin, self).has_change_permission(request, obj)
        if not change_perm:
            return self.has_view_permission(request, obj)
        return change_perm

    def get_model_perms(self, request):
        perms = super(MyModelAdmin, self).get_model_perms(request)
        perms['readonly'] = self.has_readonly_permission(request)
        perms['view'] = self.has_view_permission(request)
        perms['change'] = perms['change'] or perms['view']
        return perms

    def get_urls(self):
        urlpatterns = super(MyModelAdmin, self).get_urls()
        return self._get_action_urls() + urlpatterns

    def get_info(self, model=None):
        model = model or self.model
        return model._meta.app_label, self.model._meta.model_name

    _info = property(get_info)

    def _site_namespace(self):
        return self.admin_site.name

    def _reverse(self, name, *args, **kwargs):
        name = ("%s_%s_" % self.get_info(kwargs.pop('model', None))) + name
        return reverse("%s:%s" % (self._site_namespace(), name), args=args, kwargs=kwargs)

    def get_fieldsets(self, request, obj=None):
        if not getattr(self, 'trans_opts', None):
            return super(MyModelAdmin, self).get_fieldsets(request, obj)
        fieldsets = self.fieldsets
        if not fieldsets:
            fieldsets = [(None, {'fields': self.get_fields(request, obj)})]
        else:
            fieldsets = copy.deepcopy(list(fieldsets))

        translation_fields_map = {f: tuple(get_translation_fields(f))
                                  for f in self.trans_opts.fields
                                  }
        for i, (group, fields_info) in enumerate(fieldsets):
            fields = []
            for field in fields_info['fields']:
                if isinstance(field, (list, tuple)):
                    new_fields = []
                    for f in field:
                        if isinstance(f, list):
                            f = tuple(f)
                        new_fields.append(translation_fields_map.get(f, [f]))
                    fields.append(tuple(itertools.chain.from_iterable(new_fields)))
                else:
                    fields.append(translation_fields_map.get(field, field))
            fields_info['fields'] = fields
        return fieldsets

    def get_crispy_helper(self, form_class, fieldsets):
        # TODO extract to mixin
        from crispy_forms.helper import FormHelper, Layout
        from crispy_forms.layout import Div, Fieldset

        helper = getattr(form_class, 'helper', None)

        if helper and isinstance(helper, FormHelper):
            return helper

        helper = FormHelper()

        helper_args = []
        for header, _fieldset in fieldsets:
            _fieldset_args = []
            for _field in _fieldset['fields']:
                if isinstance(_field, (tuple, list)):
                    row = Div(
                        *_field,
                        css_class='form-row form-group field-box col-sm-%s' % (12 / len(_field)))
                else:
                    row = Div(
                        *_field,
                        css_class='form-row form-group')

                _fieldset_args.append(row)
            helper_args.append(
                Fieldset(
                    header,
                    *_fieldset_args,
                    css_class=_fieldset.get('classes')
                )
            )
        helper.add_layout(Layout(*helper_args))
        return helper

    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(MyModelAdmin, self).get_form(request, obj, **kwargs)
        # fieldset = self.get_fieldsets(request, obj)
        # ModelForm.helper = self.get_crispy_helper(ModelForm, fieldset)
        return ModelForm

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, is_stacked=False)
        return super(MyModelAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def get_title(self, obj=None):
        add = not obj
        title = (_('Add %s') if add else _('Change %s')) % force_text(self.opts.verbose_name)
        if not MorphAnalyzer:
            return title

        morph = MorphAnalyzer()
        parsed_morph = morph.parse(title)[0].inflect({'sing', 'accs'})

        if parsed_morph:
            title = parsed_morph.word
        return title.title()

    def get_extra_context(self, request, object_id=None, form_url='', extra_context=None):
        context = extra_context or {}
        add = object_id is None

        obj = self.get_object(request, object_id=object_id)

        context['json_context'] = self.get_json_context(request, object_id, form_url)
        context['title'] = self.get_title(obj)
        context['media'] = self.media

        context['has_view_permission'] = self.has_view_permission(request, obj)
        context['has_readonly_permission'] = self.has_readonly_permission(request, obj)

        context.update(BaseDjangoObjectActions._get_change_context(self, request, object_id,
                                                                   form_url=form_url))
        return context

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(MyModelAdmin, self).change_view(request, object_id, form_url,
                                                     extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = self.get_extra_context(request,
                                               object_id=object_id, form_url='',
                                               extra_context=extra_context)
        return super(MyModelAdmin, self).changeform_view(request, object_id, form_url,
                                                         extra_context)
