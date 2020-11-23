# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""This module defines some tools to make easier the use of the logging module.

It provide tools to seamlessly convert stream information into log record so
that any `print` can get recorded, and others to process log emitted in a
subprocess.

:Contains:
    StreamToLogRedirector
        Simple class to redirect a stream to a logger.
    QueueHandler
        Logger handler putting records into a queue.
    GuiConsoleHandler
        Logger handler adding the message of a record to a GUI panel.
    QueueLoggerThread
        Thread getting log record from a queue and asking logging to handle
        them.

"""
import codecs
import datetime
import logging
import os
import queue
import time
from logging.handlers import TimedRotatingFileHandler
from threading import Thread
from typing import IO, Union

from atom.api import Atom, Int, Str
from enaml.application import deferred_call
from typing_extensions import Literal


class StreamToLogRedirector(object):
    """Simple class to redirect a stream to a logger.

    Stream like object which can be used to replace `sys.stdout`, or
    `sys.stderr`.

    Parameters
    ----------
    logger : logging.Logger
        Instance of a loger object returned by a call to logging.getLogger
    stream_type : {'stdout', 'stderr'}, optionnal
        Type of stream being redirected. Stderr stream are logged as CRITICAL

    Attributes
    ----------
    logger : logging.Logger
        Instance of a loger used to log the received message

    """

    def __init__(
        self,
        logger: logging.Logger,
        stream_type: Union[Literal["stdout"], Literal["stderr"]] = "stdout",
    ) -> None:
        self.logger = logger
        if stream_type == "stderr":
            self.write = self.write_error
        else:
            self.write = self.write_info

    def write_info(self, message: str) -> None:
        """Log the received message as info, used for stdout.

        The received message is first strip of starting and trailing
        whitespaces and line return.

        """
        message = message.strip()
        message = str(message)
        if message != "":
            self.logger.info(message)

    def write_error(self, message: str) -> None:
        """Log the received message as critical, used for stderr.

        The received message is first strip of starting and trailing
        whitespaces and line return.

        """
        message = message.strip()
        message = str(message)
        if message != "":
            self.logger.critical(message)

    def flush(self) -> None:
        """Useless function implemented for compatibility."""
        pass


class QueueLoggerThread(Thread):
    """Process a queue of log records, sending them to the appropriate logger.

    Attributes
    ----------
    queue :
        Queue from which to collect log records.

    """

    def __init__(self, queue) -> None:
        Thread.__init__(self)
        self.queue = queue
        # Attribute which can be used to cleanly stop the thread.
        self.flag = True

    def run(self) -> None:
        """Pull record from the queue.

        This runs till the listened process does not put `None` into the queue
        or till the flag attribute is True.

        """
        while self.flag:
            # Collect all display output from process
            try:
                record = self.queue.get(timeout=0.5)
                if record is None:
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except queue.Empty:
                continue


class LogModel(Atom):
    """Simple object which can be used in a GuiHandler."""

    #: Text representing all the messages sent by the handler.
    #: Should not be altered by user code.
    text = Str()

    #: Maximum number of lines.
    buff_size = Int(1000)

    def clean_text(self):
        """Empty the text member."""
        self.text = ""
        self._lines = 0

    def add_message(self, message):
        """Add a message to the text member."""
        if self._lines > self.buff_size:
            self.text = self.text.split("\n", self._lines - self.buff_size)[-1]
        message = message.strip()
        message = str(message)
        message += "\n"

        self._lines += message.count("\n")
        self.text += message

    #: Number of lines.
    _lines = Int()


ERR_MESS = "An error occured please check the log file for more details."


class GuiHandler(logging.Handler):
    """Logger sending the log message to an object which can be linked to a GUI.

    Errors are silently ignored to avoid possible recursions and that's why
    this handler should be coupled to another, safer one.

    Parameters
    ----------
    model : Atom
        Model object with a text member.

    Methods
    -------
    emit(record)
        Handle a log record by appending the log message to the model

    """

    def __init__(self, model: LogModel) -> None:
        logging.Handler.__init__(self)
        self.model = model

    def emit(self, record: logging.LogRecord) -> None:
        """Write the log record message to the model.

        Use Html encoding to add colors, etc.

        """
        # TODO add coloring. Better to create a custom formatter
        try:
            msg = self.format(record)
            if record.levelname == "INFO":
                deferred_call(self.model.add_message, msg + "\n")
            elif record.levelname == "CRITICAL":
                deferred_call(self.model.add_message, ERR_MESS + "\n")
            else:
                deferred_call(
                    self.model.add_message, record.levelname + ": " + msg + "\n"
                )
        except Exception:
            pass


class DayRotatingTimeHandler(TimedRotatingFileHandler):
    """Custom implementation of the TimeRotatingHandler to avoid issues on
    win32.

    Found on StackOverflow ...

    """

    def __init__(self, filename: str, mode: str = "wb", **kwargs) -> None:
        self.mode = mode
        self.path = ""
        super(DayRotatingTimeHandler, self).__init__(
            filename, when="MIDNIGHT", **kwargs
        )

    def _open(self) -> IO[str]:
        """Open a file named accordingly to the base name and the time of
        creation of the file with the (original) mode and encoding.

        """
        today = str(datetime.date.today())

        base_dir, base_filename = os.path.split(self.baseFilename)
        aux = base_filename.split(".")

        # Change filename when the logging system start several time on the
        # same day.
        i = 0
        filename = aux[0] + today + "_%d" + "." + aux[1]
        while os.path.isfile(os.path.join(base_dir, filename % i)):
            i += 1

        path = os.path.join(base_dir, filename % i)
        self.path = path

        if self.encoding is None:
            stream = open(path, self.mode)
        else:
            stream = codecs.open(path, self.mode, self.encoding)
        return stream

    def doRollover(self) -> None:
        """Do a rollover.

        Close old file and open a new one, no renaming is performed to avoid
        issues on window.

        """
        if self.stream:
            self.stream.close()
        # Get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]

        self.stream = self._open()

        # TODO Mypy seems to have some issue with the inherited attributes and methods
        # not sure why
        new_rollover_at = self.computeRollover(current_time)  # type: ignore
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval  # type: ignore
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (
            self.when == "MIDNIGHT" or self.when.startswith("W")  # type: ignore
        ) and not self.utc:  # type: ignore
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                # DST kicks in before next rollover, so we need to deduct an
                # hour
                if not dst_now:
                    addend = -3600
                # DST bows out before next rollover, so we need to add an hour
                else:
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at
