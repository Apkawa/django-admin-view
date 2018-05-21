from django.apps import AppConfig as BaseConfig
from django.utils.translation import ugettext_lazy as _


class AdminViewConfig(BaseConfig):
    name = 'admin_view'
    verbose_name = _('Admin View')
