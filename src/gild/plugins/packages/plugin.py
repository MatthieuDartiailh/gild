# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Plugin handling the collection and registering of extension packages.

"""
import logging
from traceback import format_exc
from typing import MutableMapping, Union

import pkg_resources
from atom.api import Dict, List, Str
from enaml.workbench.api import Plugin, PluginManifest

logger = logging.getLogger(__name__)


class PackagesPlugin(Plugin):
    """Collect and register all manifest contributed by extension packages."""

    #: Dictionary listing the extension packages registered at startup, each
    #: entries can contain either a dict listing the id of the registered
    #: manifest with a message indicating whether registering succeeded, or
    #: a message explaining why the package was not loaded.
    packages = Dict()

    def stop(self) -> None:
        """Unregister all manifest contributed by extension packages."""
        # Sort to respect the given priority when unregistering.
        heap = sorted(self._registered)
        for manifest_id in heap:
            self.workbench.unregister(manifest_id[2])

        self.packages.clear()
        self._registered = []

    def collect_and_register(self) -> None:
        """Iter over packages and register the manifest they are providing."""
        # Getting core plugin to signal errors.
        core = self.workbench.get_plugin("enaml.workbench.core")
        cmd = "gild.errors.signal"

        packages: MutableMapping[str, Union[str, MutableMapping[str, str]]] = dict()
        registered: List[PluginManifest] = []
        core.invoke_command("gild.errors.enter_error_gathering", {})
        for ep in pkg_resources.iter_entry_points(self.manifest.extension_point):

            # Check that all dependencies are satisfied.
            try:
                ep.require()
            except Exception:
                msg = "Could not load extension package %s : %s"
                msg = msg % (ep.name, format_exc())
                packages[ep.name] = msg
                core.invoke_command(cmd, dict(kind="package", id=ep.name, message=msg))
                continue

            # Get all manifests
            manifests = ep.load()()
            if not isinstance(manifests, list):
                msg = "Package %s entry point must return a list, not %s"
                msg = msg % (ep.name, str(type(manifests)))
                packages[ep.name] = msg
                core.invoke_command(cmd, dict(kind="package", id=ep.name, message=msg))
                continue

            if any(not issubclass(m, PluginManifest) for m in manifests):
                msg = "Package %s entry point must only return PluginManifests"
                msg = msg % ep.name
                packages[ep.name] = msg
                core.invoke_command(cmd, dict(kind="package", id=ep.name, message=msg))
                continue

            ext_pack_contrib: MutableMapping[str, str] = {}
            packages[ep.name] = ext_pack_contrib
            for manifest in manifests:
                inst = manifest()
                try:
                    self.workbench.register(inst)
                except ValueError:
                    core.invoke_command(
                        cmd, dict(kind="registering", id=inst.id, message=format_exc())
                    )
                    continue

                ext_pack_contrib[inst.id] = "Successfully registered"
                priority = getattr(inst, "priority", 100)
                # Keep the insertion index, to avoid comparing id when
                # sorting (it would make no sense).
                registered.append((priority, len(registered), inst.id))

        self.packages = packages
        self._registered = registered
        core.invoke_command("gild.errors.exit_error_gathering", {})

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Private list of registered manifest used when stopping the plugin.
    _registered = List(tuple)
