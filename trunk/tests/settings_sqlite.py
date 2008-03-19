
DEBUG = TEMPLATE_DEBUG = True

DATABASE_ENGINE = 'django_sqlalchemy'
DATABASE_NAME = ''
DJANGO_SQLALCHEMY_DBURI = "sqlite:///testing.db"
DJANGO_SQLALCHEMY_ECHO = False

INSTALLED_APPS = (
    'django_sqlalchemy',
    'regression.sample_app',
    'regression.norelations',
    )

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

# Of note here will be the TransactionMiddleware. 
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)
