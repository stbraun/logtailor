# coding=utf-8
"""Test predicate."""
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

from pathlib import Path

from logtailor import logtailor


def test_unknown_config_file():
    """Call configuration with an invalid path.

    Expected to come back with default values.
    Warning to stderr.
    """
    cfg = logtailor.Configuration("invalid_path")
    assert cfg.logs == {}
    assert cfg.triggers == []
    assert cfg.output == Path(logtailor.DEFAULT_TRACE)


def test_valid_config():
    """Read a valid config file."""
    cfg = logtailor.Configuration("scratch/test.ini")
    assert "log_1" in cfg.logs and "log_2" in cfg.logs and "log_3" in cfg.logs
    assert cfg.triggers == ["<access>", "warning", "<sort>"]
    assert cfg.output == Path("tracelog.txt")


def test_validate_parse_all():
    """Read all logfiles from configuration."""
    log_dict = {"l1": Path("./app1.log"), "l2": Path("./custom/appl.log")}
    result = logtailor.validate_log(True, "", log_dict)
    assert result == [log_dict["l1"], log_dict["l2"]]


def test_validate_valid_logfile():
    """Call validate with a valid log file."""
    log_file = "scratch/example.log"
    result = logtailor.validate_log(False, log_file, {})
    assert result == [Path(log_file)]


def test_validate_logkey():
    """Call validate with a log key."""
    log_dict = {"l1": Path("./app1.log"), "l2": Path("./custom/appl.log")}
    result = logtailor.validate_log(False, "l2", log_dict)
    assert result == [Path("./custom/appl.log")]
