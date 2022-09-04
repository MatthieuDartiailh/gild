# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Declarative class for defining hnadling of preferences.

"""
from sqlite3 import paramstyle

from atom.api import List, Property, Str
from enaml.core.api import Declarative, d_, d_func
from enaml.widgets.container import Container
from enaml.workbench.api import PluginManifest, Workbench


class Preferences(Declarative):
    """Declarative class for defining a workbench preference contribution.

    Preferences object can be contributed as extensions child to the "plugin"
    extension point of a preference plugin.

    """

    #: Id of the contribution. This MUST match the declaring plugin.
    id = d_(Property(), writable=False, final=True)

    #: Short description of what is expected to be saved.
    description = d_(Str())

    #: Name of the method of the plugin contributing this extension to call
    #: when the preference plugin need to save the preferences.
    saving_method = d_(Str("preferences_from_members"))

    #: Name of the method of the plugin contributing this extension to call
    #: when the preference plugin need to load preferences.
    loading_method = d_(Str("update_members_from_preferences"))

    #: The list of plugin members whose values should be observed and whose
    #: update should cause and automatic update of the preferences.
    auto_save = d_(List())

    #: A callable taking the plugin_id and the preference declaration as arg
    #: and returning an autonomous enaml view (Container) used to edit
    #: the preferences.
    @d_func
    def edit_view(self, workbench: Workbench, id: str) -> Container:
        """Create a view to edit the preferences.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        id : str
            Id of the plugin for which to generate the view.

        Returns
        -------
        view : enaml.widgets.api.Container
            View used to edit the preferences. It should have a model
            attribute. The model members must correspond to the tagged members
            the plugin, their values will be used to update the preferences.

        """
        pass

    # --- Private API

    def _get_id(self) -> str:
        parent = self.parent
        while not isinstance(parent, PluginManifest):
            parent = parent.parent
        return parent.id
