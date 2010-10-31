#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='pyxmi',
      version='1.0',
      description='Generate XMI from Python source',
      author='Doug Winter',
      author_email='doug.winter@isotoma.com',
      zip_safe=False,
      packages=find_packages(),
      package_data = {
          'pyxmi': ['conf/MagicDraw.conf', 'conf/MagicDraw.xml'],
        },
      scripts= ['scripts/pyxmi'],
     )
