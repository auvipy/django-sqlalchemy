from django.conf import settings
from django.db.backends import BaseDatabaseWrapper, \
    BaseDatabaseFeatures, BaseDatabaseOperations
#from djalchemy.backend.query import QuerySetMixin

try:
    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.sql import operators
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading sqlalchemy module: %s" % e)

from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(settings.DJANGO_SQLALCHEMY_DBURI)
Session = scoped_session(
    sessionmaker(
        bind=engine, transactional=True)
)

session = Session()

# default metadata
metadata = MetaData(bind=engine)

if getattr(settings, 'DJANGO_SQLALCHEMY_ECHO'):
    metadata.bind.echo = settings.DJANGO_SQLALCHEMY_ECHO

DatabaseError = Exception
IntegrityError = Exception


class DatabaseFeatures(BaseDatabaseFeatures):
    uses_custom_queryset = True


class DatabaseOperations(BaseDatabaseOperations):
    def quote_name(self, name):
        return metadata.bind.dialect.identifier_preparer.quote_identifier(name)

    def query_set_class(self, DefaultQuerySet):
        from djalchemy.backend.utils import parse_filter

        class SqlAlchemyQuerySet(DefaultQuerySet):
            """
            A SqlAlchemy implementation of the Django QuerySet class
            """
            def __init__(self, model=None, query=None):
                self.model = model
                self.query = query or self.model.query

            def __and__(self, other):
                combined = self._clone()
                combined.query.combine(other.query, sql.AND)
                return combined

            def __or__(self, other):
                combined = self._clone()
                combined.query.combine(other.query, sql.OR)
                return combined

            def __repr__(self):
                return repr(self.query.all())

            def __len__(self):
                return self.query.count()

            def __iter__(self):
                return iter(self.query)

            def __getitem__(self, k):
                return self.query.__getitem__(k)

            ####################################
            # METHODS THAT DO DATABASE QUERIES #
            ####################################

            def iterator(self):
                """
                An iterator over the results from applying this QuerySet to the
                database.
                """
                return iter(self.query)

            def count(self):
                """
                Performs a SELECT COUNT() and returns the number of records as an
                integer.

                If the queryset is already cached (i.e. self._result_cache is set) this
                simply returns the length of the cached results set to avoid multiple
                SELECT COUNT(*) calls.
                """
                return self.query.count()

            def get(self, *args, **kwargs):
                """
                Performs the query and returns a single object matching the given
                keyword arguments.
                """
                return self.filter(*args, **kwargs).one()

            def create(self, **kwargs):
                """
                Create a new object with the given kwargs, saving it to the database
                and returning the created object.
                """
                obj = self.model(**kwargs)
                obj.save()
                return obj

            def get_or_create(self, **kwargs):
                """
                Looks up an object with the given kwargs, creating one if necessary.
                Returns a tuple of (object, created), where created is a boolean
                specifying whether an object was created.
                """
                assert kwargs, \
                        'get_or_create() must be passed at least one keyword argument'
                defaults = kwargs.pop('defaults', {})
                try:
                    return self.get(**kwargs), False
                except self.model.DoesNotExist:
                    params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
                    params.update(defaults)
                    obj = self.model(**params)
                    obj.save()
                    return obj, True

            def latest(self, field_name=None):
                """
                Returns the latest object, according to the model's 'get_latest_by'
                option or optional given field_name.
                """
                latest_by = field_name or self.model._meta.get_latest_by
                assert bool(latest_by), "latest() requires either a field_name parameter or 'get_latest_by' in the model"
                return self.query.order_by('-%s' % latest_by).one()

            def in_bulk(self, id_list):
                """
                TODO:need to map
                Returns a dictionary mapping each of the given IDs to the object with
                that ID.
                """
                assert isinstance(id_list, (tuple, list)), \
                        "in_bulk() must be provided with a list of IDs."
                if not id_list:
                    return {}
                self.query = self.query.filter('pk__in', id_list)
                return dict([(obj._get_pk_val(), obj) for obj in self.query])

            def delete(self):
                """
                Deletes the records in the current QuerySet.
                """
                self.query.session.delete(self.query)
            delete.alters_data = True

            def update(self, **kwargs):
                """
                TODO:need to map
                Updates all elements in the current QuerySet, setting all the given
                fields to the appropriate values.
                """
                query = self.query.clone(sql.UpdateQuery)
                query.add_update_values(kwargs)
                query.execute_sql(None)
                self._result_cache = None
            update.alters_data = True

            ##################################################
            # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
            ##################################################

            def values(self, *fields):
                """
                TODO:need to map
                """
                # >>> b = a.from_statement(select([Category.c.name]))
                # >>> print b
                # SELECT foo_category.name AS foo_category_name 
                # FROM foo_category
                # >>> 
                return self._clone(klass=ValuesQuerySet, setup=True, _fields=fields)

            def valueslist(self, *fields, **kwargs):
                """
                TODO:need to map
                """
                flat = kwargs.pop('flat', False)
                if kwargs:
                    raise TypeError('Unexpected keyword arguments to valueslist: %s'
                            % (kwargs.keys(),))
                if flat and len(fields) > 1:
                    raise TypeError("'flat' is not valid when valueslist is called with more than one field.")
                return self._clone(klass=ValuesListQuerySet, setup=True, flat=flat,
                        _fields=fields)

            def dates(self, field_name, kind, order='ASC'):
                """
                TODO:need to map
                Returns a list of datetime objects representing all available dates
                for the given field_name, scoped to 'kind'.
                """
                assert kind in ("month", "year", "day"), \
                        "'kind' must be one of 'year', 'month' or 'day'."
                assert order in ('ASC', 'DESC'), \
                        "'order' must be either 'ASC' or 'DESC'."
                # Let the FieldDoesNotExist exception propagate.
                field = self.model._meta.get_field(field_name, many_to_many=False)
                assert isinstance(field, DateField), "%r isn't a DateField." \
                        % field_name
                return self._clone(klass=DateQuerySet, setup=True, _field=field,
                        _kind=kind, _order=order)

            ##################################################################
            # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
            ##################################################################

            def all(self):
                """
                Returns a new QuerySet that is a copy of the current one. This allows a
                QuerySet to proxy for a model manager in some cases.
                """
                return self._clone()

            def filter(self, *args, **kwargs):
                """
                Returns a new QuerySet instance with the args ANDed to the existing
                set.
                """
                return self._filter_or_exclude(False, *args, **kwargs)

            def exclude(self, *args, **kwargs):
                """
                Returns a new QuerySet instance with NOT (args) ANDed to the existing
                set.
                """
                return self._filter_or_exclude(True, *args, **kwargs)

            def _filter_or_exclude(self, exclude, *args, **kwargs):
                return parse_filter(self, exclude, **kwargs)

            def complex_filter(self, filter_obj):
                """
                TODO:need to map
                Returns a new QuerySet instance with filter_obj added to the filters.
                filter_obj can be a Q object (or anything with an add_to_query()
                method) or a dictionary of keyword lookup arguments.

                This exists to support framework features such as 'limit_choices_to',
                and usually it will be more natural to use other methods.
                """
                if isinstance(filter_obj, Q) or hasattr(filter_obj, 'add_to_query'):
                    return self._filter_or_exclude(None, filter_obj)
                else:
                    return self._filter_or_exclude(None, **filter_obj)

            def select_related(self, *fields, **kwargs):
                """
                TODO:need to map
                Returns a new QuerySet instance that will select related objects. If
                fields are specified, they must be ForeignKey fields and only those
                related objects are included in the selection.
                """
                depth = kwargs.pop('depth', 0)
                # TODO: Remove this? select_related(False) isn't really useful.
                true_or_false = kwargs.pop('true_or_false', True)
                if kwargs:
                    raise TypeError('Unexpected keyword arguments to select_related: %s'
                            % (kwargs.keys(),))
                obj = self._clone()
                if fields:
                    if depth:
                        raise TypeError('Cannot pass both "depth" and fields to select_related()')
                    obj.query.add_select_related(fields)
                else:
                    obj.query.select_related = true_or_false
                if depth:
                    obj.query.max_depth = depth
                return obj

            def order_by(self, *field_names):
                """
                TODO:need to map
                Returns a new QuerySet instance with the ordering changed.
                """
                for order in field_names:
                    desc = False
                    if order[0] == "-":
                        desc = True
                        order = order[1:]
                    if "." in order:
                        table, field = order.split(".")
                        # rel_name = cls.DjangoAlchemy._related_objects[table_model[table]]
                        # o = getattr(table_model[table].DjangoAlchemy.c, field)
                        query = query.join(rel_name)
                    else:
                        o = getattr(self.model.c, order)

                    if desc:
                        from sqlalchemy import desc
                        query = query.order_by(desc(o))
                    else:
                        query = query.order_by(o)        
                return query

            def distinct(self, true_or_false=True):
                """
                Returns a new QuerySet instance that will select only distinct results.
                """
                clone = self._clone()
                clone.query._distinct = true_or_false
                return clone

            def extra(
                self, select=None, where=None, params=None, tables=None, order_by=None):
                """
                TODO:need to map
                Add extra SQL fragments to the query.
                """
                assert self.query.can_filter(), \
                        "Cannot change a query once a slice has been taken"
                clone = self._clone()
                if select:
                    clone.query.extra_select.update(select)
                if where:
                    clone.query.extra_where.extend(where)
                if params:
                    clone.query.extra_params.extend(params)
                if tables:
                    clone.query.extra_tables.extend(tables)
                if order_by:
                    clone.query.extra_order_by = order_by
                return clone

            def reverse(self):
                """
                Reverses the ordering of the queryset.
                """
                clone = self._clone()
                for field in clone.query._order_by:
                    if field.modifier == operators.desc_op:
                        field.modifier = operators.asc_op
                    else:
                        field.modifier = operators.desc_op
                return clone

            ###################
            # PRIVATE METHODS #
            ###################

            def _clone(self, klass=None, setup=False, **kwargs):
                if klass is None:
                    klass = self.__class__
                c = klass(model=self.model, query=self.query._clone())
                c.__dict__.update(kwargs)
                if setup and hasattr(c, '_setup_query'):
                    c._setup_query()
                return c

            def _fill_cache(self, num=None):
                """
                Fills the result cache with 'num' more entries (or
                until the results iterator is exhausted).
                """
                if self._iter:
                    try:
                        for i in range(num or ITER_CHUNK_SIZE):
                            self._result_cache.append(self._iter.next())
                    except StopIteration:
                        self._iter = None

            def _insert(self, _return_id=False, _raw_values=False, **kwargs):
                """
                Inserts a new record for the given model. This provides an
                interface to the InsertQuery class and is how Model.save()
                is implemented. It is not part of the public API of QuerySet,
                though.
                """
                print "howdy"
            _insert.alters_data = True
        return SqlAlchemyQuerySet


class ConnectionProxy:
    """
    Provides a proxy between what Django expects as a connection and SQLAlchemy
    """
    def __init__(self, session, connection):
        pass


class DatabaseWrapper(BaseDatabaseWrapper):
    features = DatabaseFeatures()
    ops = DatabaseOperations()

    def _cursor(self, settings):
        from sqlalchemy.databases.sqlite import SQLiteDialect
        conn = session.connection()
        kwargs = {}
        if isinstance(conn.engine.dialect, SQLiteDialect,):
            from django.db.backends.sqlite3.base import SQLiteCursorWrapper
            kwargs['factory'] = SQLiteCursorWrapper
        return conn.connection.cursor(**kwargs)
