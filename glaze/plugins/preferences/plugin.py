# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Preferences plugin definition.

"""
import os
from collections import OrderedDict
from functools import partial
from typing import Any
from typing import Dict as TypedDict
from typing import Optional

import toml
from atom.api import Dict, Str, Typed
from enaml.workbench.api import Plugin

from .preferences import Preferences

PREFS_POINT = "glaze.preferences.plugin"


class PrefPlugin(Plugin):
    """Plugin responsible for managing the application preferences."""

    #: Folder used by the application to store informations such as preferences
    #: log files, ...
    app_directory = Str()

    #: Path of the last location visited using a dialog.
    last_directory = Str()

    def start(self) -> None:
        """Start the plugin, locate app folder and load default preferences."""
        # Look for the app specific storage under the user to locate the application
        # folder that may be stored somewhere else.
        storage_path = os.path.join(os.path.expanduser("~"), self.location_file)
        if os.path.isfile(storage_path):
            self.app_directory = app_path = toml.load(storage_path)["app_path"]
        else:
            raise RuntimeError(
                "The location file does not exist. This should "
                "never happen since it is created during the app startup, "
                "ensure that the preference plugin startup sequence runs before "
                "starting teh plugin."
            )
        self.app_directory = app_path
        self._prefs = OrderedDict()

        pref_path = os.path.join(app_path, "preferences")
        if not os.path.isdir(pref_path):
            os.mkdir(pref_path)

        default_pref_path = os.path.join(pref_path, "default.ini")
        if os.path.isfile(default_pref_path):
            self._prefs = toml.load(default_pref_path, OrderedDict)

        self._refresh_pref_decls()
        self._bind_observers()

    def stop(self) -> None:
        """Stop the plugin."""
        self._unbind_observers()
        self._pref_decls.clear()
        del self._prefs

    def save_preferences(self, path: Optional[str] = None) -> None:
        """Collect and save preferences for all registered plugins.

        Parameters
        ----------
        path : str, optional
            Path of the file in which save the preferences. In its absence
            the default file is used.

        """
        if path is None:
            path = os.path.join(self.app_directory, "preferences", "default.ini")

        prefs = OrderedDict()
        for plugin_id in self._pref_decls:
            plugin = self.workbench.get_plugin(plugin_id)
            decl = self._pref_decls[plugin_id]
            save_method = getattr(plugin, decl.saving_method)
            prefs[plugin_id] = save_method()

        with open(path, "w") as f:
            toml.dump(prefs, f)

    def load_preferences(self, path: Optional[str] = None) -> None:
        """Load preferences and update all registered plugin.

        Parameters
        ----------
        path : str, optional
            Path to the file storing the preferences. In its absence default
            preferences are loaded.

        """
        if path is None:
            path = os.path.join(self.app_directory, "preferences", "default.ini")

        if not os.path.isfile(path):
            return

        prefs = toml.load(path, OrderedDict)
        self._prefs.merge(prefs)
        for plugin_id in prefs:
            if plugin_id in self._pref_decls:
                plugin = self.workbench.get_plugin(plugin_id, force_create=False)
                if plugin:
                    decl = self._pref_decls[plugin_id]
                    load_method = getattr(plugin, decl.loading_method)
                    load_method(prefs[plugin_id])

    def plugin_init_complete(self, plugin_id: str) -> None:
        """Notify the preference plugin that a plugin has started properly.

        The associated command should be called by a plugin once it has started
        and loaded its preferences. This call is necessary to avoid overriding
        values for auto-save members by default values.

        Parameters
        ----------
        plugin_id : str
            Id of the plugin which has started.

        """
        plugin = self.workbench.get_plugin(plugin_id)
        pref_decl = self._pref_decls[plugin_id]
        for member in pref_decl.auto_save:
            # Custom observer which does not rely on the fact that the object
            # in the change dictionnary is a plugin
            observer = partial(self._auto_save_update, plugin_id)
            plugin.observe(member, observer)

    def get_plugin_preferences(self, plugin_id: str) -> TypedDict[str, Any]:
        """Access to the preferences values stored for a plugin.

        Parameters
        ----------
        plugin_id : unicode
            Id of the plugin whose preferences values should be returned.

        Returns
        -------
        prefs : dict(str, str)
            Preferences for the plugin as a dict.

        """
        if plugin_id not in self._pref_decls:
            msg = "Plugin %s is not registered in the preferences system"
            raise KeyError(msg % plugin_id)

        if plugin_id in self._prefs:
            return self._prefs[plugin_id]

        return {}

    def open_editor(self):
        """"""
        pass
        # TODO here must build all editors from declaration, open dialog
        # and manage the update if the user validate.

    # =========================================================================
    # ---- Private API --------------------------------------------------------
    # =========================================================================

    #: Ordered dict in which the preferences are stored
    _prefs = Typed(OrderedDict)

    #: Mapping between plugin_id and the declared preferences.
    _pref_decls = Dict()

    # TODO : low priority : refactor using Declarator pattern
    def _refresh_pref_decls(self):
        """Refresh the list of states contributed by extensions."""
        workbench = self.workbench
        point = workbench.get_extension_point(PREFS_POINT)
        extensions = point.extensions

        # If no extension remain clear everything
        if not extensions:
            self._pref_decls.clear()
            return

        # Map extension to preference declaration
        new_ids = dict()
        old_ids = self._pref_decls
        for extension in extensions:
            if extension.plugin_id in old_ids:
                pref = old_ids[extension.plugin_id]
            else:
                pref = self._load_pref_decl(extension)
            new_ids[extension.plugin_id] = pref

        self._pref_decls = new_ids

    def _load_pref_decl(self, extension):
        """Get the Preferences contributed by an extension

        Parameters
        ----------
        extension : Extension
            Extension contributing to the pref extension point.

        Returns
        -------
        pref_decl : Preferences
            Preference object contributed by the extension.

        """
        # Getting the pref declaration contributed by the extension, either
        # as a child or returned by the factory. Only the first state is
        # considered.
        workbench = self.workbench
        prefs = extension.get_children(Preferences)
        if extension.factory is not None and not prefs:
            pref = extension.factory(workbench)
            if not isinstance(pref, Preferences):
                msg = "extension '%s' created non-Preferences of type '%s'"
                args = (extension.qualified_id, type(pref).__name__)
                raise TypeError(msg % args)
        else:
            pref = prefs[0]

        return pref

    def _auto_save_update(self, plugin_id: str, change: TypedDict[str, Any]) -> None:
        """Observer for the auto-save members

        Parameters
        ----------
        plugin_id : str
            Id of the plugin owner of the member being observed

        change : dict
            Change dictionnary given by Atom

        """
        name = change["name"]
        value = change["value"]
        if plugin_id in self._prefs:
            self._prefs[plugin_id][name] = value
        else:
            self._prefs[plugin_id] = {name: value}

        self._prefs.write()

    def _on_pref_decls_updated(self, change: TypedDict[str, Any]) -> None:
        """The observer for the preferences extension point"""
        self._refresh_pref_decls()

    def _bind_observers(self) -> None:
        """Setup the observers for the plugin."""
        workbench = self.workbench
        point = workbench.get_extension_point(PREFS_POINT)
        point.observe("extensions", self._on_pref_decls_updated)

    def _unbind_observers(self) -> None:
        """Remove the observers for the plugin."""
        workbench = self.workbench
        point = workbench.get_extension_point(PREFS_POINT)
        point.unobserve("extensions", self._on_pref_decls_updated)
