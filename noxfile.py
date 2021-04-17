# coding=utf-8
""" Configuration of nox test automation tool. """

import nox


@nox.session(python=['3.7', '3.8', '3.9'])
def lint(session):
    """Run static analysis."""
    session.run("pipenv", "install", "--dev", external=True)
    session.run("pipenv", "run", "flake8", "logtailor/", "tests/")


@nox.session(python=['3.7', '3.8', '3.9'])
def tests(session):
    """Run tests for all supported versions of Python."""
    session.run("pipenv", "install", "--dev", external=True)
    session.run("pipenv", "run", "pytest", "tests/")
