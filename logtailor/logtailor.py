#!/usr/bin/env python3
"""Logfile analysis tool."""
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

import sys
import time
from configparser import MissingSectionHeaderError
from pathlib import Path
from typing import Dict, List
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event

from loguru import logger
import click
from confloader import ConfDict

from .processors import SerialProcessor, ParallelProcessor


# Version number. Managed by bumpversion, do not edit!
__version__ = '1.2.3'

# Configuration
INI_FILE = ".logtailor.ini"
INI_LOGFILES = "logfiles"
INI_GENERAL = "general"
INI_OUTPUT = "output"
INI_TRIGGERS = "triggers"

DEFAULT_TRACE = "./trace.txt"

MAX_QUEUE_SIZE = 1000

TIMEOUT = 30  # timeout for thread completion.


L_TIME = "{time:YYYY.MM.DD HH:mm:ss.SSSSS}"
L_FORMAT = L_TIME + " - {level:8s} - {file}{function}:{line} - {message}"

L_CONFIG = {
    "handlers": [
        {"sink": sys.stdout, "format": "{time} - {message}"},
        {
            "sink": "logtailor.log",
            "format": L_FORMAT,
            "filter": "logtailor",
            "level": "TRACE",
        },
    ]
}
logger.configure(**L_CONFIG)
logger.enable("logtailor")


class Configuration:
    """Manages configuration file access to items.

    Provides:
    logs: Dict[str, str] - mapping of keys to logfiles.
    triggers: List[str] - list of triggers.
    output: Path - trace file.
    """

    def __init__(self, path: str):
        """Initializes the configuration.

        :param path: path to configuration file.
        :type path: str
        """
        try:
            cfg = ConfDict.from_file(
                path, defaults={"triggers": [], "output": DEFAULT_TRACE}
            )
            ofs = len("logfiles.")
            self.logs_ = {
                k[ofs:].strip(): Path(v)
                for k, v in cfg.items()
                if k.startswith("logfiles.")
            }
            self.output_ = Path(cfg["output"])
            self.triggers_ = cfg["triggers"]
        except MissingSectionHeaderError as msh:
            sys.stderr.write(str(msh) + "\n")
            sys.exit(1)
        except ConfDict.ConfigurationError as cex:
            sys.stderr.write(
                "Configuration error. Falling back to default configuration. "
                "({})\n".format(cex)
            )
            self.logs_ = {}
            self.triggers_ = []
            self.output_ = Path(DEFAULT_TRACE)

    @property
    def logs(self):
        """Configured logfiles with their keys.

        :return: dictionary of key: logfile pairs.
        :rtype: Dict[str, Path]
        """
        return self.logs_

    @property
    def output(self):
        """Configured path to output file.

        :return: path to output file.
        :rtype: Path
        """
        return self.output_

    @property
    def triggers(self):
        """Configured triggers.

        :return: list of triggers.
        :rtype: List[str]
        """
        return self.triggers_


@logger.catch
def render_log(log_queue: Queue, f_out, cancel: Event):
    """Render lines read from queue."""
    logger.trace("render_log() started")
    while True:
        if cancel.is_set() and log_queue.empty():
            logger.trace("render_log() -->  canceled")
            return
        time.sleep(0.1)
        while not log_queue.empty():
            line = log_queue.get()
            out(f_out, line)
            log_queue.task_done()


def out(f_out, line: str):
    """Write line to output."""
    ln_out = line.strip() + "\n\r"
    f_out.write(ln_out)
    sys.stdout.write(ln_out)


@logger.catch
def validate_log(parse_all: bool, log: str, logs: Dict[str, Path]):
    """Validate given log.

    :param parse_all: parse all configured log files.
    :type parse_all: boolean
    :param log: path or reference to a logfile to parse.
    :type log: str
    :param logs: a map of references to configured log files for convenience.
    :type logs: Dict[str, Path]
    :return: one or more logfiles to parse.
    :rtype:  List[Path]
    """
    if parse_all:
        return list(logs.values())
    if log is None:
        sys.stderr.write(
            "Please specify at least a log file. Try --help for additional "
            "information.\n|n"
        )
        sys.exit(1)
    if log in logs:
        return [Path(logs[log])]
    path = Path(log)
    if path.exists():
        return [path]
    sys.stderr.write(
        "Logfile {} does not exist and is not a known log key. Please "
        "use one of: {}\n\n".format(log, ", ".join(logs.keys()))
    )
    sys.exit(1)


def mode(is_append: bool):
    """Write mode dependend on is_append."""
    return "a" if is_append else "w"


def processor_factory(
    log_files: List[Path],
    triggers: List[str],
    log_queue: Queue,
    cancel_event: Event,
    tailing: bool,
    history: bool,
    encoding: str
):
    """Create a processor instance.

    :param log_files: list of logfiles to parse.
    :type log_files: List[Path]
    :param triggers: search the logfiles for these triggers.
    :type triggers: List[str]
    :param log_queue: deliver filtered lines in this queue.
    :type log_queue: Queue
    :param cancel_event: trigger to cancel logile processing.
    :type cancel_event: Event
    :param tailing: wait for more data at eol.
    :type tailing: bool
    :param history: parse log file entries recorded before start of the tool.
    :type history: bool
    :param encoding: encoding of the log file.
    :type encoding: str
    :return: a log processor instance.
    :rtype: LogProcessor
    """
    if tailing:
        return ParallelProcessor(log_files, triggers, log_queue,
                                 cancel_event, history, encoding, tailing)
    return SerialProcessor(log_files, triggers, log_queue,
                           cancel_event, history, encoding)


def determine_triggers(triggers, add_triggers, use_triggers):
    """Determine set of effective triggers.

    :param triggers: list of configured triggers.
    :type triggers: List[str]
    :param add_triggers: additional triggers.
    :type add_triggers: List[str]
    :param use_triggers: triggers shall be applied.
    :type use_triggers: bool
    :return: list of effective triggers.
    :rtype: List[str]
    """
    if use_triggers:
        triggers_ = triggers
        triggers_.extend(add_triggers)
    else:
        triggers_ = []
    return triggers_


def verbose_info(log_files, triggers):
    """Print verbose information to stderr.

    :param log_files: list of log files.
    :type log_files: List[Path]
    :param triggers: list of triggers.
    :type triggers: List[str]
    """
    sys.stderr.write("{}\n".format("-" * 80))
    sys.stderr.write(
        "\tlogtailor version {}. Copyright 2018 Stefan Braun.\n".format(__version__)
    )
    sys.stderr.write("Triggers:\n")
    for trigger in triggers:
        sys.stderr.write("\t{}\n".format(trigger))
    sys.stderr.write("Log files:\n")
    for log in log_files:
        sys.stderr.write("\t{}\n".format(log))
    sys.stderr.write("{}\n".format("-" * 80))


def print_version_and_exit():
    """Print version and copyright info to stderr and exit with 0."""
    sys.stderr.write(
        "logtailor version {}. Copyright 2018 Stefan Braun.\n".format(__version__)
    )
    sys.exit(0)


# pylint: disable=too-many-locals
@click.command()
@click.option(
    "--log",
    type=str,
    help="Logfile to stream. Path to a file or a key to a logfile "
    "in the configuration.",
)
@click.option(
    "--tail/--no-tail",
    default=True,
    help="Tail logfile waiting for more data. Do not exit at eof.",
)
@click.option(
    "--history/--no-history",
    default=False,
    help="Start with a clean output. Existing logs will not be printed.",
)
@click.option(
    "--filter/--no-filter",
    "-f/-nf",
    "filter_",
    default=True,
    help="Disable filtering. Print all logs.",
)
@click.option(
    "--trigger",
    "-t",
    type=str,
    multiple=True,
    help="Add a new trigger. May be used multiple times.",
)
@click.option(
    "--verbose/--no-verbose",
    "-v/-nv",
    default=False,
    help="Output is more verbose. For example name of logfile and "
    "active tags are printed.",
)
@click.option(
    "--parse-all",
    "-p",
    is_flag=True,
    default=False,
    help="Parse all logs in sequence and append the result.",
)
@click.option(
    "--append/--no-append", "-a", default=False, help="Append to Target file."
)
@click.option(
    "--version",
    "show_version",
    is_flag=True,
    help="Show version information and exit..",
)
@click.option(
    "--encoding",
    type=str,
    default='utf-8',
    help="Encoding of the log files, e.g., latin1. Default is utf-8."
)
@logger.catch
def tailor(
    history: bool,
    filter_: bool,
    trigger: str,
    log: str,
    tail: bool,
    verbose: bool,
    parse_all: bool,
    append: bool,
    show_version: bool,
    encoding: str
):
    """Tail log file and filter for triggers.

    Print only lines matching patterns given in triggers.

    :param log: reference to a logfile. Path to a file or a key to a logfile
    in the configuration.
    :type log: str
    :param tail: Tail logfile waiting for more data. Do not exit at eof.
    :type tail: bool
    :param history: show history. If False show only lines created after start
    of program,
    :type history: bool
    :param filter_: apply line filter or switch it off.
    :type filter_: bool
    :param trigger: add a trigger to the filter criteria.
    :type trigger: str
    :param verbose: more verbose output.
    :type verbose: bool
    :param parse_all: parse all known log files.
    :type parse_all: bool
    :param append: append to existing target file.
    :type append: bool
    :param show_version: show version information and exit.
    :type show_version: bool
    :param encoding: encoding of the log file(s), e.g., latin1.
    :type encoding: str
    """
    if show_version:
        print_version_and_exit()
    cfg = Configuration(INI_FILE)
    triggers = determine_triggers(cfg.triggers, trigger, filter_)
    log_files = validate_log(parse_all, log, cfg.logs)
    if verbose:
        verbose_info(log_files, triggers)
    log_queue = Queue(MAX_QUEUE_SIZE)
    with open(cfg.output, mode(append), buffering=1) as f_out:
        with ThreadPoolExecutor(max_workers=2) as tp_ex:
            cancel_event = Event()
            cancel_event.clear()
            future_render = tp_ex.submit(render_log, log_queue, f_out, cancel_event)
            processor = processor_factory(
                log_files, triggers, log_queue, cancel_event, tail, history, encoding
            )
            future_processor = tp_ex.submit(processor.run)

            click.pause()
            cancel_event.set()
            try:
                future_processor.result(timeout=TIMEOUT)
                future_render.result(timeout=TIMEOUT)
            except (concurrent.futures.TimeoutError,
                    concurrent.futures.CancelledError) as exc:
                msg = "Timeout waiting for processing threads to complete ({})."
                logger.warning(msg, exc)
            logger.trace("----- stopped -----")


if __name__ == "__main__":
    tailor()  # pylint: disable=no-value-for-parameter
