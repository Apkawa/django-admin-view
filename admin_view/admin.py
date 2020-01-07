# coding: utf-8
from __future__ import unicode_literals

import copy
import itertools

import six
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.templatetags.static import static
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from admin_view.mixins.admin import (
    ClassViewAdminMixin,
    PermissionShortcutAdminMixin,
    FakeModelAdminMixin
)
from .changelist import PerPageChangeList
from .views.base import AdminTemplateView

try:
    from pymorphy2 import MorphAnalyzer
except ImportError:
    MorphAnalyzer = None

try:
    from django_object_actions import BaseDjangoObjectActions
except ImportError:
    class BaseDjangoObjectActions:
        pass

FORM_FIELD_OVERRIDES = {}

try:
    from easy_thumbnails.fields import ThumbnailerField
    from easy_thumbnails.widgets import ImageClearableFileInput

    FORM_FIELD_OVERRIDES[ThumbnailerField] = {'widget': ImageClearableFileInput}
except ImportError:
    pass


class CustomAdmin(six.with_metaclass(
    forms.MediaDefiningClass,
    PermissionShortcutAdminMixin,
    ClassViewAdminMixin,
    FakeModelAdminMixin
)):
    fields = fieldsets = exclude = ()
    date_hierarchy = ordering = None
    list_select_related = save_as = save_on_top = False

    app_label = None
    module_name = None

    verbose_name = u''
    verbose_name_plural = u''

    use_permission = True

    default_permissions = {
        'change': None,
        'add': None,
        'delete': None,
        'view': None,
    }
    permissions = None

    template_name = 'admin/custom_view/custom_view.html'

    change_view = changelist_view = add_view = AdminTemplateView

    actions = None

    def __init__(self, model, admin_site):
        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site

        assert self.app_label, 'app_label required'
        assert self.module_name, 'module_name required'

    def get_view_on_site_url(self, obj):
        return None

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
        if self.use_permission:
            return self.has_user_permission(request, 'add')
        return False

    def has_delete_permission(self, request, obj=None):
        if self.use_permission:
            return self.has_user_permission(request, 'delete')
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
            title=self.get_title(None),
            media=self.media + self.get_media()

        )

    def get_media(self):
        extra = '' if settings.DEBUG else '.min'
        js = [
            'core.js',
            'vendor/jquery/jquery%s.js' % extra,
            'jquery.init.js',
            'admin/RelatedObjectLookups.js',
            'actions%s.js' % extra,
            'urlify.js',
            'prepopulate%s.js' % extra,
            'vendor/xregexp/xregexp%s.js' % extra,
        ]
        if self.actions is not None:
            js.append('actions%s.js%s' % (extra, settings.STATIC_REV))
        # if self.prepopulated_fields:
        #     js.extend([
        #         'urlify.js?r=%s' % settings.STATIC_REV,
        #         'prepopulate%s.js%s' % (extra, settings.STATIC_REV)
        #     ])
        return forms.Media(js=[static('admin/js/%s' % url) for url in js])


class ModelViewAdminMixin(
    ClassViewAdminMixin,
    PermissionShortcutAdminMixin,
    BaseDjangoObjectActions,
    FakeModelAdminMixin):
    formfield_overrides = FORM_FIELD_OVERRIDES

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
        return (not super(ModelViewAdminMixin, self).has_change_permission(request, obj)
                and self.has_view_permission(request, obj))

    def has_view_permission(self, request, obj=None):
        for perm_key in ['view', 'change']:
            if self.has_user_permission(request, perm_key):
                return True
        return False

    def has_change_permission(self, request, obj=None):
        change_perm = super(ModelViewAdminMixin, self).has_change_permission(request, obj)
        if not change_perm:
            return self.has_view_permission(request, obj)
        return change_perm

    def get_model_perms(self, request):
        perms = super(ModelViewAdminMixin, self).get_model_perms(request)
        perms['readonly'] = self.has_readonly_permission(request)
        perms['view'] = self.has_view_permission(request)
        perms['change'] = perms['change'] or perms['view']
        return perms

    def get_urls(self):
        urlpatterns = super(ModelViewAdminMixin, self).get_urls()
        return self._get_action_urls() + urlpatterns

    def get_info(self, model=None):
        info = super().get_info()
        return info

    _info = property(get_info)

    def _site_namespace(self):
        return self.admin_site.name

    def _reverse(self, name, *args, **kwargs):
        name = ("%s_%s_" % self.get_info()) + name
        return reverse("%s:%s" % (self._site_namespace(), name), args=args, kwargs=kwargs)

    def _get_translation_fields_map(self):
        try:
            from modeltranslation.utils import get_translation_fields
        except ImportError:
            return {}
        return {
            f: tuple(get_translation_fields(f))
            for f in self.trans_opts.fields
        }

    def get_fieldsets(self, request, obj=None):
        if not getattr(self, 'trans_opts', None):
            return super(ModelViewAdminMixin, self).get_fieldsets(request, obj)
        fieldsets = self.fieldsets
        if not fieldsets:
            fieldsets = [(None, {'fields': self.get_fields(request, obj)})]
        else:
            fieldsets = copy.deepcopy(list(fieldsets))
        translation_fields_map = self._get_translation_fields_map()
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
        ModelForm = super(ModelViewAdminMixin, self).get_form(request, obj, **kwargs)
        # fieldset = self.get_fieldsets(request, obj)
        # ModelForm.helper = self.get_crispy_helper(ModelForm, fieldset)
        return ModelForm

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        kwargs['widget'] = FilteredSelectMultiple(db_field.verbose_name, is_stacked=False)
        return super(ModelViewAdminMixin, self).formfield_for_manytomany(db_field, request,
                                                                         **kwargs)

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

        context['title'] = self.get_title(obj)
        context['media'] = self.media

        context['has_view_permission'] = self.has_view_permission(request, obj)
        context['has_readonly_permission'] = self.has_readonly_permission(request, obj)

        # TODO FIXME
        # context.update(BaseDjangoObjectActions._get_change_context(self, request, object_id,
        #                                                            form_url=form_url))
        return context

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(ModelViewAdminMixin, self).change_view(request, object_id, form_url,
                                                            extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = self.get_extra_context(request,
                                               object_id=object_id, form_url='',
                                               extra_context=extra_context)
        return super(ModelViewAdminMixin, self).changeform_view(request, object_id, form_url,
                                                                extra_context)


class ModelViewAdmin(ModelViewAdminMixin,
                     admin.ModelAdmin):
    pass
