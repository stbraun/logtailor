# coding=utf-8
"""Test LogProcessor."""
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

import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event

import pytest

# pylint: disable=protected-access


def test_empty_triggers(ser_processor):
    """No triggers defined."""
    assert not ser_processor._predicate("test line")


def test_empty_line(ser_processor):
    """No input."""
    assert not ser_processor._predicate("")
    ser_processor.triggers = ["some", "triggers"]
    assert not ser_processor._predicate("")


def test_no_match(ser_processor):
    """Line without matching trigger."""
    ser_processor.triggers = ["no", "match"]
    assert not ser_processor._predicate("test line")


def test_match(ser_processor):
    """Trigger matching input."""
    ser_processor.triggers = ["shall", "hit"]
    assert ser_processor._predicate("hit this line")
    ser_processor.triggers = ["line", "trigger"]
    assert ser_processor._predicate("hit this line")


# pylint: disable=protected-access


def test_empty_serial_processing(ser_processor):
    """Serial processing with empty logfile list."""
    ser_processor.run()


def test_empty_parallel_processing(par_processor):
    """Parallel processing with empty logfile list."""
    par_processor.run()


def test_single_serial_processing(ser_processor, single_log):
    """Serial processing with single log."""
    queue = Queue()
    cancel = Event()
    ser_processor.logfiles = [single_log]
    ser_processor.filtered = False
    ser_processor.log_queue = queue
    ser_processor.cancel = cancel
    ser_processor.run()
    assert queue.qsize() == 3


def test_single_parallel_processing(par_processor, single_log):
    """Parallel processing with single log."""
    queue = Queue()
    cancel = Event()

    def stop_thread():
        time.sleep(1)
        cancel.set()

    par_processor.logfiles = [single_log]
    par_processor.filtered = False
    par_processor.log_queue = queue
    par_processor.cancel = cancel
    with ThreadPoolExecutor(max_workers=2) as tpex:
        tpex.submit(par_processor.run)
        tpex.submit(stop_thread())
    if queue.qsize() != 3:
        print("ERROR qsize:")
        while not queue.empty():
            print(queue.get())
        pytest.fail("unexpected queue size")
    assert queue.qsize() == 3


def test_multi_serial_processing(ser_processor, single_log):
    """Serial processing with multiple log."""
    queue = Queue()
    cancel = Event()
    ser_processor.logfiles = [single_log, single_log]
    ser_processor.filtered = False
    ser_processor.log_queue = queue
    ser_processor.cancel = cancel
    ser_processor.run()
    assert queue.qsize() == 6


def test_multi_parallel_processing(par_processor, single_log):
    """Parallel processing with multiple logs."""
    queue = Queue()
    cancel = Event()

    def stop_threads():
        time.sleep(1)
        cancel.set()

    par_processor.logfiles = [single_log, single_log]
    par_processor.filtered = False
    par_processor.log_queue = queue
    par_processor.cancel = cancel
    with ThreadPoolExecutor(max_workers=2) as tpex:
        tpex.submit(par_processor.run)
        tpex.submit(stop_threads())
    assert queue.qsize() == 6
