# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2022 by Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Configuartion of the test of the icon manager plugin.

"""
import enaml
import pytest

from gild.plugins.icons import IconManagerManifest
from gild.plugins.preferences import PreferencesManifest

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest


@pytest.fixture
def icon_workbench(workbench, app_name, app_dir):
    """Register the icon manager plugin and dependencies."""
    workbench.register(CoreManifest())
    workbench.register(PreferencesManifest(application_name=app_name))
    workbench.register(IconManagerManifest())

    yield workbench

    for m_id in ("gild.icons", "gild.preferences"):
        try:
            workbench.unregister(m_id)
        except Exception:
            pass
