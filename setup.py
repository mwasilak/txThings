#!/usr/bin/env python

from setuptools import setup, find_packages

import sys

if sys.version_info.major >= 3:
    py2_ipa = []
else:
    py2_ipa = [ 'py2-ipaddress>=3.4.1' ]

setup(name='txThings',
      version='0.3.0',
      description='CoAP protocol implementation for Twisted Framework',
      author='Maciej Wasilak',
      author_email='wasilak@gmail.com',
      url='https://github.com/siskin/txThings/',
      packages=find_packages(exclude=["*.test", "*.test.*"]),
      install_requires = ['twisted>=14.0.0', 'six>=1.10.0'] + py2_ipa,
     )
