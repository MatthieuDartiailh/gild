# -----------------------------------------------------------------------------
# Copyright 2022 by Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the ErrorsPlugin.

"""
import enaml
import pytest
from enaml.widgets.api import MultilineField

from gild.plugins.errors import ErrorsManifest
from gild.plugins.lifecycle import LifecycleManifest
from gild.plugins.packages import PackagesManifest
from gild.testing.util import get_window, handle_dialog, show_and_close_widget

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest

    from gild.plugins.errors.widgets import HierarchicalErrorsDisplay


APP_ID = "gild.lifecycle"
ERRORS_ID = "gild.errors"


@pytest.fixture
def err_workbench(workbench):
    """Create a workbench and register basic manifests."""
    workbench.register(CoreManifest())
    workbench.register(ErrorsManifest())
    workbench.register(PackagesManifest())
    return workbench


class FailedFormat(object):
    def __str__(self):
        self.called = 1
        raise ValueError()

    def __repr__(self):
        self.called = 1
        raise ValueError()


# =============================================================================
# --- Test plugin -------------------------------------------------------------
# =============================================================================


def test_life_cycle(err_workbench):
    """Test basic behavior of ErrorsPlugin."""
    plugin = err_workbench.get_plugin(ERRORS_ID)

    assert len(plugin.errors) == 4

    plugin._errors_handlers.contributions = {}

    assert len(plugin.errors) == 0

    plugin.stop()

    assert not len(plugin.errors)


def test_signal_command_with_unknown(err_workbench, gild_qtbot):
    """Test the signal command with a stupid kind of error."""
    core = err_workbench.get_plugin("enaml.workbench.core")

    with handle_dialog(gild_qtbot):
        core.invoke_command("gild.errors.signal", {"kind": "stupid", "msg": None})

    with handle_dialog(gild_qtbot):
        fail = FailedFormat()
        core.invoke_command("gild.errors.signal", {"kind": "stupid", "msg": fail})

    assert getattr(fail, "called", None)


def test_handling_error_in_handlers(err_workbench, gild_qtbot):
    """Test handling an error occuring in a specilaized handler."""
    plugin = err_workbench.get_plugin(ERRORS_ID)

    def check_dialog(bot, dial):
        assert "error" in dial.errors
        assert "registering" not in dial.errors

    with handle_dialog(gild_qtbot, handler=check_dialog):
        plugin.signal("registering")

    with handle_dialog(gild_qtbot, handler=check_dialog):
        plugin.signal("registering", msg=FailedFormat())


def test_gathering_mode(err_workbench, gild_qtbot):
    """Test gathering multiple errors."""
    core = err_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.errors.enter_error_gathering")

    core.invoke_command("gild.errors.signal", {"kind": "stupid", "msg": None})

    with pytest.raises(AssertionError):
        get_window(gild_qtbot)

    with handle_dialog(gild_qtbot):
        core.invoke_command("gild.errors.exit_error_gathering")


def test_report_command(err_workbench, gild_qtbot):
    """Test generating an application errors report."""
    core = err_workbench.get_plugin("enaml.workbench.core")
    with handle_dialog(gild_qtbot):
        core.invoke_command("gild.errors.report")

    with handle_dialog(gild_qtbot):
        core.invoke_command("gild.errors.report", dict(kind="error"))

    with handle_dialog(gild_qtbot):
        core.invoke_command("gild.errors.report", dict(kind="stupid"))


def test_install_excepthook(err_workbench, gild_qtbot):
    """Test the installation and use of the sys.excepthook."""
    import sys

    old_hook = sys.excepthook

    err_workbench.register(UIManifest())
    err_workbench.register(LifecycleManifest())
    core = err_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.errors.install_excepthook")

    new_hook = sys.excepthook
    sys.excepthook = old_hook

    assert old_hook is not new_hook

    try:
        raise Exception()
    except Exception:
        with handle_dialog(gild_qtbot):
            new_hook(*sys.exc_info())


# =============================================================================
# --- Test error handler ------------------------------------------------------
# =============================================================================


def test_reporting_single_error(err_workbench):
    """Check handling a single error."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["error"]

    assert handler.handle(err_workbench, {"message": "test"})

    assert "No message" in handler.handle(err_workbench, {}).text


def test_reporting_multiple_errors(err_workbench):
    """Check handling multiple errors."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["error"]

    assert handler.handle(err_workbench, [{"message": "test"}])

    assert "No message" in handler.handle(err_workbench, {}).text


# =============================================================================
# --- Test registering handler ------------------------------------------------
# =============================================================================


def test_reporting_single_registering_error(err_workbench):
    """Check handling a single registering error."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["registering"]

    assert handler.handle(err_workbench, {"id": "test", "message": "test"})

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


def test_reporting_multiple_registering_errors(err_workbench):
    """Check handling multiple package errors."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["registering"]

    assert handler.handle(err_workbench, [{"id": "test", "message": "test"}])

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


# =============================================================================
# --- Test extensions handler -------------------------------------------------
# =============================================================================


def test_handling_single_extension_error(err_workbench):
    """Check handling a single extension error."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["extensions"]

    assert handler.handle(err_workbench, {"point": "test", "errors": {}})

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


def test_handling_multiple_extension_errors(err_workbench):
    """Check handling multiple extension errors."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["extensions"]

    assert handler.handle(err_workbench, [{"point": "test", "errors": {}}])

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


def test_reporting_on_extension_errors(gild_qtbot, err_workbench):
    """Check reporting extension errors."""
    plugin = err_workbench.get_plugin("gild.errors")
    handler = plugin._errors_handlers.contributions["extensions"]

    widget = handler.report(err_workbench)
    assert isinstance(widget, MultilineField)
    show_and_close_widget(gild_qtbot, widget)

    handler.errors = {"test": {"errror": "msg"}}

    widget = handler.report(err_workbench)
    assert isinstance(widget, HierarchicalErrorsDisplay)
    show_and_close_widget(gild_qtbot, widget)
