#!/usr/bin/env python

import subprocess

import setuptools

setup_info = dict(

    name = 'yolops',
    version = '0.0.3',
    description = 'Multipurpose devops tool',
    long_description = '' +
        'Yolops is a devops toolbox.'
        '',
    license = 'MIT',

    url = 'https://github.com/dontnod/yolops',

    author = 'Dontnod Entertainment',
    author_email = 'root@dont-nod.com',

    packages = setuptools.find_packages(include=['yolops', 'yolops.*']),

    install_requires = [
        'click',
    ],

    entry_points = {
        'console_scripts' : [ 'yolops = yolops.main:main' ],
    },

    # See list at https://pypi.python.org/pypi?:action=list_classifiers
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],

    keywords = 'yolo devops',
)

setuptools_info = dict(
    zip_safe = True,
)

setuptools.setup(**setup_info)
