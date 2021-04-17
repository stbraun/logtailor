# coding=utf-8
"""Test fixtures."""
# Copyright (c) 2018 Stefan Braun
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from queue import Queue
from threading import Event

import pytest

from logtailor import processors


@pytest.fixture
def ser_processor():
    """Provide a SerialProcessor instance."""
    processor = processors.SerialProcessor([], [], Queue(), Event(), True, 'utf-8')
    return processor


@pytest.fixture
def par_processor():
    """Provide a ParallelProcessor instance."""
    processor = processors.ParallelProcessor([], [], Queue(), Event(), True, 'utf-8')
    return processor


@pytest.fixture
def single_log():
    """Provide a single log file fixture."""
    log = PathM("single.log")
    log.text_to_provide = ["single 01", "single 02", "single 03"]
    return log


# pylint: disable=missing-docstring
class PathM:
    """Simple mock replacement for Path."""

    def __init__(self, path: str):
        print("PathM.__init__({})".format(path))
        self.path = path
        self.text_to_provide = []
        self.received_text = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    # pylint: disable=too-many-arguments
    def open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        return self

    def exists(self):
        return True

    def absolute(self):
        return self.path

    def readlines(self):
        yield from self.text_to_provide

    def close(self):
        pass

    def __eq__(self, other):
        return self.path == other.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return "<{}>".format(self.path)
