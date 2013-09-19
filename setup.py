#!/usr/bin/env python

from distutils.core import setup

setup(name='wikipedia-dump-tools',
      version='0.1',
      description='Python programs for working with Wikipedia dumps.',
      author='Drew Vogel',
      author_email='dvogel@sunlightfoundation.com',
      packages=['wikitools.filters'],
      requires=['functional (==0.7.0)']
     )
