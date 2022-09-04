# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Utility tools for handling preferences and declaring plugin extensions.

"""
from typing import Any

from enaml.workbench.api import Workbench


# FIXME
def invoke_command(
    workbench: Workbench, cmd: str, parameters: dict, trigger: Any = None
) -> Any:
    """[summary]

    Parameters
    ----------
    workbench : Workbench
        [description]
    cmd : str
        [description]
    parameters : dict
        [description]
    trigger : Any, optional
        [description], by default None

    Returns
    -------
    Any
        [description]
    """
    core = workbench.get_plugin("enaml.workbench.core")
    return core.invoke_command(cmd, parameters, trigger)
