"""Setup for logtailor logfile filter.

Copyright 2018, Stefan Braun.
"""

from setuptools import setup

version='1.2.3'

setup(
    name="logtailor",
    version=version,
    description="Log tail and filter tool.",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="development tools",
    author="Stefan Braun",
    author_email="sb@stbraun.com",
    license="MIT",
    py_modules=["logtailor"],
    packages=["logtailor"],
    install_requires=[
        "click",
        "confloader",
        "loguru",
        "pex",
        "pytest",
        "pytest-watch",
    ],
    entry_points={"console_scripts": ["logtailor=logtailor.logtailor:tailor"]},
)
