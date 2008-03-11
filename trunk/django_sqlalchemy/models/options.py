'''
This module provides support for defining several options on your Elixir
entities.  There are three different kinds of options that can be set 
up, and for this there are three different statements: using_options_,
using_table_options_ and using_mapper_options_.

Alternatively, these options can be set on all Elixir entities by modifying 
the `options_defaults` dictionary before defining any entity.

`using_options`
---------------
The 'using_options' DSL statement allows you to set up some additional
behaviors on your model objects, including table names, ordering, and
more.  To specify an option, simply supply the option as a keyword 
argument onto the statement, as follows:

.. sourcecode:: python

    class Person(Entity):
        name = Field(Unicode(64))

        using_options(shortnames=True, order_by='name')

The list of supported arguments are as follows:

+---------------------+-------------------------------------------------------+
| Option Name         | Description                                           |
+=====================+=======================================================+
| ``inheritance``     | Specify the type of inheritance this entity must use. |
|                     | It can be one of ``single`` or ``multi``. Defaults to |
|                     | ``single``. Concrete inheritance is currently not in  |
|                     | a usable state.                                       |
+---------------------+-------------------------------------------------------+
| ``polymorphic``     | Whether the inheritance should be polymorphic or not. |
|                     | Defaults to ``True``.                                 |
+---------------------+-------------------------------------------------------+
| ``metadata``        | Specify a custom MetaData for this entity.            |
|                     | By default, entities uses the global                  |
|                     | ``django_sqlalchemy.models.metadata``.                                  |
|                     | This option can also be set for all entities of a     |
|                     | module by setting the ``__metadata__`` attribute of   |
|                     | that module.                                          |
+---------------------+-------------------------------------------------------+
| ``autoload``        | Automatically load column definitions from the        |
|                     | existing database table.                              |
+---------------------+-------------------------------------------------------+
| ``tablename``       | Specify a custom tablename. You can either provide a  |
|                     | plain string or a callable. The callable will be      |
|                     | given the entity (ie class) as argument and must      |
|                     | return a string representing the name of the table    |
|                     | for that entity.                                      |
+---------------------+-------------------------------------------------------+
| ``shortnames``      | Usually tablenames include the full module-path       |
|                     | to the entity, but lower-cased and separated by       |
|                     | underscores ("_"), eg.: "project1_model_myentity"     |
|                     | for an entity named "MyEntity" in the module          |
|                     | "project1.model".  If shortnames is ``True``, the     |
|                     | tablename will just be the entity's classname         |
|                     | lower-cased, ie. "myentity".                          |
+---------------------+-------------------------------------------------------+
| ``auto_primarykey`` | If given as string, it will represent the             |
|                     | auto-primary-key's column name.  If this option       |
|                     | is True, it will allow auto-creation of a primary     |
|                     | key if there's no primary key defined for the         |
|                     | corresponding entity.  If this option is False,       |
|                     | it will disallow auto-creation of a primary key.      |
+---------------------+-------------------------------------------------------+
| ``version_id_col``  | If this option is True, it will create a version      |
|                     | column automatically using the default name. If given |
|                     | as string, it will create the column using that name. |
|                     | This can be used to prevent concurrent modifications  |
|                     | to the entity's table rows (i.e. it will raise an     |
|                     | exception if it happens).                             |
+---------------------+-------------------------------------------------------+
| ``order_by``        | How to order select results. Either a string or a     |
|                     | list of strings, composed of the field name,          |
|                     | optionally lead by a minus (for descending order).    |
+---------------------+-------------------------------------------------------+
| ``session``         | Specify a custom contextual session for this entity.  |
|                     | By default, entities uses the global                  |
|                     | ``django_sqlalchemy.models.session``.                                   |
|                     | This option accepts Objectstore                       |
|                     | (found in Elixir and ActiveMapper), SessionContext    |
|                     | (found in SQLAlchemy 0.3) or ScopedSession (found in  |
|                     | SQLAlchemy 0.4) objects. It also supports ``None``,   |
|                     | in which case your entity will be mapped using a      |
|                     | non-contextual mapper. This option can also be set    |
|                     | for all entities of a module via by setting the       |
|                     | ``__session__`` attribute of that module.             |
+---------------------+-------------------------------------------------------+
| ``autosetup``       | Specify whether that entity will contain automatic    |
|                     | setup triggers. That is if this entity will be        |
|                     | automatically setup (along with all other entities    |
|                     | which were already declared) if any of the following  |
|                     | condition happen: some of its attributes are accessed |
|                     | ('c', 'table', 'mapper' or 'query'), instanciated     |
|                     | (called) or the create_all method of this entity's    |
|                     | metadata is called. Defaults to ``False``.            |
+---------------------+-------------------------------------------------------+
| ``allowcoloverride``| Specify whether it is allowed to override columns.    |
|                     | By default, Elixir forbids you to add a column to an  |
|                     | entity's table which already exist in that table. If  |
|                     | you set this option to ``True`` it will skip that     |
|                     | check. Use with care as it is easy to shoot oneself   |
|                     | in the foot when overriding columns.                  |
+---------------------+-------------------------------------------------------+


For examples, please refer to the examples and unit tests.

`using_table_options`
---------------------
The 'using_table_options' DSL statement allows you to set up some 
additional options on your entity table. It is meant only to handle the 
options which are not supported directly by the 'using_options' statement.
By opposition to the 'using_options' statement, these options are passed 
directly to the underlying SQLAlchemy Table object (both non-keyword arguments
and keyword arguments) without any processing.

For further information, please refer to the `SQLAlchemy table's documentation
<http://www.sqlalchemy.org/docs/04/sqlalchemy_schema.html
#docstrings_sqlalchemy.schema_Table>`_.

You might also be interested in the section about `constraints 
<http://www.sqlalchemy.org/docs/04/metadata.html#metadata_constraints>`_.

`using_mapper_options`
----------------------
The 'using_mapper_options' DSL statement allows you to set up some 
additional options on your entity mapper. It is meant only to handle the 
options which are not supported directly by the 'using_options' statement.
By opposition to the 'using_options' statement, these options are passed 
directly to the underlying SQLAlchemy mapper (as keyword arguments) 
without any processing.

For further information, please refer to the `SQLAlchemy mapper 
function's documentation 
<http://www.sqlalchemy.org/docs/04/sqlalchemy_orm.html
#docstrings_sqlalchemy.orm_modfunc_mapper>`_.
'''

from django_sqlalchemy.models.statements import ClassMutator
from sqlalchemy import Integer, String

__doc_all__ = ['options_defaults']

# format constants
FKCOL_NAMEFORMAT = "%(relname)s_%(key)s"
M2MCOL_NAMEFORMAT = "%(tablename)s_%(key)s"
CONSTRAINT_NAMEFORMAT = "%(tablename)s_%(colnames)s_fk"

# other global constants
DEFAULT_AUTO_PRIMARYKEY_NAME = "id"
DEFAULT_AUTO_PRIMARYKEY_TYPE = Integer
DEFAULT_VERSION_ID_COL_NAME = "row_version"
DEFAULT_POLYMORPHIC_COL_NAME = "row_type"
POLYMORPHIC_COL_SIZE = 40
POLYMORPHIC_COL_TYPE = String(POLYMORPHIC_COL_SIZE)

# 
options_defaults = dict(
    autosetup=True,
    inheritance='single',
    polymorphic=True,
    autoload=False,
    tablename=None,
    shortnames=False,
    auto_primarykey=True,
    version_id_col=False,
    allowcoloverride=False,
    mapper_options=dict(),
    table_options=dict(),
)


valid_options = options_defaults.keys() + [
    'metadata',
    'session',
    'collection',
    'order_by',
]


def using_options_handler(entity, *args, **kwargs):
    for kwarg in kwargs:
        if kwarg in valid_options:
            setattr(entity._descriptor, kwarg, kwargs[kwarg])
        else:
            raise Exception("'%s' is not a valid option for django_sqlalchemy entities." 
                            % kwarg)


def using_table_options_handler(entity, *args, **kwargs):
    entity._descriptor.table_args = list(args)
    entity._descriptor.table_options.update(kwargs)


def using_mapper_options_handler(entity, *args, **kwargs):
    entity._descriptor.mapper_options.update(kwargs)


using_options = ClassMutator(using_options_handler)
using_table_options = ClassMutator(using_table_options_handler)
using_mapper_options = ClassMutator(using_mapper_options_handler)
