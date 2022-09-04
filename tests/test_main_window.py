# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2022 by Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""App plugin extensions declarations.

"""
import enaml
import pytest
from enaml.workbench.workbench import Workbench

from gild.plugins.errors import ErrorsManifest
from gild.plugins.lifecycle import LifecycleManifest

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest

    from .app_helpers import ClosedContributor, ClosingContributor1


@pytest.fixture
def workbench_and_tools(gild_qtbot):
    """Create a workbench to test closing of the application window."""
    workbench = Workbench()
    workbench.register(CoreManifest())
    workbench.register(UIManifest())
    workbench.register(LifecycleManifest())
    workbench.register(ErrorsManifest())
    closing = ClosingContributor1()
    workbench.register(closing)
    closed = ClosedContributor()
    workbench.register(closed)

    return workbench, closing, closed


def test_app_window(gild_qtbot, workbench_and_tools):
    """Test that closing and closed handlers are called when trying to close
    the app window.

    """
    w, closing, closed = workbench_and_tools

    ui = w.get_plugin("enaml.workbench.ui")
    ui.show_window()

    ui.close_window()

    def assert_closing_called():
        assert closing.called

    gild_qtbot.wait_until(assert_closing_called)
    assert ui.window.visible

    closing.accept = True
    ui.close_window()

    def assert_closed_called():
        assert closed.called

    gild_qtbot.wait_until(assert_closed_called)
    assert not ui.window.visible
