# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
""" Plugin handling loading extension packages at startup.

"""
import enaml

with enaml.imports():
    from .manifest import PackagesManifest


__all__ = ["PackagesManifest"]
