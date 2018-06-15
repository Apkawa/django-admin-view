from functools import wraps

from django.contrib.admin.views.decorators import staff_member_required


def admin_view_class(view_class, view_type='change', template_name=None):
    def decorator(func):
        @wraps(func)
        def wrap(self, request, *args, **kwargs):
            view = getattr(func, '_view', None)
            if not view:
                view_kw = {}
                if template_name:
                    view_kw['template_name'] = template_name
                view = staff_member_required(
                    view_class.as_view(admin=self, view_type=view_type, **view_kw))
                setattr(func, '_view', None)
            return view(request, *args, **kwargs)
        return wrap
    return decorator
