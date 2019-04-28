[![Join the chat at https://gitter.im/django-sqlalchemy/Lobby](https://badges.gitter.im/django-sqlalchemy/Lobby.svg)](https://gitter.im/django-sqlalchemy/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

** Warning: This project is in early design decision stage. you can participate on development process **

The end goal of this project is to build the django ORM on top of SQLalchemy core so that, existing django apps can easily migrate from current ORM of django to SQLalchemy based django ORM with almost no change or as little change as possible.

## Motivation: https://rixx.de/blog/djangocon-europe-2019-how-and-why-to-build-a-django-based-project-with-sqlalchemy-core-for-data-analysis/

# django-sqlalchemy

A common request over the entire life of Django has been to use Django's forms (and in particular, Django's Admin) with data stores that aren't Django's ORM. SQLAlchemy is a popular choice for those using SQL databases. With the formalization of django Meta API it is now possible to use that formalize API for interfacing with
other non-django-orm data stores. 


The django-sqlalchemy project aims to work as a seamless integrating of SQLAlchemy with django web framework.
Long term goal of this project is to become a drop in replacement for django ORM and all the
parts of django should be able to use SQLalchemy easily as they use django ORM today.


To acheive the goal, need all nuts and bolts to make sqlalchemy work well with django. Integration with
different django features working with sqlalchemy Like management commands, django Meta compliant layer
to interface with django forms/modelforms + Admin panel + Signals etc.



## Brief Architectural overview of SQLAlchemy in contrast to django ORM
* The first one is : SQLAlchemy is a deeply layered system, whereas Django's ORM is basically just one layer which is the ORM. In SQLAlchemy you have at the very bottom the engine which with abstracts away connection pools and basic API differences between different databases, on top of that you have the SQL abstraction language, sitting on top of that and the table definitions you have the basic ORM and on top of that you have the declarative ORM which looks very close to the Django ORM.
* Django's ORM is basically quite simple. Each time you do any query it generates a SQL expression for you and sends a query to the database. Then it constructs an object for you. That object can be modified and if you call save() on it, it will update the record in the database with the new values of the attributes. In SQLAlchemy there is an object called the “session” and it basically encapsulates a transaction. Each object is tracked by primary key in this session. As such each object only exists once by primary key. As such you can safely make a lot of queries and you never have things out of sync. When you commit the session it will send all changes at once to the database in correct order, if you rollback the session nothing happens instead.


## Proposed solutions and Implementation design specification

As the goal of this project is to create an alternative drop in replacement of django ORM to make sqlalchemy work almost natively on django apps, migrations, forms, modelforms, Admin, contenttyps, signals so the SQLalchemy core should be mapped with django Models properly.

### Django-sqlalchmey package specific
1. Basic glues for working well with django application as SQLAlchemy relies on global state for a few things:

* A MetaData instance which tracks all known SQL tables.
* A base class for all models using the ORM.
* A session factory.
Every application using SQLAlchemy must provides its own instance of these. This makes it hard to create add-on packages that also use SQLAlchemy, since they either need to have their own SQLAlchemy state, which makes it hard to integrate them into application, or they need to jump through multiple complex hoops to allow them share state with application.
2. Django compatible settings for SQLalchemy package
3. Django derived db management commands for handling django-SQLalchemy
4. Migration Hnadling of the django-alchemy package. For that we have thre options:
* use alembic to handle migrations much like flask-migrate
* use sqlalchmey-migrate which is inspired by ruby-on-rails
* use django's build in migration to handle sqlalchemy migrations[might need to improve django migrations too]
 I will use the django built in migration framework to detect the change of sqlalchemy schema migrations. Though the migration framework is tightly coupled with django ORM we need to refactor and map the django model with SQLalchemy core to 

3. Django model Meta API compliant layer to expose sqlalchemy table definitions on django forms/modelforms and admin app
4. Work Properly with django ContentTypes
5. Work properly with Django GIS
6. Work well with signals

### Refactor django internals 
The meta API used by admin and model forms should be completely public 
and stable. The problem is some methods of the meta API return 
field instances, and the API for the fields (especially for related 
fields) isn't public nor stable. For that reason works needed to be done to make the related field API stable.

from https://code.djangoproject.com/ticket/24317 
* Problems:
 when using get_fields(), it'll return either a field.rel instance (for reverse side of user defined fields), or a real field instance (for example ForeignKey). These behave differently, so that the user must always remember which one he is dealing with. This creates lots of non-necessary conditioning in multiple places of Django.
For example, the select_related descent has one branch for descending foreign keys and one to one fields, and another branch for descending to reverse one to one fields. Conceptually both one to one and reverse one to one fields are very similar, so this complication is non-necessary.

So the idea is to deprecate field.rel, and instead add field.remote_field. The remote_field is just a field subclass, just like everything else in Django.

* The benefits are:
Conceptual simplicity - dealing with fields and rels is non-necessary, and confusing. Everything from get_fields() should be a field.
Code simplicity - no special casing based on if a given relation is described by a rel or not
Code reuse - ReverseManyToManyField is in most regard exactly like ManyToManyField
The expected problems are mostly from 3rd party code. Users of _meta that already work on expectation of getting rel instances will likely need updating. Those users who subclass Django's fields (or duck-type Django's fields) will need updating. Examples of such projects include django-rest-framework and django-taggit.


## Open Questions on Design specification and implementation
* migration handling[django built in migration/alembic]
* system checks
* sqlalchemy core, orm and declarative extention
