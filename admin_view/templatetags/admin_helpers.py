# coding: utf-8
from __future__ import unicode_literals

from django import template
from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname as orig_admin_urlname
from django.core.urlresolvers import reverse
from django.db import models

register = template.Library()


@register.filter()
def admin_urlname_v2(opts, name):
    if isinstance(opts, models.Model):
        opts = opts._meta
    return orig_admin_urlname(opts, name)


@register.simple_tag(takes_context=True)
def admin_url(context, name, *args, **kwargs):
    admin_site = context.get('ADMIN_SITE', admin.site)
    return reverse(name, args=args, kwargs=kwargs, current_app=admin_site.name)


@register.simple_tag
def row_css(cl, index):
    if not hasattr(cl.model_admin, 'get_row_css'):
        return u''
    return cl.model_admin.get_row_css(cl.result_list[index], index)
