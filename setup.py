# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in reconciler/__init__.py
from reconciler import __version__ as version

setup(
	name='reconciler',
	version=version,
	description='Reconciliation tool for GSTR 2A and Purchase Invoice',
	author='Aerele Technologies Private Limited',
	author_email='admin@aerele.in',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
