# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""State sharing between plugin (pendant of command plugin).

"""
import enaml

from .state import State

with enaml.imports():
    from .manifest import StateManifest

__all__ = ["State", "StateManifest"]
