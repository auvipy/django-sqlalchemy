# django-sqlalchemy
Experimental project on supporting SQL Alchemy to django orm

roadmap for development of the django-sqlalchemy project.

Introduction
Development for the django-sqlalchemy project is broken down in three primary areas:

Management Commands - overriding these, like syncdb, to pass off functionality to SQLAlchemy
Declarative Mapper - mapping the Django model structure into SQLAlchemy Table and Mapper information so that access to SA is available while still providing access to all of Django's expectations for functionality of a model.
QuerySet Mapping - Map the backend django-sqlalchemy database so that we can override Django's QuerySet into a SqlAlchemyQuerySet that interprets and passes on all backend query functionality to SA. This includes the handing of sessions, metadata, and transactions.
The detailed scope of work is defined in the detail section for each of the above areas.

Details
Management Commands
The following management commands need to be overridden and replaced with SQLAlchemy versions:

syncdb - This needs to be mapped to the setup_all() method for SQLAlchemy which will do the right thing and create the appropriate tables. Since SQLAlchemy handles table creation in the same manner as Django (i.e. only creating the tables if not already present) this mapping shouldn't be too complicated.
sql - This is mapped to SA so that SA provides the sql create syntax. We need to investigate colorization down the road so the "user experience" is similar to Django.
Declarative Mapper
Basic Models - The basics for the declarative mapping are already in place and working properly.
Fields - All of the current base fields are mapped to their Django equivalent, although many are untested. We still need to get the related fields: ForeignKey, ManyToManyField, and OneToOneField mapped correctly. There's been some work in this area.
Polymorphic - We also need to look at mapping in Polymorphic structures: Multi-Table Inheritance and Abstract Base Classes. Intermediate Models will not be far behind so those will need to be looked at as well.
SA Enhancements - As we begin testing we're sure to identify areas that need to be further explored. One area for greater functionality down the road is to expose more of the SA abilities within our mapped model.
QuerySet Mapping
SqlAlchemyQuerySet Class - All items in the QuerySet class need to be mapped to the appropriate method on the SA Query class. Currently this is partially complete and all items with TODO in them still need to be investigated and mapped.
Transaction Support - Transaction support that Django makes through it's TransactionMiddleware needs to be mapped into appropriate SA calls.
Tests
A lot of the initial work on django-sqlalchemy was more exploratory in nature, in order to determine the appropriate roadmap for implementation. At this point that roadmap is pretty clear, although certain details will only be know as we run into issues. (We don't know what we don't know.) It is proper at this time to begin fleshing out the testing of the implementation to provide coverage for the functionality already implemented.
