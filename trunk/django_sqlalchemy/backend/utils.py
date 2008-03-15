from django.db.models.sql.constants import *
from django.core.exceptions import FieldError

QUERY_TERMS_MAPPING = {
    'exact': '__eq__(%s)', 
    'iexact': '__eq__(%s)', 
    'contains': 'like("%%%s%%")', 
    'icontains': 'like("%%%s%%")',
    'gt': '__gt__(%s)', 
    'gte': '__gte__(%s)', 
    'lt': '__lt__(%s)', 
    'lte': '__lte__(%s)', 
    'in': 'in(%s)',
    'startswith': 'like("%s%%")', 
    'istartswith': 'like("%s%%")', 
    'endswith': 'like("%%%s")', 
    'iendswith': 'like("%%%s")',
    'range': 'between(%s, %s)', 
    'year': None, 
    'month': None, 
    'day': None, 
    'isnull': '__eq__(None)', 
    'search': None,
    'regex': None, 
    'iregex': None,
}

def parse_filter(model, exclude, **kwargs):
    """
    Add a single filter to the query. The 'filter_expr' is a pair:
    (filter_string, value). E.g. ('name__contains', 'fred')
    
    If 'negate' is True, this is an exclude() filter. If 'trim' is True, we
    automatically trim the final join group (used internally when
    constructing nested queries).
    """
    query = model.query._clone()
    
    for filter_expr in [(k, v) for k, v in kwargs.items()]:
        arg, value = filter_expr
        parts = arg.split(LOOKUP_SEP)
        if not parts:
            raise FieldError("Cannot parse keyword query %r" % arg)
    
        # Work out the lookup type and remove it from 'parts', if necessary.
        if len(parts) == 1 or parts[-1] not in QUERY_TERMS_MAPPING:
            lookup_type = 'exact'
        else:
            lookup_type = parts.pop()

        # Interpret '__exact=None' as the sql 'is NULL'; otherwise, reject all
        # uses of None as a query value.
        if value is None:
            if lookup_type != 'exact':
                raise ValueError("Cannot use None as a query value")
            lookup_type = 'isnull'
            value = True
        elif callable(value):
            value = value()
        
        if isinstance(value, basestring) and lookup_type not in ('contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith'):
            value = '"%s"' % value
        q = "model.c." + ".".join(parts) + "." + (QUERY_TERMS_MAPPING[lookup_type] % value)
        if exclude:
            q = "~(%s)" % q
        query = query.filter(eval(q))
    return query