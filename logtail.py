#!/usr/bin/env python3
"""
Logfile analysis tool.

Copyright 2018 Stefan Braun.
"""

import sys
import time
from typing import Union
from pathlib import Path

import click

BASE_LOG_PATH = Path(
    "c:/Users/sbraun/AppData/Roaming/Rockwell Automation/FactoryTalk "
    "ProductionCentre/logs/PlantOpsClient/")
LOG_PEC = BASE_LOG_PATH / "ApplicationStart_ProductionExecutionClient-ftps.log"
LOG_PMC1 = BASE_LOG_PATH / "ApplicationStart_ProductionManagementClient-ftps" \
                           ".log"
LOG_PMC2 = BASE_LOG_PATH / "pmc_MainScreen-ftps.log"
LOG_DM = BASE_LOG_PATH / "ApplicationStart_DataManager-ftps.log"
LOG_PRC = BASE_LOG_PATH / "ApplicationStart_ExceptionDashboard-ftps.log"
LOG_RD = BASE_LOG_PATH / "ApplicationStart_RecipeDesigner-ftps.log"
LOG_ADMIN = BASE_LOG_PATH / "adminConsole-ftps.log"
LOG_DUMMY = BASE_LOG_PATH / "DummyFormForUnitTesting-ftps.log"

LOG_D = {'LOG_PEC': LOG_PEC, 'LOG_PMC1': LOG_PMC1, 'LOG_PMC2': LOG_PMC2,
         'LOG_DM': LOG_DM, 'LOG_PRC': LOG_PRC, 'LOG_RD': LOG_RD,
         'LOG_ADMIN': LOG_ADMIN, 'LOG_DUMMY': LOG_DUMMY}
LOGS = LOG_D.values()

TARGET = Path("./Target.txt")

"""
Triggers:
---------
<sort> - general sorting related logs
<sort-ui> - sorting UI, e.g. layout, images, etc.
<sort-ctl> - control, e.g. change of sort criteria or sort order, button clicks
<sort-cmp> - comparator logs, e.g. less than / equal / greater than decisions
"""

TRIGGERS = ['<access>', '<access-user>', '<signature>']


def predicate(line):
    """Check line for triggers."""
    for trigger in TRIGGERS:
        if trigger in line:
            return True
    return False


def out(f_out, line: str):
    """Write line to output."""
    ln_out = line.strip() + '\n'
    f_out.write(ln_out)
    sys.stdout.write(ln_out)


def validate_log(parse_all: bool, log: Union[str, Path]):
    """Validate given log."""
    if parse_all:
        return LOGS
    try:
        if isinstance(log, Path) and log.exists():
            logfile = log
        else:
            logfile = LOG_D[log]
        return (logfile,)
    except KeyError:
        sys.stderr.write(
            'Logfile {} does not exist and is not a known log key. Please '
            'use one of: {}\n'.format(
                log, ', '.join(LOG_D.keys())))
        sys.exit(1)


@click.command()
@click.option('--log', type=Path,
              help='Logfile to stream. One of {} or a file path to a '
                   'logfile'.format(LOG_D.keys()))
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

    :param log: reference to a logfile. One of LOG_D.keys() or path to a
    logfile.
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
    logs = validate_log(parse_all, log)
    TRIGGERS.extend(trigger)
    mode = 'a' if append else 'w'
    with open(TARGET, mode, buffering=1) as f_out:
        for log_ in logs:
            if not log_.exists():
                continue
            with log_.open("r") as f_in:
                if verbose:
                    out(f_out, str(log_.absolute()))
                    out(f_out, "Triggers: {}".format(', '.join(TRIGGERS)))
                if not history and not parse_all:
                    # read and drop existing lines
                    f_in.readlines()
                while True:
                    for line in f_in.readlines():
                        if not filter_ or predicate(line):
                            out(f_out, line)
                    if parse_all:
                        break
                    time.sleep(1)
