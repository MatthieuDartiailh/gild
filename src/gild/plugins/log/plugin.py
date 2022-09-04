# --------------------------------------------------------------------------------------
# Copyright 2020 by Gild Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Log plugin definition.

"""
import logging
import os
from typing import Callable

import enaml
from atom.api import Dict, List, Str, Tuple, Typed
from enaml.workbench.api import Plugin

from .tools import DayRotatingTimeHandler, LogModel

with enaml.imports():
    from .widgets import LogDialog


MODULE_PATH = os.path.dirname(__file__)


class LogPlugin(Plugin):
    """Plugin managing the application logging."""

    #: List of installed handlers.
    handler_ids = List(Str())

    #: List of installed filters.
    filter_ids = List(Str())

    #: Current log
    rotating_log = Typed(DayRotatingTimeHandler)

    #: Possible model for a GUI to display the log.
    gui_model = Typed(LogModel)

    def display_current_log(self) -> None:
        """Display the current instance of the rotating log file."""
        with open(self.rotating_log.path) as f:
            log = f.read()
        LogDialog(log=log).exec_()

    def add_handler(self, id: str, handler: logging.Handler, logger="") -> None:
        """Add a handler to the specified logger.

        Parameters
        ----------
        id : str
            Id of the new handler. This id should be unique.

        handler : logging.Handler, optional
            Handler to add.

        logger : unicode, optional
            Name of the logger to which the handler should be added. By default
            the handler is added to the root logger.

        """
        name = logger
        logger = logging.getLogger(name)

        logger.addHandler(handler)

        self._handlers[id] = (handler, name)
        self.handler_ids = list(self._handlers.keys())

    def remove_handler(self, id: str) -> None:
        """Remove the specified handler.

        Parameters
        ----------
        id : str
            Id of the handler to remove.

        """
        handlers = self._handlers
        if id in handlers:
            handler, logger_name = handlers.pop(id)
            logger = logging.getLogger(logger_name)
            logger.removeHandler(handler)
            for filter_id in self.filter_ids:
                infos = self._filters[filter_id]
                if infos[1] == id:
                    del self._filters[filter_id]

            self.filter_ids = list(self._filters.keys())
            self.handler_ids = list(self._handlers.keys())

    def add_filter(
        self, id: str, filter: Callable[[logging.LogRecord], bool], handler_id: str
    ) -> None:
        """Add a filter to the specified handler.

        Parameters
        ----------
        id : str
            Id of the filter to add.

        filter : Callable[[logging.LogRecord]
            Callable determining if a log record should be processed.

        handler_id : str
            Id of the handler to which this filter should be added

        """
        if not hasattr(filter, "filter"):
            logger = logging.getLogger(__name__)
            logger.warning("Filter does not implemet a filter method")
            return

        handlers = self._handlers
        if handler_id in handlers:
            handler, _ = handlers[handler_id]
            handler.addFilter(filter)
            self._filters[id] = (filter, handler_id)

            self.filter_ids = list(self._filters.keys())

        else:
            logger = logging.getLogger(__name__)
            logger.warning("Handler {} does not exist")

    def remove_filter(self, id: str) -> None:
        """Remove the specified filter.

        Parameters
        ----------
        id : unicode
            Id of the filter to remove.

        """
        filters = self._filters
        if id in filters:
            filter, handler_id = filters.pop(id)
            handler, _ = self._handlers[handler_id]
            handler.removeFilter(filter)
            self.filter_ids = list(self._filters.keys())

    def set_formatter(self, handler_id: str, formatter: logging.Formatter) -> None:
        """Set the formatter of the specified handler.

        Parameters
        ----------
        handler_id : str
            Id of the handler whose formatter shoudl be set.

        formatter : logging.Formatter
            Formatter for the handler.

        """
        handlers = self._handlers
        handler_id = str(handler_id)
        if handler_id in handlers:
            handler, _ = handlers[handler_id]
            handler.setFormatter(formatter)

        else:
            logger = logging.getLogger(__name__)
            logger.warning("Handler {} does not exist")

    # ---- Private API --------------------------------------------------------

    # Mapping between handler ids and handler, logger name pairs.
    _handlers = Dict(Str(), Tuple())

    # Mapping between filter_id and filter, handler_id pairs.
    _filters = Dict(Str(), Tuple())
