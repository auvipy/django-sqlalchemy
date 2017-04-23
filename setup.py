#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.md').read()
doclink = """
Documentation
-------------

The full documentation is at http://django-sqlalchemy.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='django-sqlalchemy',
    version='0.0.1',
    description='django extension for sqlalchemy integration ',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Asif Saifuddin Auvi',
    author_email='auvipy@gmail.com',
    url='https://github.com/auvipy/django-sqlalchemy',
    packages=[
        'django-sqlalchemy',
    ],
    package_dir={'django-sqlalchemy': 'sqladjango'},
    include_package_data=True,
    install_requires=[
    ],
    license='MIT',
    zip_safe=False,
    keywords='django-sqlalchemy','sqlalchemy','django',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
