# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Tools to build cmdline argument parsers extensible by application plugins.

"""
from argparse import ArgumentParser
from operator import itemgetter
from traceback import format_exc
from typing import Any, Callable, Optional

from atom.api import Atom, Dict, List, Str, Value
from pkg_resources import iter_entry_points


class ArgParser(Atom):
    """Wrapper class around argparse.ArgumentParser.

    This class allow to defer the actual creation of the parser and can hence
    be used to modify some arguments (choices) before creating the real parser.

    """

    #: Name of the application
    app_name = Str()

    #: Mappping between a name passed to the 'choices' arguments of add
    #: add_argument to allow to modify the choices after adding the argument.
    choices = Dict()

    def parse_args(self, args: Optional[list] = None) -> Dict[str, Any]:
        """Parse the arguments.

        By default the arguments passed on the command line are parsed.

        """
        if not self._parser:
            self._init_parser()
        args = self._parser.parse_args(args)

        # Resolve choices.
        mapping = self._arg_to_choices
        for k, v in vars(args).items():
            if k in mapping:
                setattr(args, k, mapping[k][v])

        return args

    def add_argument(self, *args, **kwargs) -> None:
        """Add an argument to the parser.

        See argparse documentation for the accepted arguments and their
        meaning.

        """
        if not args[0].startswith("-"):
            raise ValueError(f"Only optional arguments can be added to {self.app_name}")

        if len(args) == 1:
            arg_name = args[0].strip("--")
        else:
            arg_name = args[1].strip("--")

        if "choices" in kwargs and kwargs["choices"] in self.choices:
            kwargs["choices"] = self.choices[kwargs["choices"]]
            self._arg_to_choices[arg_name] = kwargs["choices"]
            # TODO make help explain to what each value is mapped
        self._arguments.append((args, kwargs))

    def add_choice(self, kind: str, value: str, alias: Optional[str] = None) -> None:
        """Add a possible value for a choice.

        Parameters
        ----------
        kind : str
            Choice id to which to add the proposed value.

        value : str
            New possible value to add to the list of possible value.

        alias : str | None
            Short name to give to the choice. If the chosen one is in conflic
            with an existing name it is ignored.

        """
        if kind not in self.choices:
            self.choices[kind] = {}

        ch = self.choices[kind]
        if not alias or alias in ch:
            ch[value] = value
        else:
            ch[alias] = value

    # --- Private API ---------------------------------------------------------

    # Cached value of the argparser.ArgumentParser instance created by
    # _init_parser, or parser provided by the parent parser.
    _parser = Value()

    # List of tuple to use to create arguments.
    _arguments = List()

    #: Mapping between argument and associated choices.
    #: Used to resolve choices.
    _arg_to_choices = Dict()

    def _init_parser(self) -> None:
        """Initialize the underlying argparse.ArgumentParser."""
        if not self._parser:
            self._parser = ArgumentParser()

        for args, kwargs in self._arguments:
            self._parser.add_argument(*args, **kwargs)


def extend_parser(
    parser: ArgParser,
    entry_point: str,
    handle_error: Callable[[str, str, str, Exception], None],
) -> None:
    """Extend a parser using a specific setuptools extension point.

    Parameters
    ----------
    parser : ArgParsee
        Parser that should be extended.
    entry_point : str
        Setuptools extension point id.
    handle_error : Callable[[str, str, str, Exception]
        Callable used to handle errors. The callable gets an error title, a
        short summary, a detailed report and the exception itself.

    """
    modifiers = []
    for i, ep in enumerate(iter_entry_points(entry_point)):
        try:
            modifier, priority = ep.load(require=False)
            modifiers.append((ep, modifier, priority, i))
        except Exception as e:
            title = "Error loading extension %s" % ep.name
            content = (
                "The following error occurred when trying to load the "
                "entry point {} :\n {}".format(ep.name, e)
            )
            details = format_exc()
            handle_error(title, content, details, e)

    modifiers.sort(key=itemgetter(1, 2))
    try:
        for m in modifiers:
            m[1](parser)
    except Exception as e:
        title = "Error modifying cmd line arguments"
        content = (
            "The following error occurred when the entry point {} "
            "tried to add cmd line options :\n {}".format(ep.name, e)
        )
        details = format_exc()
        handle_error(title, content, details, e)
