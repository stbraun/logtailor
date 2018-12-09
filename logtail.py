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
from typing import List, Dict

import click
from confloader import ConfDict

# Version number. Managed by bumpversion, do not edit!
VERSION = '0.5.2'

# Configuration
INI_FILE = '.logtail.ini'
INI_LOGFILES = 'logfiles'
INI_GENERAL = 'general'
INI_OUTPUT = 'output'
INI_TRIGGERS = 'triggers'

DEFAULT_TRACE = './trace.txt'


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
            cfg = ConfDict.from_file(path, defaults={'triggers': [],
                                                     'output': DEFAULT_TRACE})
            ofs = len('logfiles.')
            self.logs = {k[ofs:].strip(): v for k, v in cfg.items() if
                         k.startswith('logfiles.')}
            self.output = Path(cfg['output'])
            self.triggers = cfg['triggers']
        except MissingSectionHeaderError as msh:
            sys.stderr.write(str(msh) + '\n')
            sys.exit(1)
        except ConfDict.ConfigurationError as cex:
            sys.stderr.write(
                'Configuration error. Falling back to default configuration. '
                '({})\n'.format(
                    cex))
            self.logs = {}
            self.triggers = []
            self.output = Path(DEFAULT_TRACE)


def predicate(line, triggers: List[str]):
    """Check line for triggers."""
    for trigger in triggers:
        if trigger in line:
            return True
    return False


def out(f_out, line: str):
    """Write line to output."""
    ln_out = line.strip() + '\n'
    f_out.write(ln_out)
    sys.stdout.write(ln_out)


def validate_log(parse_all: bool, log: str, logs: Dict[str, str]):
    """Validate given log.

    :param parse_all: parse all configured log files.
    :type parse_all: boolean
    :param log: path or reference to a logfile to parse.
    :type log: str
    :param logs: a map of references to configured log files for convenience.
    :type logs: Dict[str:str]
    :return: one or more logfiles to parse.
    :rtype:  List[Path]
    """
    if parse_all:
        return [Path(log) for log in logs.values()]
    if log in logs:
        return [Path(logs[log])]
    path = Path(log)
    if path.exists():
        return [path]
    sys.stderr.write(
        'Logfile {} does not exist and is not a known log key. Please '
        'use one of: {}\n'.format(log, ', '.join(logs.keys())))
    sys.exit(1)


@click.command()
@click.option('--log', type=str,
              help='Logfile to stream. Path to a file or a key to a logfile '
                   'in the configuration.')
@click.option('--history/--no-history', default=False,
              help='Start with a clean output. Existing logs will not be '
                   'printed.')
@click.option('--filter/--no-filter', '-f/-nf', 'filter_', default=True,
              help='Disable filtering. Print all logs.')
@click.option('--trigger', '-t', type=str, multiple=True,
              help='Add a new trigger. May be used multiple times.')
@click.option('--verbose/--no-verbose', '-v/-nv', default=False,
              help='Output is more verbose. For example name of logfile and '
                   'active tags are printed.')
@click.option('--parse-all', '-p', is_flag=True, default=False,
              help='Parse all logs in sequence and append the result.')
@click.option('--append/--no-append', '-a', default=False,
              help='Append to Target file.')
@click.option('--version', 'show_version', is_flag=True, help='Show version information and exit..')
def tail(history: bool, filter_: bool, trigger: str, log: str,
         verbose: bool, parse_all: bool, append: bool, show_version: bool):
    """Tail log file and filter for tags.

    Print only lines matching patterns given in triggers.

    :param log: reference to a logfile. Path to a file or a key to a logfile
    in the configuration.
    :type log: str
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
    :param version: show version information and exit.
    :type version: bool
    """
    if show_version:
        sys.stdout.write('logtail version {}. Copyright 2018 Stefan Braun.\n'.format(VERSION))
        sys.exit(0)
    cfg = Configuration(INI_FILE)
    log_files = validate_log(parse_all, log, cfg.logs)
    cfg.triggers.extend(trigger)
    mode = 'a' if append else 'w'
    with open(cfg.output, mode, buffering=1) as f_out:
        for log_ in log_files:
            if not log_.exists():
                continue
            with log_.open("r") as f_in:
                if verbose:
                    out(f_out, str(log_.absolute()))
                    out(f_out, "Triggers: {}".format(', '.join(cfg.triggers)))
                if not history and not parse_all:
                    # read and drop existing lines
                    f_in.readlines()
                while True:
                    for line in f_in.readlines():
                        if not filter_ or predicate(line, cfg.triggers):
                            out(f_out, line)
                    if parse_all:
                        break
                    time.sleep(1)
