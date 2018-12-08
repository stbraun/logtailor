#!/usr/bin/env python3
"""
Logfile analysis tool.

Copyright 2018 Stefan Braun.
"""

import sys
import time
from pathlib import Path
from typing import Union, List, Dict

import click
from py.iniconfig import IniConfig

# Configuration
INI_LOGFILES = 'logfiles'
INI_GENERAL = 'general'
INI_OUTPUT = 'output'
INI_TRIGGERS = 'triggers'

DEFAULT_TRACE = './trace.txt'


class Configuration:
    """Manages configuration file access to items."""

    def __init__(self, path: Path = Path('.logtail.ini')):
        """Initializes the configuration.

        :param path: path to configuration file.
        :type path: Path.
        """
        self.logs = {}
        if path.exists():
            cfg = IniConfig(path)
            if INI_LOGFILES in cfg.sections:
                self.logs = cfg.sections[INI_LOGFILES]
            self.output = Path(
                cfg.get(INI_GENERAL, INI_OUTPUT, default=DEFAULT_TRACE))
            self.triggers = cfg.get(INI_GENERAL, INI_TRIGGERS,
                                    default='').split('\n')
        else:
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


def validate_log(parse_all: bool, log: Union[str, Path], logs: Dict[str,str]):
    """Validate given log.

    :param parse_all: parse all configured log files.
    :type parse_all: boolean
    :param log: path or reference to a logfile to parse.
    :type log: Union[str, Path]
    :param logs: a map of references to configured log files for convenience.
    :type logs: Dict[str:str]
    """
    if parse_all:
        return logs.values()
    try:
        if isinstance(log, Path) and log.exists():
            logfile = log
        else:
            logfile = logs[log]
        return (logfile,)
    except KeyError:
        sys.stderr.write(
            'Logfile {} does not exist and is not a known log key. Please '
            'use one of: {}\n'.format(
                log, ', '.join(logs.keys())))
        sys.exit(1)


@click.command()
@click.option('--log', type=Path,
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
def tail(history: bool, filter_: bool, trigger: str, log: Union[Path, str],
         verbose: bool, parse_all: bool, append: bool):
    """Tail log file and filter for tags.

    Print only lines matching patterns given in triggers.

    :param log: reference to a logfile. Path to a file or a key to a logfile
    in the configuration.
    :type log: Union[Path, str]
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
    """
    cfg = Configuration()
    logs = validate_log(parse_all, log, cfg.logs)
    cfg.triggers.extend(trigger)
    mode = 'a' if append else 'w'
    with open(cfg.output, mode, buffering=1) as f_out:
        for log_ in logs:
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
