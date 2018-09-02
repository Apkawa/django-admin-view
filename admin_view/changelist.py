from django.contrib.admin.utils import quote
from django.contrib.admin.views.main import ChangeList
from django.urls import reverse


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

    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse('admin:%s_%s_change' % (self.model_admin.get_info()),
                       args=(quote(pk),),
                       current_app=self.model_admin.admin_site.name)
