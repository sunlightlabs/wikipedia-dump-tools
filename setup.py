#!/usr/bin/env python

from setuptools import setup

setup(name='wikipedia-dump-tools',
      version='0.1',
      description='Python programs for working with Wikipedia dumps.',
      author='Drew Vogel',
      author_email='dvogel@sunlightfoundation.com',
      packages=['wikitools'],
      requires=['functional (==0.7.0)']
     )
