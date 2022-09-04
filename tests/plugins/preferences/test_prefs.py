# -----------------------------------------------------------------------------
# Copyright 2022 by Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the preferences plugin.

"""
import os
import pathlib

import enaml
import pytest
import toml

from gild.plugins.errors import ErrorsManifest
from gild.plugins.lifecycle import LifecycleManifest
from gild.plugins.preferences import PreferencesManifest
from gild.testing.util import handle_dialog

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from .pref_utils import BadPrefContributor, PrefContributor, PrefContributor2

PLUGIN_ID = "gild.preferences"


@pytest.fixture
def pref_workbench(workbench, app_dir, app_name):
    """Register the plugins resuired to test the preferences plugin."""
    workbench.register(CoreManifest())
    workbench.register(LifecycleManifest())
    workbench.register(ErrorsManifest())
    workbench.register(PreferencesManifest(application_name=app_name))
    return workbench


def test_app_startup1(pref_workbench, app_dir_storage, tmpdir, gild_qtbot):
    """Test app start-up when no app_directory.ini exists."""
    # Remove the default location
    app = pref_workbench.get_plugin("gild.lifecycle")
    app_dir = tmpdir.join("_test")
    if app_dir_storage.is_file():
        os.remove(app_dir_storage)

    # Start the app and fake a user answer.
    with handle_dialog(
        gild_qtbot, handler=lambda bot, d: setattr(d, "path", str(app_dir))
    ):
        app.run_app_startup(object())

    assert app_dir_storage.is_file()
    with open(app_dir_storage) as f:
        assert toml.load(f)["app_path"] == app_dir
    assert os.path.isdir(app_dir)


def test_app_startup2(pref_workbench, app_dir_storage, tmpdir, gild_qtbot):
    """Test app start-up when user quit app."""
    # Remove the default location
    app = pref_workbench.get_plugin("gild.lifecycle")
    if app_dir_storage.is_file():
        os.remove(app_dir_storage)

    # Start the app and fake a user answer.
    app = pref_workbench.get_plugin("gild.lifecycle")

    with pytest.raises(SystemExit):
        with handle_dialog(gild_qtbot, "reject"):
            app.run_app_startup(object())


def test_app_startup3(pref_workbench, app_dir_storage, tmpdir, gild_qtbot):
    """Test app start-up when a preference file already exists."""
    # Remove the default location
    app = pref_workbench.get_plugin("gild.lifecycle")
    app_dir = str(tmpdir.join("_test"))
    with open(app_dir_storage, "w") as f:
        toml.dump(dict(app_path=app_dir), f)

    assert not os.path.isdir(app_dir)

    # Start the app and fake a user answer.
    app = pref_workbench.get_plugin("gild.lifecycle")

    app.run_app_startup(object())

    assert os.path.isdir(app_dir)


def test_app_startup4(pref_workbench, app_dir_storage, tmpdir, gild_qtbot):
    """Test app start-up when user request to reset app folder."""
    app_dir = str(tmpdir.join("_test"))
    app = pref_workbench.get_plugin("gild.lifecycle")

    # Start the app and fake a user answer.
    app = pref_workbench.get_plugin("gild.lifecycle")

    class DummyArgs(object):

        reset_app_folder = True

    with handle_dialog(gild_qtbot, handler=lambda bot, x: setattr(x, "path", app_dir)):
        app.run_app_startup(DummyArgs)

    assert os.path.isfile(app_dir_storage)
    with open(app_dir_storage, "r") as f:
        assert toml.load(f)["app_path"] == app_dir
    assert os.path.isdir(app_dir)


def test_lifecycle(pref_workbench, app_dir):
    """Test the plugin lifecycle when no default.toml exist in app folder."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    # Start preferences plugin.
    prefs = pref_workbench.get_plugin(PLUGIN_ID)
    assert prefs.app_directory == str(app_dir)
    assert (app_dir / "preferences").is_dir()
    core = pref_workbench.get_plugin("enaml.workbench.core")
    assert (
        core.invoke_command("gild.preferences.get", dict(plugin_id="test.prefs"))
        is not None
    )

    pref_workbench.register(PrefContributor2())
    assert (
        core.invoke_command("gild.preferences.get", dict(plugin_id="test.prefs2"))
        is not None
    )

    # Stopping
    pref_workbench.unregister(c_man.id)
    with pytest.raises(KeyError):
        core.invoke_command("gild.preferences.get", dict(plugin_id="test.prefs"))
    pref_workbench.unregister(PrefContributor2().id)
    assert not prefs._prefs


def test_load_defaultini(pref_workbench, app_dir):
    """Test that a default.toml file found in the app folder under prefs
    is loaded on startup.

    """
    prefs_path = app_dir / "preferences"
    prefs_path.mkdir()

    with open(prefs_path / "default.toml", "w") as f:
        c_man = PrefContributor()
        toml.dump({c_man.id: {"string": "This is a test"}}, f)

    pref_workbench.register(c_man)

    c_pl = pref_workbench.get_plugin(c_man.id)

    assert c_pl.string == "This is a test"


# def test_update_contrib_and_type_checking(pref_workbench):
#     """Check that the contributions are correctly updated when a new
#     plugin is registered and check that the contribution is of the right
#     type.

#     """
#     c_man = PrefContributor()
#     pref_workbench.register(c_man)

#     # Start preferences plugin.
#     pref_workbench.get_plugin(PLUGIN_ID)

#     # Test observation of extension point and type checking.
#     b_man = BadPrefContributor()
#     with pytest.raises(TypeError):
#         pref_workbench.register(b_man)


def test_auto_sync(pref_workbench, app_dir):
    """Check that auito_sync members are correctly handled."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.auto = "test_auto"

    ref = {c_man.id: {"auto": "test_auto"}}
    path = app_dir / "preferences" / "default.toml"
    assert os.path.isfile(path)
    with path.open() as f:
        assert toml.load(f) == ref

    contrib.auto = "test"

    ref = {c_man.id: {"auto": "test"}}
    path = app_dir / "preferences" / "default.toml"
    assert os.path.isfile(path)
    with path.open() as f:
        assert toml.load(f) == ref


def test_save1(pref_workbench, app_dir):
    """Test saving to the default file."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.string = "test_save"

    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.preferences.save", {}, pref_workbench)

    path = app_dir / "preferences" / "default.toml"
    ref = {c_man.id: {"string": "test_save", "auto": ""}}
    assert os.path.isfile(path)
    with path.open() as f:
        assert toml.load(f) == ref


def test_save2(pref_workbench, app_dir):
    """Test saving to a specific file."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.string = "test_save"

    path = app_dir / "preferences" / "custom.toml"
    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.preferences.save", {"path": path})

    ref = {c_man.id: {"string": "test_save", "auto": ""}}
    assert os.path.isfile(path)
    with path.open() as f:
        assert toml.load(f) == ref


def test_save3(pref_workbench, app_dir, monkeypatch):
    """Test saving to a specific file."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)

    contrib = pref_workbench.get_plugin(c_man.id)
    contrib.string = "test_save"

    prefs_path = app_dir / "preferences"
    path = prefs_path / "custom.toml"

    @classmethod
    def answer(*args, **kwargs):
        return path

    with enaml.imports():
        from gild.plugins.preferences.manifest import FileDialogEx
    monkeypatch.setattr(FileDialogEx, "get_save_file_name", answer)
    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command(
        "gild.preferences.save", {"path": prefs_path, "ask_user": True}
    )

    ref = {c_man.id: {"string": "test_save", "auto": ""}}
    assert os.path.isfile(path)
    with path.open() as f:
        assert toml.load(f) == ref
    assert pref_workbench.get_plugin(PLUGIN_ID).last_directory == str(prefs_path)


def test_load1(pref_workbench, app_dir):
    """Test loading default preferences for unstarted plugin."""
    # Register and start preferences plugin
    pref_workbench.get_plugin(PLUGIN_ID)

    c_man = PrefContributor()
    pref_workbench.register(c_man)

    path = app_dir / "preferences" / "default.toml"
    with path.open("w") as f:
        toml.dump({c_man.id: {"string": "test"}}, f)

    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.preferences.load", {})
    assert pref_workbench.get_plugin(c_man.id, False) is None
    contrib = pref_workbench.get_plugin(c_man.id)

    assert contrib.string == "test"


def test_load2(pref_workbench):
    """Test loading preferences from non-existing file."""
    pref_workbench.register(PrefContributor())

    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.preferences.load", {"path": ""}, pref_workbench)

    assert not pref_workbench.get_plugin(PLUGIN_ID)._prefs


def test_load3(pref_workbench, app_dir):
    """Test loading preferences from non-default file for started plugin."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)
    contrib = pref_workbench.get_plugin(c_man.id)

    path = app_dir / "preferences" / "custom.ini"
    with path.open("w") as f:
        toml.dump({c_man.id: {"string": "test"}}, f)

    assert contrib.string == ""

    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command("gild.preferences.load", {"path": path}, pref_workbench)

    assert contrib.string == "test"


def test_load4(pref_workbench, app_dir, monkeypatch):
    """Test loading preferences from non-default file for started plugin."""
    c_man = PrefContributor()
    pref_workbench.register(c_man)
    contrib = pref_workbench.get_plugin(c_man.id)

    prefs_path = app_dir / "preferences"
    path = prefs_path / "custom.ini"
    with path.open("w") as f:
        toml.dump({c_man.id: {"string": "test"}}, f)

    assert contrib.string == ""

    @classmethod
    def answer(*args, **kwargs):
        return path

    with enaml.imports():
        from gild.plugins.preferences.manifest import FileDialogEx
    monkeypatch.setattr(FileDialogEx, "get_open_file_name", answer)
    core = pref_workbench.get_plugin("enaml.workbench.core")
    core.invoke_command(
        "gild.preferences.load", {"path": prefs_path, "ask_user": True}, pref_workbench
    )

    assert contrib.string == "test"
    assert pref_workbench.get_plugin(PLUGIN_ID).last_directory == str(prefs_path)
