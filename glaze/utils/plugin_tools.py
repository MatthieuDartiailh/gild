# -----------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Useful tools to avoid code duplication when writing plugins.

"""
from collections import defaultdict
from typing import Any, Callable as TypedCallable, Iterable, Mapping, Tuple, Union

from atom.api import Atom, Callable, Coerced, Dict, List, Str, Typed
from enaml.workbench.api import Extension, Plugin, Workbench
from enaml.workbench.core.execution_event import ExecutionEvent

from .atom_util import preferences_from_members, update_members_from_preferences


class HasPreferencesPlugin(Plugin):
    """Base class for plugin using preferences.

    Simply defines the most basic preferences system inherited from
    HasPrefAtom. Preferences are automatically queried and saved using the
    glaze.preferences plugin.

    """

    update_members_from_preferences = update_members_from_preferences

    preferences_from_members = preferences_from_members

    def start(self):
        """Upon starting initialize members using preferences."""
        core = self.workbench.get_plugin("enaml.workbench.core")

        prefs = core.invoke_command(
            "glaze.preferences.get", {"plugin_id": self.manifest.id}
        )

        self.update_members_from_preferences(prefs)
        core.invoke_command(
            "glaze.preferences.plugin_init_complete", {"plugin_id": self.manifest.id}
        )


def make_handler(id: str, method_name: str) -> TypedCallable[[ExecutionEvent], Any]:
    """Generate a generic handler calling a plugin method.

    Parameters
    ----------
    id : str
        Id of the plugin on which the method is defined
    method_name : str
        Name of teh method to call.

    """

    def handler(event: ExecutionEvent) -> Any:
        """Handler getting the method corresponding to the command from the
        plugin.

        """
        pl = event.workbench.get_plugin(id)
        return getattr(pl, method_name)(**event.parameters)

    handler.__name__ += "_" + method_name
    return handler


def make_extension_validator(
    base_cls: type,
    fn_names: Iterable[str] = (),
    attributes: Iterable[str] = ("description",),
) -> TypedCallable[[Any], Tuple[bool, str]]:
    """Create an extension validation function checking that key methods were
    overridden and attributes values provided.

    Parameters
    ----------
    base_cls : type
        Base class from which the contribution should inherit.

    fn_names : iterable[str], optional
        Names of the function the extensions must override.

    attributes : iterable[str], optional
        Names of the attributes the extension should provide values for.

    Returns
    -------
    validator : callable
        Function that can be used to validate an extension contribution.

    """

    def validator(contrib: Any) -> Tuple[bool, str]:
        """Validate the children of an extension."""
        for name in fn_names:
            member = getattr(contrib, name)
            func = getattr(member, "__func__", None)
            o_func = getattr(base_cls, name)
            if not func or func is o_func:
                msg = f"{base_cls} '{contrib.id}' does not declare a {name} function."
                return False, msg

        for attr in attributes:
            if not getattr(contrib, attr):
                msg = "%s %s does not provide a %s"
                return False, msg % (base_cls, contrib.id, attr)

        return True, ""

    doc = "Ensure that %s subclasses does override %s" % (base_cls, fn_names)
    validator.__doc__ = doc

    return validator


class ClassTuple(tuple):
    """Special tuple meant to hold classes.

    Provides an smart constructor and a nice str representation.

    """

    def __new__(cls, vals: Union[type, Tuple[type]]):
        if isinstance(vals, type):
            return tuple.__new__(ClassTuple, [vals])
        else:
            return tuple.__new__(ClassTuple, vals)

    def __str__(self) -> str:
        return ", ".join((c.__name__ for c in self))


class BaseCollector(Atom):
    """Base class for automating extension collection."""

    #: Reference to the application workbench.
    workbench = Typed(Workbench)

    #: Id of the extension point to observe.
    point = Str()

    #: Expected class(es) of the object generated by the extension.
    ext_class = Coerced(ClassTuple)

    #: Dictionary storing the contributions of the observed extension point.
    #: This should not be altered by user code. This is never modified in place
    #: so user code will get reliable notifications when observing it.
    contributions = Dict()

    def start(self) -> None:
        """Run first collections of contributions and set up observers.

        This method should be called in the start method of the plugin using
        this object.

        """
        self._refresh_contributions()
        self._bind_observers()

    def stop(self) -> None:
        """Unbind observers and clean up ressources.

        This method should be called in the stop method of the plugin using
        this object.

        """
        self._unbind_observers()
        self.unobserve("contributions")  # Dicsonnect all observers
        self.contributions.clear()
        self._extensions.clear()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Private storage keeping track of which extension declared which object.
    _extensions = Typed(defaultdict, (list,))

    def _refresh_contributions(self) -> None:
        """Refresh the extensions contributions.

        This method should be called in the start method of the plugin using
        this object.

        """
        raise NotImplementedError()

    def _on_contribs_updated(self, change: Mapping[str, Any]) -> None:
        """The observer for the extension point"""
        raise NotImplementedError()

    def _bind_observers(self) -> None:
        """Setup the observers for the extension point.

        This method should be called in the start method of the plugin using
        this object.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(self.point)
        point.observe("extensions", self._on_contribs_updated)

    def _unbind_observers(self) -> None:
        """Remove the observers for the plugin.

        This method should be called in the stop method of the plugin using
        this object.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(self.point)
        point.unobserve("extensions", self._on_contribs_updated)


class ExtensionsCollector(BaseCollector):
    """Convenience class collecting an extension point contribution.

    This class can be used on any extension point to which extensions
    contribute instances of a specific class. Those object should always have
    an id member.

    """

    #: Callable to use to ensure that the provided extension does fit.
    #: Should take the proposed contribution as single argument and return a
    #: bool indicating the result of the test, and a message  explaining what
    #: went wrong (or an empty string if test passed).
    validate_ext = Callable(lambda e: (True, ""))

    def contributed_by(self, contrib_id: str) -> Extension:
        """Find the extension declaring a contribution."""
        contrib = self.contributions[contrib_id]
        for ext, cs in self._extensions.items():
            if contrib in cs:
                return ext

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Private storage keeping track of which extension declared which object.
    _extensions = Typed(defaultdict, (list,))

    def _refresh_contributions(self) -> None:
        """Refresh the extensions contributions.

        This method should be called in the start method of the plugin using
        this object.

        """
        tb = {}
        workbench = self.workbench
        point = workbench.get_extension_point(self.point)

        # If no extension remain clear everything
        if not point or not point.extensions:
            # Force a notification to be emitted.
            self.contributions = {}
            self._extensions.clear()
            return

        extensions = point.extensions

        # Get the contributions declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._extensions
        for extension in extensions:
            if extension in old_extensions:
                contribs = old_extensions[extension]
            else:
                try:
                    contribs = self._load_contributions(extension)
                except TypeError as e:
                    tb["Extension " + extension.qualified_id] = "{}".format(e)
                    continue
            new_extensions[extension].extend(contribs)

        # Create mapping between contrib id and declaration.
        contribs = {}
        for extension in extensions:
            for contrib in new_extensions[extension]:
                if contrib.id in contribs:
                    msg = "{} attempted to register already registered '{}'"
                    pattern = "Duplicate " + contrib.id + "_{}"
                    i = 0
                    while pattern.format(i) in tb:
                        i += 1
                    tb[pattern.format(i)] = msg.format(
                        extension.qualified_id, contrib.id
                    )
                res, msg = self.validate_ext(contrib)
                if not res:
                    ext = "While loading {},".format(extension.qualified_id)
                    tb[contrib.id] = ext + msg
                contribs[contrib.id] = contrib

        self.contributions = contribs
        self._extensions = new_extensions
        if tb:
            core = self.workbench.get_plugin("enaml.workbench.core")
            core.invoke_command(
                "glaze.errors.signal",
                {"kind": "extensions", "point": self.point, "errors": tb},
            )

    def _load_contributions(self, extension: Extension) -> list:
        """Load the contributed objects for the given extension.

        Parameters
        ----------
        extension : Extension
            The extension object of interest.

        Returns
        -------
        contribs : list
            The objects declared by the extension.

        """
        workbench = self.workbench
        contribs = extension.get_children(self.ext_class)
        if extension.factory is not None and not contribs:
            for contrib in extension.factory(workbench):
                if not isinstance(contrib, self.ext_class):
                    msg = "extension '{}' created non-{}."
                    raise TypeError(msg.format(extension.qualified_id, self.ext_class))
                contribs.append(contrib)

        return contribs

    def _on_contribs_updated(self, change: Mapping[str, Any]) -> None:
        """The observer for the extension point"""
        self._refresh_contributions()


class DeclaratorCollector(BaseCollector):
    """Class registering Declarator contributed to an extension point.

    This class can be used on any extension point to which extensions
    contribute Declarator.

    """

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Temporary list in which declarations which cannot yet be taken into
    #: account because another declaration has not yet been registered.
    _delayed = List()

    def _refresh_contributions(self) -> None:
        """Load all extensions contributed to the observed point."""
        workbench = self.workbench
        point = workbench.get_extension_point(self.point)
        extensions = point.extensions

        self._register_decls(extensions)

    def _register_decls(self, extensions: Iterable[Extension]) -> None:
        """Register the declaration linked to some extensions.

        Handle multiple registering attempts.

        """
        # Get the declarators for all extensions.
        tb = {}
        contributions = self.contributions.copy()
        new_extensions = defaultdict(list)
        old_extensions = self._extensions
        for extension in extensions:
            if extension not in old_extensions:
                try:
                    declarators = self._get_decls(extension)
                except TypeError as e:
                    tb["Extension " + extension.qualified_id] = "{}".format(e)
                    continue
            new_extensions[extension].extend(declarators)

        # Register all contributions.
        for extension in new_extensions:
            for declarator in new_extensions[extension]:
                declarator.register(self, tb)

        # Handle delayed registering.
        old = 0
        while old != len(self._delayed) and self._delayed:
            # Copy and clean delayed list.
            delayed = self._delayed[:]
            old = len(delayed)
            self._delayed = []

            # Attempt to re-register delayed declarators
            for declarator in delayed:
                declarator.register(self, tb)

        if self._delayed:
            msg = "Some declarations have not been registered : {}"
            tb["Missing declarations"] = msg.format(self._delayed)

        self._extensions.update(new_extensions)

        if self.contributions != contributions:
            c = self.contributions
            with self.suppress_notifications():
                self.contributions = contributions
            self.contributions = c

        if tb:
            core = self.workbench.get_plugin("enaml.workbench.core")
            core.invoke_command(
                "glaze.errors.signal",
                {"kind": "extensions", "point": self.point, "errors": tb},
            )

    def _get_decls(self, extension: Extension) -> List:
        """Get the task declarations declared by an extension."""
        workbench = self.workbench
        contribs = extension.get_children(self.ext_class)
        if extension.factory is not None and not contribs:
            for contrib in extension.factory(workbench):
                if not isinstance(contrib, self.ext_class):
                    msg = "Extension '{}' should create {} not {}."
                    raise TypeError(
                        msg.format(
                            extension.qualified_id,
                            self.ext_class,
                            type(contrib).__name__,
                        )
                    )
                contribs.append(contrib)

        return contribs

    def _unregister_decls(self, extensions: Mapping[Extension, List]) -> None:
        """Unregister the declarations linked to some extensions."""
        contributions = self.contributions.copy()
        for extension in extensions:
            for declarator in extensions[extension]:
                declarator.unregister(self)
            del self._extensions[extension]

        if self.contributions != contributions:
            c = self.contributions
            with self.suppress_notifications():
                self.contributions = contributions
            self.contributions = c

    def _on_contribs_updated(self, change: Mapping[str, Any]) -> None:
        """Update the registered declarations when an extension is
        added/removed.

        """
        old = set(change.get("oldvalue", ()))
        new = set(change["value"])
        # If no extension remain clear everything
        if not new:
            # Force a notification to be emitted.
            self.contributions = {}
            self._extensions.clear()
            return

        added = new - old
        removed = old - new
        self._unregister_decls(
            {ext: d for ext, d in self._extensions.items() if ext in removed}
        )

        self._register_decls(added)
