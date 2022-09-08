# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Plugin to manage extensions controlling the app life cycle.

If using a custom Workbench window subclass you need to inherit from the
AppWindow to preserve teh life cycle behaviors provided by this plugin.

"""
import enaml

from .extensions import AppClosed, AppClosing, AppStartup

with enaml.imports():
    from .manifest import LifecycleManifest

__all__ = ["AppClosed", "AppClosing", "AppStartup", "LifecycleManifest"]
