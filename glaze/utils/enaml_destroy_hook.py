# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Mixin class to provide declarative finalization customisations capabilities.

"""
from typing import Type, TypeVar

from atom.api import Event
from enaml.core.api import d_

T = TypeVar("T")


def add_destroy_hook(cls: Type[T]) -> Type[T]:
    """Add a declarative event signaling that an object will be destroyed."""

    class Destroyable(cls):  # type: ignore
        """Subclass overriding the destroy method to emit 'ended' before
        destroying.

        """

        #: Event emitted just before destroying the object.
        ended = d_(Event())

        def destroy(self) -> None:
            """Re-implemented to emit ended before cleaning up the declarative
            structure.

            """
            self.ended = True
            super(Destroyable, self).destroy()

    return Destroyable
