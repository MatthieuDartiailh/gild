# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
""" App managed logging.

This plugin offers the possibility to add custom handlers, filters and formatters.

"""
import enaml

with enaml.imports():
    from .manifest import LogManifest

__all__ = ["LogManifest"]
