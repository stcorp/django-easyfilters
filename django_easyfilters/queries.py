from collections import OrderedDict

from django.db.models import Count
from django.db.models.functions import Trunc


def date_aggregation(qs, fieldname, kind):
    """
    Performs an aggregation for a supplied DateQuerySet
    """
    result = qs.annotate(truncdate=Trunc(fieldname, kind)).values('truncdate').annotate(count=Count('pk')).order_by('truncdate')
    return [(x['truncdate'], x['count']) for x in result if x['truncdate'] is not None]


def value_counts(qs, fieldname):
    """
    Performs a simple query returning the count of each value of
    the field 'fieldname' in the QuerySet, returning the results
    as a OrderedDict of value: count
    """
    values_counts = qs.filter(**{
        fieldname+"__isnull": False
    }).values_list(fieldname)\
        .order_by(fieldname)\
        .annotate(Count(fieldname))
    count_dict = OrderedDict()
    null_count = qs.filter(**{fieldname+"__isnull": True}).count()
    if null_count:
        count_dict[None] = null_count
    for val, count in values_counts:
        count_dict[val] = count
    return count_dict


def numeric_range_counts(qs, fieldname, ranges):
    clause = ''.join(['CASE '] +
                     ['WHEN %s > %s AND %s <= %s THEN %s '
                      % (fieldname, val[0], fieldname, val[1], i)
                      for i, val in enumerate(ranges)] +
                     # An inclusive lower limit for the first item in ranges:
                     ['WHEN %s = %s THEN 0 ' % (fieldname, ranges[0][0])] +
                     ['ELSE %s END ' % len(ranges)])
    results = qs.extra(select={'rangefield': clause}).values('rangefield').annotate(count=Count('pk')).order_by('rangefield')
    count_dict = OrderedDict()
    for item in results:
        try:
            r = ranges[item['rangefield']]
        except IndexError:
            # Include in the top range - this could be a rounding error
            r = ranges[-1]
        count_dict[r] = item['count']
    return count_dict

