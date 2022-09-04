# -----------------------------------------------------------------------------
# Copyright 2022 by Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Pytest fixtures.

"""
import logging
import os
import pathlib

import pytest
import toml
from enaml.qt.qt_application import QtApplication
from enaml.workbench.api import Workbench

from gild.plugins.preferences import PreferencesManifest

from .util import close_all_popups, close_all_windows

#: Global variable storing the application folder path
APP_FOLDER = ""


#: Global variable linked to the --gild-sleep cmd line option.
DIALOG_SLEEP = 0


def pytest_addoption(parser):
    """Add command line options."""
    parser.addoption(
        "--gild-sleep",
        action="store",
        type=float,
        help="Time to sleep after showing a dialog",
    )


def pytest_configure(config):
    """Turn the --gild-sleep command line into a global variable."""
    s = config.getoption("--gild-sleep")
    if s is not None:
        global DIALOG_SLEEP
        DIALOG_SLEEP = s * 1000


@pytest.fixture
def dialog_sleep():
    """Return the time to sleep as set by the --gild-sleep option."""
    return DIALOG_SLEEP


@pytest.fixture(scope="session")
def app():
    """Make sure a QtApplication is active."""
    app = QtApplication.instance()
    if app is None:
        app = QtApplication()
        yield app
        app.stop()
    else:
        yield app


@pytest.fixture
def gild_qtbot(app, qtbot):
    """Set the enaml application on the bot and add automatic windows cleanup."""
    qtbot.enaml_app = app
    with close_all_windows(qtbot), close_all_popups(qtbot):
        yield qtbot


@pytest.fixture
def app_name() -> str:
    """Name of the application used for testing."""
    yield "test"


@pytest.fixture
def app_dir_storage(monkeypatch, tmpdir, app_name: str) -> pathlib.Path:
    """Path at which the file storing the app dir location is stored."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: pathlib.Path(str(tmpdir)))

    yield pathlib.Path(str(tmpdir), f".{app_name}")


@pytest.fixture
def app_dir(tmpdir, app_name, app_dir_storage):
    """Temporary application directory"""
    app_dir = pathlib.Path(str(tmpdir)) / "test"
    app_dir.mkdir(exist_ok=True, parents=True)
    with open(app_dir_storage, "w") as f:
        toml.dump(dict(app_path=str(app_dir)), f)

    yield app_dir


@pytest.fixture
def logger(caplog):
    """Fixture returning a logger for testing and cleaning handlers afterwards."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    yield logger

    logger.handlers = []


@pytest.fixture
def workbench():
    """Create a workbench instance."""
    workbench = Workbench()
    return workbench
