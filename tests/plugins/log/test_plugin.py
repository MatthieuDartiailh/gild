# -----------------------------------------------------------------------------
# Copyright 2022 by Glaze Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the log plugin.

"""
import logging
import os
import sys

import enaml
import pytest
from enaml.workbench.api import Workbench

from glaze.plugins.lifecycle import LifecycleManifest
from glaze.plugins.log import LogManifest
from glaze.plugins.log.tools import GuiHandler, LogModel, StreamToLogRedirector
from glaze.plugins.preferences import PreferencesManifest
from glaze.plugins.states import StateManifest
from glaze.testing.util import handle_dialog

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest


PLUGIN_ID = "glaze.logging"


class CMDArgs(object):
    pass


@pytest.fixture
def workbench(app_name):
    workbench = Workbench()
    workbench.register(CoreManifest())
    workbench.register(LifecycleManifest())
    workbench.register(PreferencesManifest(application_name=app_name))
    workbench.register(StateManifest())
    workbench.register(LogManifest(no_capture_varname="nocapture"))

    yield workbench

    workbench.unregister(PLUGIN_ID)


def test_handler1(workbench, logger):
    """Test adding removing handler."""
    core = workbench.get_plugin("enaml.workbench.core")
    handler = GuiHandler(model=LogModel())
    core.invoke_command(
        "glaze.logging.add_handler",
        {"id": "ui", "handler": handler, "logger": "test"},
        None,
    )
    log_plugin = workbench.get_plugin(PLUGIN_ID)

    assert log_plugin.handler_ids == ["ui"]
    assert handler in logger.handlers
    assert log_plugin._handlers == {"ui": (handler, "test")}

    core.invoke_command("glaze.logging.remove_handler", {"id": "ui"}, None)

    assert log_plugin.handler_ids == []
    assert handler not in logger.handlers
    assert log_plugin._handlers == {}


def test_filter1(workbench, logger):
    """Test adding removing filter."""
    core = workbench.get_plugin("enaml.workbench.core")
    handler = GuiHandler(model=LogModel())
    core.invoke_command(
        "glaze.logging.add_handler",
        {"id": "ui", "handler": handler, "logger": "test"},
        None,
    )

    class Filter(object):
        def filter(self, record):
            return True

    test_filter = Filter()

    core.invoke_command(
        "glaze.logging.add_filter",
        {"id": "filter", "filter": test_filter, "handler_id": "ui"},
        None,
    )

    log_plugin = workbench.get_plugin(PLUGIN_ID)

    assert log_plugin.filter_ids == ["filter"]
    assert log_plugin._filters == {"filter": (test_filter, "ui")}

    core.invoke_command("glaze.logging.remove_filter", {"id": "filter"}, None)

    assert log_plugin.filter_ids == []
    assert log_plugin._filters == {}


def test_filter2(workbench):
    """Test adding a filter and removing the handler."""
    core = workbench.get_plugin("enaml.workbench.core")
    handler = GuiHandler(model=LogModel())
    core.invoke_command(
        "glaze.logging.add_handler",
        {"id": "ui", "handler": handler, "logger": "test"},
        None,
    )

    class Filter(object):
        def filter(self, record):
            return True

    test_filter = Filter()

    core.invoke_command(
        "glaze.logging.add_filter",
        {"id": "filter", "filter": test_filter, "handler_id": "ui"},
        None,
    )

    log_plugin = workbench.get_plugin(PLUGIN_ID)

    assert log_plugin.filter_ids == ["filter"]
    assert log_plugin._filters == {"filter": (test_filter, "ui")}

    core.invoke_command("glaze.logging.remove_handler", {"id": "ui"}, None)

    assert log_plugin.filter_ids == []
    assert log_plugin._filters == {}


def test_filter3(workbench, logger):
    """Test adding an improper filter."""
    core = workbench.get_plugin("enaml.workbench.core")

    core.invoke_command(
        "glaze.logging.add_filter",
        {"id": "filter", "filter": object(), "handler_id": "ui"},
        None,
    )


def test_filter4(workbench, logger):
    """Test adding a filter to a non-existing handler."""
    core = workbench.get_plugin("enaml.workbench.core")

    class Filter(object):
        def filter(self, record):
            return True

    core.invoke_command(
        "glaze.logging.add_filter",
        {"id": "filter", "filter": Filter(), "handler_id": "ui"},
        None,
    )


def test_formatter(workbench, logger, glaze_qtbot):
    """Test setting the formatter of a handler."""
    core = workbench.get_plugin("enaml.workbench.core")
    model = LogModel()
    handler = GuiHandler(model=model)
    core.invoke_command(
        "glaze.logging.add_handler",
        {"id": "ui", "handler": handler, "logger": "test"},
        None,
    )

    formatter = logging.Formatter("test : %(message)s")
    core.invoke_command(
        "glaze.logging.set_formatter",
        {"formatter": formatter, "handler_id": "ui"},
        None,
    )

    logger.info("test")

    def assert_text():
        assert model.text == "test : test\n"

    glaze_qtbot.wait_until(assert_text)


def test_formatter2(workbench, logger, glaze_qtbot):
    """Test setting the formatter of a non existing handler."""
    core = workbench.get_plugin("enaml.workbench.core")

    formatter = logging.Formatter("test : %(message)s")
    core.invoke_command(
        "glaze.logging.set_formatter",
        {"formatter": formatter, "handler_id": "non-existing"},
        None,
    )

    glaze_qtbot.wait(10)


def test_start_logging1(workbench):
    """Test startup function when redirection of sys.stdout is required"""
    cmd_args = CMDArgs()
    cmd_args.nocapture = False
    old = sys.stdout

    app = workbench.get_plugin("glaze.lifecycle")
    app.run_app_startup(cmd_args)
    plugin = workbench.get_plugin(PLUGIN_ID)
    app_dir = workbench.get_plugin("glaze.preferences").app_directory

    try:
        assert os.path.isdir(os.path.join(app_dir, "logs"))
        assert "glaze.file_log" in plugin.handler_ids
        assert "glaze.gui_log" in plugin.handler_ids
        assert plugin.gui_model
        assert isinstance(sys.stdout, StreamToLogRedirector)
        assert isinstance(sys.stderr, StreamToLogRedirector)
    finally:
        sys.stdout = old


def test_start_logging2(workbench):
    """Test startup function when redirection of sys.stdout is not required"""
    cmd_args = CMDArgs()
    cmd_args.nocapture = True
    old = sys.stdout

    app = workbench.get_plugin("glaze.lifecycle")
    app.run_app_startup(cmd_args)
    plugin = workbench.get_plugin(PLUGIN_ID)
    app_dir = workbench.get_plugin("glaze.preferences").app_directory

    try:
        assert os.path.isdir(os.path.join(app_dir, "logs"))
        assert "glaze.file_log" in plugin.handler_ids
        assert "glaze.gui_log" in plugin.handler_ids
        assert plugin.gui_model
        # Fail in no capture mode (unknown reason).
        assert not isinstance(sys.stdout, StreamToLogRedirector)
        assert not isinstance(sys.stderr, StreamToLogRedirector)
    finally:
        sys.stdout = old


def test_display_current_log(workbench, glaze_qtbot):
    """Test the log display window"""
    cmd_args = CMDArgs()
    cmd_args.nocapture = True

    app = workbench.get_plugin("glaze.lifecycle")
    app.run_app_startup(cmd_args)

    core = workbench.get_plugin("enaml.workbench.core")
    with handle_dialog(glaze_qtbot):
        core.invoke_command("glaze.logging.display_current_log", {}, None)
