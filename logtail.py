#!/usr/bin/env python3
import sys
import time
from typing import Union
from pathlib import Path

import click
import rx

base_log_path = Path(
    "c:/Users/sbraun/AppData/Roaming/Rockwell Automation/FactoryTalk "
    "ProductionCentre/logs/PlantOpsClient/")
log_pec = base_log_path / "ApplicationStart_ProductionExecutionClient-ftps.log"
log_pmc1 = base_log_path / "ApplicationStart_ProductionManagementClient-ftps" \
                           ".log"
log_pmc2 = base_log_path / "pmc_MainScreen-ftps.log"
log_dm = base_log_path / "ApplicationStart_DataManager-ftps.log"
log_prc = base_log_path / "ApplicationStart_ExceptionDashboard-ftps.log"
log_rd = base_log_path / "ApplicationStart_RecipeDesigner-ftps.log"
log_admin = base_log_path / "adminConsole-ftps.log"
log_dummy = base_log_path / "DummyFormForUnitTesting-ftps.log"

LOG_D = {'log_pec': log_pec, 'log_pmc1': log_pmc1, 'log_pmc2': log_pmc2,
         'log_dm': log_dm, 'log_prc': log_prc, 'log_rd': log_rd,
         'log_admin': log_admin, 'log_dummy': log_dummy}
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


def out(f_out, line):
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
        return logfile,
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
@click.option('--hist/--no-hist', default=False,
              help='Start with a clean output. Existing logs will not be '
                   'printed.')
@click.option('--filter/--no-filter', '-f/-nf', default=True,
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
def tail(hist: bool, filter: bool, trigger: str, log: Union[Path, str],
         verbose: bool, parse_all: bool, append: bool):
    """Tail log file and filter for tags.

    Print only lines matching patterns given in triggers.

    :param log: reference to a logfile. One of LOG_D.keys() or path to a
    logfile.
    :type log: Union[Path, str]
    :param hist: show history. If False show only lines created after start
    of program,
    :type hist: bool
    :param filter: apply line filter or switch it off.
    :type filter: bool
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
                    out(f_out, log_.absolute())
                    out(f_out, "Triggers: {}".format(', '.join(TRIGGERS)))
                if not hist and not parse_all:
                    # read and drop existing lines
                    f_in.readlines()
                while True:
                    rx.Observable.from_(f_in.readlines()) \
                        .filter(lambda ln: not filter or predicate(ln)) \
                        .subscribe(lambda ln: out(f_out, ln))
                    if parse_all:
                        break
                    time.sleep(1)


if __name__ == '__main__':
    tail()
