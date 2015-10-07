#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='txThings',
      version='0.1.4',
      description='CoAP protocol implementation for Twisted Framework',
      author='Maciej Wasilak',
      author_email='wasilak@gmail.com',
      url='https://github.com/siskin/txThings/',
      packages=find_packages(exclude=["*.test", "*.test.*"]),
      install_requires = ['twisted>=14.0.0'],
     )
