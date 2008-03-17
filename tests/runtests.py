import os, sys
from os.path import join, dirname
sys.path.insert(0, dirname(dirname(__file__)))
# This thing ensures that we're importing the local, development version. 
import django_sqlalchemy
sys.path.pop(0)

def django_sqlalchemy_tests(verbosity, test_labels):
    from django.conf import settings
    settings.SITE_ID = 1
    settings.USE_I18N = True

    from django.test.simple import run_tests
    failures = run_tests(test_labels, verbosity=verbosity, interactive=False, )
    if failures:
        sys.exit(failures)


if __name__ == "__main__":
    # Mostly copied from Django's tests/runtests.py
    from optparse import OptionParser
    usage = "%prog [options] [model model model ...]"
    parser = OptionParser(usage=usage)
    parser.add_option('-v','--verbosity', action='store', dest='verbosity', default='0',
        type='choice', choices=['0', '1', '2'],
        help='Verbosity level; 0=minimal output, 1=normal output, 2=all output')
    parser.add_option(
        '--settings',
        help='Python path to settings module, e.g. "myproject.settings". If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment variable will be used.',
        default="settings_sqlite"
        )
    options, args = parser.parse_args()
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    elif "DJANGO_SETTINGS_MODULE" not in os.environ:
        parser.error("DJANGO_SETTINGS_MODULE is not set in the environment. "
                      "Set it or use --settings.")
    django_sqlalchemy_tests(int(options.verbosity), args)
