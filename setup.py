#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Baidu AIP SDK for asyncio
"""
import platform
import sys

from setuptools import setup

if sys.version_info < (3,5):
    sys.exit('Sorry, Python < 3.5 is not supported')

setup(
    name = 'aiobaidu',
    version = '0.0.3',
    packages=['aiobaidu'],
    install_requires=[
        'aiohttp>2.0',
    ],
    license = 'Apache License',
    author = 'https://github.com/yaroslav-dudar',
    author_email = 'flayingfog@gmail.com',
    url = 'https://github.com/yaroslav-dudar/aio-baidu',
    description = 'Baidu AIP SDK for asyncio',
    keywords = ['baidu', 'face', 'aiobaidu']
)
