#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

PACKAGES = ['tclient']


def get_init_val(val, packages=PACKAGES):
    pkg_init = "%s/__init__.py" % PACKAGES[0]
    value = '__%s__' % val
    fn = open(pkg_init)
    for line in fn.readlines():
        if line.startswith(value):
            return line.split('=')[1].strip().strip("'")


setup(
    name=get_init_val('title'),
    version=get_init_val('version'),
    description=get_init_val('description'),
    long_description=open('README').read(),
    classifiers=["Topic :: Internet :: WWW/HTTP"],
    author=get_init_val('author'),
    author_email=get_init_val('author_email'),
    url=get_init_val('url'),
    package_data={'': ['../LICENSE', '../README', '../README.md']},
    include_package_data=True,
    license=get_init_val('license'),
    packages=PACKAGES,
    requires=['tornado']
)
