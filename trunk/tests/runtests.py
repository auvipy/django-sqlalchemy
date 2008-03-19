#!/usr/bin/env python
import os, sys
from os.path import join, dirname, basename, abspath

def sqla_run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    # Again, mostly copies form django.test.simple.run_tests.
    import unittest
    from django.conf import settings
    from django.test.simple import build_test, build_suite
    from django.db.models.loading import get_apps, get_app
    settings.DEBUG = False    
    suite = unittest.TestSuite()
    testfiles = []
    if test_labels:
        for label in test_labels:
            fname = join(dirname(__file__), "regression", label)
            testfiles.append(fname)
    else:
        from glob import glob
        dirs = glob(join(dirname(__name__), "regression/*.test"))
        dirs = [join(dirname(__name__), bname) for bname in map(basename, dirs)]
        for test_file in dirs:
            testfiles.append(test_file)

    import doctest
    total_fails = 0
    for fname in testfiles:
        fails, tests = doctest.testfile(
            basename(fname), package="regression",
            optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
        total_fails += fails
    return total_fails


def django_sqlalchemy_tests(verbosity, test_labels):
    from django.conf import settings
    settings.SITE_ID = 1
    settings.USE_I18N = True

    failures = sqla_run_tests(test_labels, verbosity=verbosity, interactive=False, )
    if failures:
        print "%d failures" % failures


if __name__ == "__main__":
    __file__ = abspath(__file__)
    basepath = dirname(dirname(__file__))
    sys.path.insert(0, basepath)
    # This thing ensures that we're importing the local, development version. 
    import django_sqlalchemy
    sys.path.pop(0)
    # Mostly copied from Django's tests/runtests.py
    from optparse import OptionParser
    usage = "%prog [options] [model model model ...]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-v','--verbosity',
        action='store', dest='verbosity', default='0',
        type='choice', choices=['0', '1', '2'],
        help='Verbosity level; 0=minimal output, 1=normal output, 2=all output')
    parser.add_option(
        '--settings',
        help='Python path to settings module, e.g. "myproject.settings". '
        'If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment '
        'variable will be used.',
        default="settings_sqlite"
        )
    options, args = parser.parse_args()
    if options.settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = options.settings
    elif "DJANGO_SETTINGS_MODULE" not in os.environ:
        parser.error("DJANGO_SETTINGS_MODULE is not set in the environment. "
                      "Set it or use --settings.")
    django_sqlalchemy_tests(int(options.verbosity), args)
