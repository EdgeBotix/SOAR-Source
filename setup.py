#!/usr/bin/env python

from distutils.core import setup

setup(name='libdw',
      version='2013-3',
      description='The Digital World Code Distribution',
      author='-',
      author_email='-',
      license='GPLv2',
      url='http://www.sutd.edu.sg',
      packages = ['libdw','form','soar','soar.io','soar.graphics',\
                  'soar.serial','soar.controls','soar.outputs'],
      package_data={'libdw': ['*.pyc'], 'form': ['*.pyc'],\
                    'soar': ['*.pyc', 'io/*.pyc', 'graphics/*.pyc',\
                             'serial/*.pyc', 'controls/*.pyc', 'outputs/*.pyc',\
                             'media/*','worlds/*']},
      scripts=['setupsoar.py', 'soar/soar'])
