# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Error reporting through logging and dialogs.

"""
import enaml

from .errors import ErrorHandler

with enaml.imports():
    from .manifest import ErrorsManifest

__all__ = ["ErrorHandler", "ErrorsManifest"]
