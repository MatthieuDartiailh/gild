# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Application icons management plugins.

"""
import enaml

from .icon_theme import Icon, IconTheme

with enaml.imports():
    from .manifest import IconManagerManifest


def get_icon(workbench, icon_id):
    """Utility function querying an icon.

    This function is provided to be more compact than using the core plugin.
    All widgets can access the workbench thanks to dynamic scoping if the main
    application window is one of their parent.

    """
    plugin = workbench.get_plugin("gild.icons")
    return plugin.get_icon(icon_id)


__all__ = ["IconTheme", "Icon", "IconManagerManifest", "get_icon"]
