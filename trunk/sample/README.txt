Here's a sample shell to see how to get going

# this is with no database present

mtrier@michael-triers-computer:~/Development/django-sqlalchemy/sample$ ./manage.py shell
Python 2.5.1 (r251:54863, Jan 17 2008, 19:35:17) 
[GCC 4.0.1 (Apple Inc. build 5465)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from django_sqlalchemy.models import *
>>> setup_all()
>>> create_all()
>>> from foo.models import Category
>>> c = Category(name='Empty')
>>> session.flush()
/Library/Python/2.5/site-packages/SQLAlchemy-0.4.2p3-py2.5.egg/sqlalchemy/types.py:372: RuntimeWarning: Unicode type received non-unicode bind param value 'Empty'
  warnings.warn(RuntimeWarning("Unicode type received non-unicode bind param value %r" % value))
>>> c
<Category: Category>
>>> c.name
'Empty'
>>> ^D


# this is after the database exists

mtrier@michael-triers-computer:~/Development/django-sqlalchemy/sample$ ./manage.py shell
Python 2.5.1 (r251:54863, Jan 17 2008, 19:35:17) 
[GCC 4.0.1 (Apple Inc. build 5465)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from django_sqlalchemy.models import *
>>> setup_all()
>>> from foo.models import Category
>>> c = Category.query.all()
>>> c
[<Category: Category>]
>>> c = Category.query.one()
>>> c
<Category: Category>
>>> c.name
u'Empty'
>>> c.created_at
datetime.datetime(2008, 3, 4, 19, 45, 28, 442492)
