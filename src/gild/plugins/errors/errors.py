# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Declarations for the extensions to the error plugin.

"""
from typing import List, Mapping, Union

from atom.api import Str
from enaml.core.api import Declarative, d_, d_func
from enaml.widgets.widget import Widget
from enaml.workbench.api import Workbench


class ErrorHandler(Declarative):
    """Handler taking care of certain kind of errors."""

    #: Id of the error. When signaling errors it will referred to as the kind.
    id = d_(Str())

    #: Short description of what this handler can do. The keyword for the
    #: handle method should be specified.
    description = d_(Str())

    @d_func
    def handle(
        self, workbench: Workbench, infos: Union[Mapping, List[Mapping]]
    ) -> Widget:
        """Handle the report by taking any appropriate measurement.

        The error should always be logged to be sure that a trace remains.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        infos : dict or list
            Information about the error to handle. Should also accept a list
            of such description. The format of the infos should be described in
            the description member.

        Returns
        -------
        widget : enaml.widgets.api.Widget
            Enaml widget to display as appropriate in a dialog.

        """
        raise NotImplementedError()

    @d_func
    def report(self, workbench: Workbench) -> Widget:
        """Provide a report about all errors that occurred.

        Implementing this method is optional.

        Returns
        -------
        widget : enaml.widgets.api.Widget
            A widget describing the errors that will be included in a dialog
            by the plugin. If None is returned the report is simply ignored.

        """
        pass
