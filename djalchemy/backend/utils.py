import operator

from django.db.models.sql.constants import *
from django.core.exceptions import FieldError
from django.db.models.sql.constants import QUERY_TERMS
from django.utils.functional import curry

QUERY_TERMS_MAPPING = {
    'exact': operator.eq, 
    'iexact': operator.eq, 
    'gt': operator.gt, 
    'gte': operator.ge, 
    'lt': operator.lt, 
    'lte': operator.le
}

def lookup_query_expression(lookup_type, field, value):
    if lookup_type in QUERY_TERMS_MAPPING:
        return curry(QUERY_TERMS_MAPPING[lookup_type], field, value)
    elif lookup_type == 'contains':
        return curry(field.like, '%%%s%%' % value)
    elif lookup_type == 'icontains':
        return curry(field.ilike, '%%%s%%' % value)
    elif lookup_type == 'in':
        return curry(field.in_, value)
    elif lookup_type == 'startswith':        
        return curry(field.like, '%s%%' % value)
    elif lookup_type == 'istartswith':
        return curry(field.ilike, '%s%%' % value)
    elif lookup_type == 'endswith':
        return curry(field.like, '%%%s' % value)
    elif lookup_type == 'iendswith':
        return curry(field.ilike, '%%%s' % value)
    elif lookup_type == 'range':
        raise NotImplemented()
    elif lookup_type == 'year':        
        raise NotImplemented()
    elif lookup_type == 'month':
        raise NotImplemented()
    elif lookup_type == 'day':
        raise NotImplemented()
    elif lookup_type == 'search':
        raise NotImplemented()
    elif lookup_type == 'regex':
        raise NotImplemented()
    elif lookup_type == 'iregex':
        raise NotImplemented()
    elif lookup_type == 'isnull': 
        if value:
            return curry(operator.eq, field, None)
        else:
            return curry(operator.ne, field, None)
    else:
        return None
        
def parse_filter(queryset, exclude, **kwargs):
    """
    Add a single filter to the query. The 'filter_expr' is a pair:
    (filter_string, value). E.g. ('name__contains', 'fred')
    
    If 'negate' is True, this is an exclude() filter. If 'trim' is True, we
    automatically trim the final join group (used internally when
    constructing nested queries).
    """
    
    query = queryset._clone()
    
    for filter_expr in [(k, v) for k, v in kwargs.items()]:
        arg, value = filter_expr
        parts = [queryset.model] + arg.split(LOOKUP_SEP)
        if not parts:
            raise FieldError("Cannot parse keyword query %r" % arg)
    
        # Work out the lookup type and remove it from 'parts', if necessary.
        if len(parts) == 1 or parts[-1] not in QUERY_TERMS:
            lookup_type = 'exact'
        else:
            lookup_type = parts.pop()
                
        if callable(value):
            value = value()
        
        field = reduce(lambda x, y: getattr(x, y), parts)
    
        op = lookup_query_expression(lookup_type, field, value)
        expression = op()
        
        if exclude:
            expression = ~(expression)
        query.query = query.query.filter(expression)
    return query