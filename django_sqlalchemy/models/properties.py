'''
This module provides support for defining properties on your entities. It both
provides, the `Property` class which acts as a building block for common 
properties such as fields and relationships (for those, please consult the 
corresponding modules), but also provides some more specialized properties, 
such as `ColumnProperty`. It also provides the GenericProperty class which 
allows you to wrap any SQLAlchemy property, and its DSL-syntax equivalent: 
has_property_.

`has_property`
--------------
The ``has_property`` statement allows you to define properties which rely on 
their entity's table (and columns) being defined before they can be declared
themselves. The `has_property` statement takes two arguments: first the name of
the property to be defined and second a function (often given as an anonymous
lambda) taking one argument and returning the desired SQLAlchemy property. That
function will be called whenever the entity table is completely defined, and
will be given the .c attribute of the entity as argument (as a way to access 
the entity columns).

Here is a quick example of how to use ``has_property``.

.. sourcecode:: python

    class OrderLine(Entity):
        has_field('quantity', Float)
        has_field('unit_price', Float)
        has_property('price', 
                     lambda c: column_property(
                         (c.quantity * c.unit_price).label('price')))
'''

from django_sqlalchemy.models.statements import PropertyStatement
from sqlalchemy.orm import column_property

__doc_all__ = ['EntityBuilder', 'Property', 'GenericProperty', 
               'ColumnProperty']

class EntityBuilder(object):
    '''
    Abstract base class for all entity builders. An Entity builder is a class 
    of objects which can be added to an Entity (usually by using special 
    properties or statements) to "build" that entity. Building an entity,
    meaning to add columns to its "main" table, create other tables, add
    properties to its mapper, ... To do so an EntityBuilder must override the
    corresponding method(s). This is to ensure the different operations happen
    in the correct order (for example, that the table is fully created before
    the mapper that use it is defined).
    '''
    #XXX: add helper methods: add_property, etc... here?
    # either in addition to in EntityDescriptor or instead of there.
    def create_pk_cols(self):
        pass

    def create_non_pk_cols(self):
        pass

    def before_table(self):
        pass

    def create_tables(self):
        pass

    def after_table(self):
        pass

    def create_properties(self):
        pass    

    def before_mapper(self):
        pass    

    def after_mapper(self):
        pass    

    def finalize(self):
        pass    


class CounterMeta(type):
    '''
    A simple meta class which adds a ``_counter`` attribute to the instances of
    the classes it is used on. This counter is simply incremented for each new
    instance.
    '''
    counter = 0

    def __call__(self, *args, **kwargs):
        instance = type.__call__(self, *args, **kwargs)
        instance._counter = CounterMeta.counter
        CounterMeta.counter += 1
        return instance

class Counter(object):
    _counter = 0
    def __init__(self, *args, **kwargs):
        Counter._counter += 1

class Property(EntityBuilder, Counter):
    '''
    Abstract base class for all properties of an Entity.
    '''
    
    def __init__(self, *args, **kwargs):
        self.entity = None
        self.name = None
        super(Property, self).__init__(*args, **kwargs)
    
    def attach(self, entity, name):
        """Attach this property to its entity, using 'name' as name.

        Properties will be attached in the order they were declared.
        """
        self.entity = entity
        self.name = name

        # register this property as a builder
        entity._descriptor.builders.append(self)

        # delete the original attribute so that it doesn't interfere with
        # SQLAlchemy.
        if hasattr(entity, name):
            delattr(entity, name)

    def __repr__(self):
        return "Property(%s, %s)" % (self.name, self.entity)


class GenericProperty(Property):
    '''
    Generic catch-all class to wrap an SQLAlchemy property.

    .. sourcecode:: python

        class OrderLine(Entity):
            quantity = Field(Float)
            unit_price = Field(Numeric)
            price = GenericProperty(lambda c: column_property(
                             (c.quantity * c.unit_price).label('price')))
    '''
    
    def __init__(self, prop):
        super(GenericProperty, self).__init__()
        self.prop = prop

    def create_properties(self):
        if callable(self.prop):
            prop_value = self.prop(self.entity.table.c)
        else:
            prop_value = self.prop
        prop_value = self.evaluate_property(prop_value)
        self.entity._descriptor.add_property(self.name, prop_value)

    def evaluate_property(self, prop):
        return prop

class ColumnProperty(GenericProperty):
    '''
    A specialized form of the GenericProperty to generate SQLAlchemy 
    ``column_property``'s. 
    
    It takes a single argument, which is a function (often 
    given as an anonymous lambda) taking one argument and returning the 
    desired (scalar-returning) SQLAlchemy ClauseElement. That function will be
    called whenever the entity table is completely defined, and will be given 
    the .c attribute of the entity as argument (as a way to access the entity 
    columns). The ColumnProperty will first wrap your ClauseElement in a label
    with the same name as the property, then wrap that in a column_property.

    .. sourcecode:: python

        class OrderLine(Entity):
            quantity = Field(Float)
            unit_price = Field(Numeric)
            price = ColumnProperty(lambda c: c.quantity * c.unit_price)

    Please look at the `corresponding SQLAlchemy 
    documentation <http://www.sqlalchemy.org/docs/04/mappers.html
    #advdatamapping_mapper_expressions>`_ for details.
    '''

    def evaluate_property(self, prop):
        return column_property(prop.label(self.name))

# class Composite(GenericProperty):
#    def __init__(self, prop):
#        super(GenericProperty, self).__init__()
#        self.prop = prop
# 
#    def evaluate_property(self, prop):
#        return composite(prop.label(self.name))
# 
# start = Composite(Point, lambda c: (c.x1, c.y1))
# 
# mapper(Vertex, vertices, properties={
#    'start':composite(Point, vertices.c.x1, vertices.c.y1),
#    'end':composite(Point, vertices.c.x2, vertices.c.y2)
# })


has_property = PropertyStatement(GenericProperty)

