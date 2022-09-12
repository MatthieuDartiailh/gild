# --------------------------------------------------------------------------------------
# Copyright 2022 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Gild is a set of utility to help build plugin application using Enaml.
"""
try:
    import qtpy
except ImportError:
    raise RuntimeError(
        "Currently Gild requires a qt backend to be installed. Since installation do "
        "not support default optional dependencies you have to manually specify the "
        "desired backend when installing"
    )
