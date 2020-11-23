# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Application icons management plugins.

"""
from .icon_theme import Icon, IconTheme


def get_icon(workbench, icon_id):
    """Utility function querying an icon.

    This function is provided to be more compact than using the core plugin.
    All widgets if the main application window is one of their parent can
    access the workbench thanks to dynamic scoping.

    """
    plugin = workbench.get_plugin("glaze.icons")
    return plugin.get_icon(icon_id)


__all__ = ["IconTheme", "Icon", "get_icon"]
