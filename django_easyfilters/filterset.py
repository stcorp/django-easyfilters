from logging import getLogger

from django import template
from django.template.loader import get_template
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst, Truncator

from .filters import ChoicesFilter, DateTimeFilter, FILTER_DISPLAY, FILTER_REMOVE, \
    ForeignKeyFilter, ManyToManyFilter, NumericRangeFilter, ValuesFilter
from .utils import get_model_field


def non_breaking_spaces(val):
    # This helps a lot with presentation, by stopping the links+count from being
    # split over a line end.
    val = val.replace(u'-', u'\u2011')
    return mark_safe(u'&nbsp;'.join(escape(part) for part in val.split(u' ')))


class FilterSet(object):

    # If the attribute "template" is provided (as a string), that will be
    # preferred;  otherwise we use the specified template_file
    template = None
    template_file = "django_easyfilters/default.html"

    title_fields = None
    defaults = None

    def __init__(self, queryset, params):
        self.params = params
        self.model = queryset.model
        self.filters = self.setup_filters()
        self.qs = self.apply_filters(queryset)

    @cached_property
    def title(self):
        return self.make_title()

    def get_filter_choices(self, filter_field):
        if not hasattr(self, '_cached_filter_choices'):
            self._cached_filter_choices = dict((f.field, f.get_choices(self.qs))
                                               for f in self.filters)
        return self._cached_filter_choices[filter_field]

    def apply_filters(self, queryset):
        for f in self.filters:
            queryset = f.apply_filter(queryset)
        return queryset

    def render_filter(self, filter_):
        field_obj, _m2m = get_model_field(self.model, filter_.field)
        choices = self.get_filter_choices(filter_.field)
        ctx = {'filterlabel': capfirst(field_obj.verbose_name)}
        ctx['choices'] = [dict(label=non_breaking_spaces(c.label),
                               url=u'?' + c.params.urlencode()
                                   if c.link_type != FILTER_DISPLAY else None,
                               link_type=c.link_type,
                               count=c.count)
                          for c in choices]
        return self.get_template(filter_.field).render(ctx)

    def get_template(self, field_name):
        if self.template:
            return template.Template(self.template)
        else:
            return get_template(self.template_file)

    def render(self):
        return mark_safe(u'\n'.join(self.render_filter(f)
                         for f in self.filters))

    def get_fields(self):
        return self.fields

    def get_filter_for_field(self, field):
        f, m2m = get_model_field(self.model, field)
        if f.remote_field is not None:
            if m2m:
                return ManyToManyFilter
            else:
                return ForeignKeyFilter
        elif f.choices:
            return ChoicesFilter
        else:
            type_ = f.get_internal_type()
            if type_ in ('DateField', 'DateTimeField'):
                return DateTimeFilter
            elif type_ in ('DecimalField', 'FloatField'):
                return NumericRangeFilter
            else:
                return ValuesFilter

    def setup_filters(self):
        filters = []
        for f in self.get_fields():
            klass = None
            opts = {} if self.defaults is None else dict(self.defaults)
            if isinstance(f, str):
                field_name = f
            else:
                opts.update(f[1])
                field_name = f[0]
                if len(f) > 2:
                    klass = f[2]
            if klass is None:
                klass = self.get_filter_for_field(field_name)
            filters.append(klass(field_name, self.model, self.params, **opts))
        return filters

    def make_title(self):
        if self.title_fields is None:
            title_fields = [filter_.field for filter_ in self.filters]
        else:
            title_fields = self.title_fields
        return u", ".join(c.label
                          for f in title_fields
                          for c in self.get_filter_choices(f)
                          if c.link_type == FILTER_REMOVE)

    def __str__(self):
        return self.render()
