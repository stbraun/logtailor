"""Setup for logtail logfile filter.

Copyright 2018, Stefan Braun.
"""

from setuptools import setup

VERSION = '0.5.0'

setup(
    name='logtail',
    version=VERSION,
    description="Log analysis tool.",
    classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords="development tools",
    author="Stefan Braun",
    author_email="sb@action.ms",
    license="MIT",
    py_modules=['logtail'],
    install_requires=['click', 'confloader', 'pex', 'bumpversion'],
    entry_points={
        'console_scripts': [
            'logtail=logtail:tail',
        ]
    },
)
