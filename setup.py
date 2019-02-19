#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import shutil
import sys
from io import open

from setuptools import setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('request_logging')


if sys.argv[-1] == 'publish':
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    shutil.rmtree('dist')
    shutil.rmtree('build')
    shutil.rmtree('django_request_logging.egg-info')
    sys.exit()


setup(
    name='django-request-logging',
    version=version,
    description='Django middleware that logs http request body.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/Rhumbix/django-request-logging.git',
    author='Rhumbix',
    author_email='dev@rhumbix.com',
    license='MIT',
    packages=['request_logging'],
    install_requires=[
        'Django',
    ],
    zip_safe=False
)
