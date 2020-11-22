# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base class for extension declaration relying on a visitor pattern.

"""
import re
from importlib import import_module
from traceback import format_exc
from typing import Any, Dict, Optional

from atom.api import Bool, Str
from enaml.core.api import Declarative, d_
from enaml.workbench.api import Plugin

from .plugin_tools import DeclaratorCollector


class Declarator(Declarative):
    """Base class for extension object which uses a visitor pattern."""

    #: Flag indicating whether the declarator has been successfully registered
    is_registered = Bool()

    def get_path(self) -> Optional[str]:
        """Query from parent the path to use for this declarator.

        Returns
        -------
        path : unicode or None
            Path declared by the parent. This can be None if no path is
            declared.

        """
        if isinstance(self.parent, Declarator):
            return self.parent.get_path()
        return None

    def get_group(self) -> Optional[str]:
        """Get the group defined by the closest parent."""
        if not isinstance(self.parent, Declarator):
            return None

        group = getattr(self.parent, "group", None)
        if group:
            return group

        return self.parent.get_group()

    def register(self, collector: DeclaratorCollector, traceback: Dict[str, Any]):
        """Add the contribution of this extension to the plugin.

        Parameters
        ----------
        collector : DeclaratorCollector
            Collector in charge handling the registering of declarators.
            Contributions should be added to the contributions member (Dict).
            If a declarator cannot be registered because another one need to be
            registered first it should add itself to the _delayed member (List)

        traceback : dict
            Dictionary in which any issue occuring during registration should
            be recorded.

        """
        raise NotImplementedError()

    # FIXME
    def unregister(self, plugin) -> None:
        """Remove the contribution of this extension to the plugin.

        Parameters
        ----------
        plugin :
            Collector in charge handling the registering of declarators.

        """
        raise NotImplementedError()

    def __str__(self) -> str:
        """Provide a nice string representation of the object."""
        raise NotImplementedError()


#: Valid paths are names which are dot separated.
PATH_VALIDATOR = re.compile(r"^(\.?\w+)*$")


class GroupDeclarator(Declarator):
    """Declarator used to group an ensemble of declarator."""

    #: Prefix path to use for all children Declarator. Path should be dot
    #: separated.
    path = d_(Str())

    #: Id of the group common to all children Declarator. It is the
    #: responsability of the children to mention they are part of a group.
    group = d_(Str())

    def get_path(self) -> Optional[str]:
        """Overriden method to walk all parents."""
        paths = []
        if isinstance(self.parent, GroupDeclarator):
            parent_path = self.parent.get_path()
            if parent_path:
                paths.append(parent_path)

        if self.path:
            paths.append(self.path)

        if paths:
            return ".".join(paths)
        return None

    def register(self, plugin: Plugin, traceback: Dict[str, Any]) -> None:
        """Register all children Declarator."""
        if not PATH_VALIDATOR.match(self.path):
            msg = "Invalid path {} in {} (path {}, group {})"
            traceback["Error %s" % len(traceback)] = msg.format(
                self.path, type(self), self.path, self.group
            )
            return

        for ch in self.children:
            if not isinstance(ch, Declarator):
                msg = "All children of GroupDeclarator must be Declarator, got"
                traceback["Error %s" % len(traceback)] = msg + "%s" % type(ch)
                continue
            ch.register(plugin, traceback)

        self.is_registered = True

    def unregister(self, plugin: Plugin) -> None:
        """Unregister all children Declarator."""
        if self.is_registered:
            for ch in self.children:
                if isinstance(ch, Declarator):
                    ch.unregister(plugin)

            self.is_registered = False

    def __str__(self) -> str:
        """Identify the declarator by its path and group."""
        st = '{} whose path is "{}" and group is "{}" declaring :\n{}'
        return st.format(
            type(self).__name__,
            self.path,
            self.group,
            "\n".join(" - {}".format(c) for c in self.children),
        )


def import_and_get(path, name: str, traceback: Dict[str, str], id: str) -> None:
    """Function importing a module and retrieving an object from it.

    This function provides a common pattern for declarator.

    """
    import enaml

    try:
        with enaml.imports():
            mod = import_module(path)
    except Exception:
        msg = "Failed to import {} :\n{}"
        traceback[id] = msg.format(path, format_exc())
        return

    try:
        return getattr(mod, name)
    except AttributeError:
        msg = "{} has no attribute {}:\n{}"
        traceback[id] = msg.format(path, name, format_exc())
        return
