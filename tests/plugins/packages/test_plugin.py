# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2022 by Glaze Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the PackagesPlugin.

"""
import enaml
import pytest
from atom.api import Atom, Bool, Str, Value

from glaze.plugins.errors import ErrorsManifest
from glaze.plugins.lifecycle import LifecycleManifest
from glaze.plugins.packages import PackagesManifest
from glaze.testing.util import handle_dialog

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from .packages_utils import Manifest1, Manifest2


APP_ID = "glaze.lifecycle"
PACKAGES_ID = "glaze.packages"


@pytest.fixture
def pack_workbench(workbench):
    """Create a workbench and register basic manifests."""
    workbench.register(CoreManifest())
    workbench.register(LifecycleManifest())
    workbench.register(ErrorsManifest())
    workbench.register(PackagesManifest())
    return workbench


def patch_pkg(monkey, answer):
    """Patch the pkg_resources.iter_entry_points function."""
    from glaze.plugins.packages.plugin import pkg_resources

    monkey.setattr(pkg_resources, "iter_entry_points", lambda x: answer)


class FalseEntryPoint(Atom):
    """False entry whose behavior can be customized."""

    #: Name of this entry point
    name = Str()

    #: Flag indicating whether the require method should raise an error.
    missing_require = Bool()

    #: List of manifest to return when load method is called.
    manifests = Value()

    def require(self):
        if self.missing_require:
            raise Exception()
        return True

    def load(self):
        return lambda: self.manifests


def test_collecting_registering_and_stopping(monkeypatch, pack_workbench, glaze_qtbot):
    """Test basic behavior of PackaggesPlugin."""
    patch_pkg(
        monkeypatch,
        [
            FalseEntryPoint(name="test", manifests=[Manifest1, Manifest2]),
            FalseEntryPoint(name="test2", manifests=[]),
        ],
    )

    app = pack_workbench.get_plugin(APP_ID)
    app.run_app_startup(object())

    def assert_registered():
        plugin = pack_workbench.get_plugin(PACKAGES_ID)
        assert "test" in plugin.packages

    glaze_qtbot.wait_until(assert_registered)

    plugin = pack_workbench.get_plugin(PACKAGES_ID)
    assert "test2" in plugin.packages
    assert "glaze.test1" in plugin.packages["test"]
    assert "glaze.test2" in plugin.packages["test"]
    assert (100, 0, "glaze.test1") in plugin._registered
    assert (0, 1, "glaze.test2") in plugin._registered
    assert pack_workbench.get_plugin("glaze.test1")
    assert pack_workbench.get_plugin("glaze.test2")

    pack_workbench.unregister(PACKAGES_ID)

    with pytest.raises(ValueError):
        pack_workbench.get_plugin("glaze.test1")
    with pytest.raises(ValueError):
        pack_workbench.get_plugin("glaze.test2")


def test_unmet_requirement(monkeypatch, pack_workbench, glaze_qtbot):
    """Test loading an extension package for which some requirements are not
    met.

    """
    patch_pkg(
        monkeypatch,
        [
            FalseEntryPoint(name="test", missing_require=True),
            FalseEntryPoint(name="test2", manifests=[]),
        ],
    )

    app = pack_workbench.get_plugin(APP_ID)
    with handle_dialog(glaze_qtbot):
        app.run_app_startup(object())

    plugin = pack_workbench.get_plugin(PACKAGES_ID)

    assert "test" in plugin.packages
    assert "test2" in plugin.packages
    assert "load" in plugin.packages["test"]
    assert not plugin._registered


def test_wrong_return_type(monkeypatch, pack_workbench, glaze_qtbot):
    """Test handling a wrong return type from the callable returned by load."""
    patch_pkg(
        monkeypatch,
        [
            FalseEntryPoint(name="test", manifests=Manifest1),
            FalseEntryPoint(name="test2", manifests=[]),
        ],
    )

    app = pack_workbench.get_plugin(APP_ID)
    with handle_dialog(glaze_qtbot):
        app.run_app_startup(object())

    plugin = pack_workbench.get_plugin(PACKAGES_ID)

    assert "test" in plugin.packages
    assert "test2" in plugin.packages
    assert "list" in plugin.packages["test"]
    assert not plugin._registered


def test_non_manifest(monkeypatch, pack_workbench, glaze_qtbot):
    """Test handling a non PluginManifest in the list of manifests."""
    patch_pkg(
        monkeypatch,
        [
            FalseEntryPoint(name="test", manifests=[Manifest1, object]),
            FalseEntryPoint(name="test2", manifests=[]),
        ],
    )

    app = pack_workbench.get_plugin(APP_ID)
    with handle_dialog(glaze_qtbot):
        app.run_app_startup(object())

    plugin = pack_workbench.get_plugin(PACKAGES_ID)

    assert "test" in plugin.packages
    assert "test2" in plugin.packages
    assert "PluginManifests" in plugin.packages["test"]
    assert not plugin._registered


def test_registering_issue(monkeypatch, pack_workbench, glaze_qtbot):
    """Test handling an error when registering a manifest."""
    patch_pkg(
        monkeypatch,
        [
            FalseEntryPoint(name="test", manifests=[Manifest1, Manifest1]),
            FalseEntryPoint(name="test2", manifests=[]),
        ],
    )

    app = pack_workbench.get_plugin(APP_ID)
    with handle_dialog(glaze_qtbot):
        app.run_app_startup(object())

    plugin = pack_workbench.get_plugin(PACKAGES_ID)

    assert "test" in plugin.packages
    assert "test2" in plugin.packages
    assert "glaze.test1" in plugin.packages["test"]
    assert len(plugin.packages["test"]) == 1


def test_reporting_single_package_error(pack_workbench):
    """Check handling a single package error."""
    plugin = pack_workbench.get_plugin("glaze.errors")
    handler = plugin._errors_handlers.contributions["package"]

    assert handler.handle(pack_workbench, {"id": "test", "message": "test"})

    with pytest.raises(Exception):
        handler.handle(pack_workbench, {})


def test_reporting_multiple_package_error(pack_workbench):
    """Check handling multiple package errors."""
    plugin = pack_workbench.get_plugin("glaze.errors")
    handler = plugin._errors_handlers.contributions["package"]

    assert handler.handle(pack_workbench, [{"id": "test", "message": "test"}])

    with pytest.raises(Exception):
        handler.handle(pack_workbench, {})
