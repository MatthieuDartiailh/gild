# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Managing preferences saving/loading.

"""
import enaml

from .preferences import Preferences

with enaml.imports():
    from .manifest import PreferencesManifest

__all__ = ["Preferences", "PreferencesManifest"]
