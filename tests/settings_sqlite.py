
DEBUG = TEMPLATE_DEBUG = True

DATABASE_ENGINE = 'djlalchemy'
DATABASE_NAME = ''
DJANGO_SQLALCHEMY_DBURI = "sqlite:///testing.db"
DJANGO_SQLALCHEMY_ECHO = False

INSTALLED_APPS = (
    'django_sqlalchemy',
    'regression.sample_app',
    'regression.norelations',
    )


