# coding=utf-8
"""Log processors."""
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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from queue import Queue
from threading import Event
import concurrent
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

# pylint: disable=too-few-public-methods


class LogProcessor(ABC):
    """Process one or more logs."""
    # pylint: disable=too-many-instance-attributes

    logfiles: List[Path]
    triggers: List[str]
    cancel: Event
    log_queue: Queue
    start_clean: bool
    filtered: bool
    verbose: bool

    def __init__(
        self,
        log_files: List[Path],
        triggers: List[str],
        log_queue: Queue,
        cancel: Event,
        history: bool,
        encoding: str,
        tailing: bool = False
    ):
        """Initialize instance.

        :param log_files: list of logfiles to parse.
        :type log_files: List[Path]
        :param triggers: search the logfiles for these triggers.
        :type triggers: List[str]
        :param log_queue: deliver filtered lines in this queue.
        :type log_queue: Queue
        :param cancel: trigger to cancel logfile processing.
        :type cancel: Event
        :param history: parse historic log items.
        :type history: bool
        :param encoding: encoding of logfile.
        :type encoding: str
        :param tailing: True to keep reading after eof, waiting for more data.
        :type tailing: bool
        """
        self.logfiles = log_files
        self.triggers = triggers
        self.log_queue = log_queue
        self.cancel = cancel
        self.verbose = False
        self.start_clean = not history
        self.filtered = True
        self.encoding = encoding
        self.tailing = tailing
        if self.verbose:
            logger.info(
                "{}({}) Triggers: {}", self.__class__.__name__, log_files, triggers
            )

    @abstractmethod
    def run(self):
        """Process log files."""

    def _predicate(self, line: str):
        """Check line for triggers."""
        for trigger in self.triggers:
            if trigger in line:
                return True
        return False

    @logger.catch
    def _process_logfile(self, logfile: Path, keep_tailing: bool):
        """Process one logfile.

        :param logfile: the log file to process.
        :type logfile: Path
        :param keep_tailing: true to keep waiting for more data at eof.
        :type keep_tailing: bool
        """
        logger.trace("--> {}.process_logfile({})", self.__class__.__name__, logfile)
        if not logfile.exists():
            logger.warning("log {} not found -->", logfile)
            return
        try:
            with logfile.open("r", encoding=self.encoding) as f_in:
                if self.start_clean:
                    # read and drop existing lines
                    logger.info("{}({}) drop history", self.__class__.__name__, logfile)
                    f_in.readlines()
                while True:
                    if self.cancel.is_set():
                        logger.trace(
                            "{}({}) canceled -->", self.__class__.__name__, logfile
                        )
                        return
                    for line in f_in.readlines():
                        line = line.strip()
                        logger.trace("Read: >{}<", line)
                        if not self.filtered or self._predicate(line):
                            logger.trace("Put: >{}<", line)
                            self.log_queue.put(line)
                            time.sleep(0.0001)
                    if not keep_tailing:
                        logger.trace(
                            "{}({}) finished -->", self.__class__.__name__, logfile
                        )
                        return
                    time.sleep(1)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Processing of logfile {} failed with {}", logfile, exc)


class SerialProcessor(LogProcessor):
    """Process one log after the other"""

    def run(self):
        """Process one logfile after the other."""
        logger.trace("--> SerialProcessor.run({})", self.logfiles)
        for logfile in self.logfiles:
            self._process_logfile(logfile, False)


class ParallelProcessor(LogProcessor):
    """Processes all logfiles in parallel."""

    @logger.catch
    def run(self):
        """Processes all logfiles in parallel."""
        logger.trace("--> ParallelProcessor.run({})", self.logfiles)
        num_workers = len(self.logfiles)
        if not num_workers:
            return
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_log = {
                executor.submit(self._process_logfile, log, self.tailing): log
                for log in self.logfiles
            }
            logger.info("ParallelProcessor --> workers started: {}", future_log)
            for future in concurrent.futures.as_completed(future_log):
                log = future_log[future]
                try:
                    future.result()
                except Exception as exc:  # pylint: disable=broad-except
                    logger.info("{} generated an exception: {}", log, exc)
