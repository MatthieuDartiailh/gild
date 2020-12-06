# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""State plugin definition.

"""
import contextlib
from typing import Any, Iterator, Mapping, Tuple

from atom.api import Atom, Bool, Dict, Typed, Value
from enaml.workbench.api import Plugin

from glaze.utils.plugin_tools import ExtensionsCollector

from .state import State


class _StateHolder(Atom):
    """Base class for all state holders of the state plugin.

    This base class is subclassed at runtime to create custom Atom object with
    the right members.

    """

    #: Is the plugin linked to this state alive or not.
    alive = Bool(True)

    #: Private flag allowing to block manual update of the state.
    _allow_set = Bool(False)

    # We cannot use Atom.freeze here since Atom does not expose an unfreeze
    def __setattr__(self, name, value):
        if self._allow_set or name == "_allow_set":
            super(_StateHolder, self).__setattr__(name, value)
        else:
            raise AttributeError("Attributes of states holder are read-only")

    @contextlib.contextmanager
    def _setting_allowed(self) -> Iterator[None]:
        """Context manager to prevent users of the state to corrupt it.

        Only the plugin using the state should ever use this context manager.

        """
        self._allow_set = True
        try:
            yield
        finally:
            self._allow_set = False

    def _updater(self, changes: Mapping[str, Any]) -> None:
        """Observer handler keeping the state up to date with the plugin."""
        with self._setting_allowed():
            setattr(self, changes["name"], changes["value"])


STATE_POINT = "glaze.states.state"


class StatePlugin(Plugin):
    """A plugin to manage application wide available states."""

    def start(self) -> None:
        """Start the plugin life-cycle."""

        def _validate(state: State) -> Tuple[bool, str]:
            msg = "State does not declare any sync members."
            return bool(state.sync_members), msg

        self._states = ExtensionsCollector(
            workbench=self.workbench,
            point=STATE_POINT,
            ext_class=State,
            validate_ext=_validate,
        )

        self._states.observe("contributions", self._notify_states_death)
        self._states.start()

    def stop(self) -> None:
        """Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        self._states.unobserve("contributions", self._notify_states_death)
        self._states.stop()

    def get_state(self, state_id: str) -> _StateHolder:
        """Return the state associated to the given id."""
        if state_id not in self._living_states:
            state_obj = self._build_state(state_id)
            self._living_states[state_id] = state_obj

        return self._living_states[state_id]

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: ExtensionsCollector keeping track of the declared states.
    _states = Typed(ExtensionsCollector)

    #: Dictionary keeping track of created and live states objects.
    _living_states = Dict()

    def _build_state(self, state_id: str) -> _StateHolder:
        """Create a custom _StateHolder class at runtime and instantiate it.

        Parameters
        ----------
        state_id : unicode
            Id of the state to return.

        Returns
        -------
        state : _StateHolder
            State reflecting the sync_members of the plugin to which it is
            linked.

        """
        state = self._states.contributions[state_id]

        # Create the class name
        class_name = "".join([s.capitalize() for s in state_id.split(".")])

        members = {}
        for m in state.sync_members:
            members[m] = Value()
        state_class = type(class_name, (_StateHolder,), members)

        # Instantiation , initialisation, and binding of the state object to
        # the plugin declaring it.
        state_object = state_class()
        extension = self._states.contributed_by(state_id)
        plugin = self.workbench.get_plugin(extension.plugin_id)
        with state_object._setting_allowed():
            for m in state.sync_members:
                setattr(state_object, m, getattr(plugin, m))
            plugin.observe(m, state_object._updater)

        return state_object

    def _notify_states_death(self, change: Mapping[str, Any]) -> None:
        """Notify that the plugin contributing a state is not plugged anymore.

        This method is used to observe the contribution member of the _states.

        """
        if "oldvalue" in change:
            deads = set(change["oldvalue"]) - set(change["value"])
            for dead in deads:
                if dead in self._living_states:
                    state = self._living_states[dead]
                    with state.setting_allowed():
                        state.alive = False
                    del self._living_states[dead]
