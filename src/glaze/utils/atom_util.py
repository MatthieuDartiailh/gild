# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------------
# Copyright 2020 by Glaze Authors, see git history for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# --------------------------------------------------------------------------------------
"""Tools to work with Atom tagged members and to automatize preferences handling.

"""
from collections import OrderedDict
from inspect import cleandoc, getfullargspec
from textwrap import fill
from typing import Any, Dict, Optional

from atom.api import Atom, Constant, Member

# String identifying the preference tag
PREF_KEY = "pref"

# Position in the list for the to pref and from pref methods
TO_PREF_ID = 0
FROM_PREF_ID = 1


def tagged_members(
    obj: Atom, meta: Optional[str] = None, meta_value: Any = None
) -> Dict[str, Member]:
    """Utility function to retrieve tagged members from an object

    Parameters
    ----------
    obj : Atom
        Object from which the tagged members should be retrieved.

    meta : str, optional
        The tag to look for, only member which has this tag will be returned

    meta_value : optional
        The value of the metadata used for filtering the members returned

    Returns
    -------
    tagged_members : dict(str, Member)
        Dictionary of the members whose metadatas corresponds to the predicate

    """
    members = obj.members()
    if meta is None and meta_value is None:
        return members
    elif meta_value is None:
        return {
            key: member
            for key, member in members.items()
            if member.metadata is not None and meta in member.metadata
        }
    else:
        return {
            key: member
            for key, member in members.items()
            if member.metadata is not None
            and meta in member.metadata
            and member.metadata[meta] == meta_value
        }


def member_from_pref(obj: Atom, member: Member, val: Any) -> Any:
    """Retrieve the value stored in the preferences for a member.

    Parameters
    ----------
    obj : Atom
        Object who owns the member.

    member : Member
        Member for which the preferences should be retrieved.

    val : Any
        Value that is stored in the preferences, depending on the case this
        might be a serialized value or simply a string.

    Returns
    -------
    value : Any
        The deserialized value that can be assigned to the member.

    """
    meta_value = member.metadata[PREF_KEY]

    # If "pref=True" then we rely on the standard save mechanism
    if meta_value is True:
        # We assume the parser takes care of simple coversion for us.
        value = val

    # If the user provided a custom "from_pref" function, then we check
    # that it has the correct signature and use it to obtain the value
    elif isinstance(meta_value, (tuple, list)) and len(meta_value) == 2:
        converter = meta_value[FROM_PREF_ID]
        if converter is None:
            # Serialization required care, deserialization does not.
            value = val
        elif len(getfullargspec(converter)[0]) == 3:
            value = meta_value[FROM_PREF_ID](obj, member, val)
        else:
            raise ValueError(
                "The converter from preference value to member "
                "value is expected to take 3 parameters, the provided function "
                f"takes {len(getfullargspec(converter)[0])}."
            )

    elif meta_value is False:
        raise NotImplementedError(
            fill(
                cleandoc(
                    """you set "pref=False" for this member. If you did
            not want to save it you should simply not declare this tag."""
                )
            )
        )
    else:
        raise NotImplementedError(
            fill(
                cleandoc(
                    """the "pref" tag of this member was not set to true,
            therefore the program expects you to declare two functions,
             "member_to_pref(obj,member,val)" and "member_from_pref(obj,member,
             val)" that will handle the serialization and deserialization of
             the value. Those should be passed as a list or a tuple, where
             the first element is member_to and the second is member_from.
             It is possible that you failed to properly declare the signature
             of those two functions."""
                )
            )
        )

    return value


def member_to_pref(obj: Atom, member: Member, val: Any) -> Any:
    """Provide the value that will be stored in the preferences for a member.

    Parameters
    ----------
    obj : Atom
        Object who owns the member.

    member : Member
        Member for which the preferences should be retrieved

    val : Value
        Value of the member to be stored in the preferences

    Returns
    -------
    pref_value : str
        The serialized value/string that will be stored in the pref.

    """
    meta_value = member.metadata[PREF_KEY]

    # If "pref=True" then we rely on the standard save mechanism
    if meta_value is True:
        pref_value = val

    # If the user provided a custom "to_pref" function, then we check
    # that it has the correct signature and use it to obtain the value
    elif (
        isinstance(meta_value, (tuple, list))
        and len(meta_value) == 2
        and len(getfullargspec(meta_value[TO_PREF_ID])[0]) == 3
    ):
        pref_value = meta_value[TO_PREF_ID](obj, member, val)

    elif meta_value is False:
        raise NotImplementedError(
            fill(
                cleandoc(
                    """you set "pref=False" for this member. If you did
            not want to save it you should simply not declare this tag."""
                )
            )
        )
    else:
        raise NotImplementedError(
            fill(
                cleandoc(
                    """the "pref" tag of this member was not set to true,
            therefore the program expects you to declare two functions,
             "member_to_pref(obj,member,val)" and "member_from_pref(obj,member,
             val)" that will handle the serialization and deserialization of
             the value. Those should be passed as a list or a tuple, where
             the first element is member_to and the second is member_from.
             It is possible that you failed to properly declare the signature
             of those two functions."""
                )
            )
        )

    return pref_value


class HasPrefAtom(Atom):
    """Base class for Atom object using preferences.

    This class defines the basic functions used to build a string dict from
    the member value and to update the members from such a dict.

    """

    pass


def preferences_from_members(self: Atom) -> OrderedDict:
    """Get the members values as string to store them in .ini files."""
    pref = OrderedDict()
    for name, member in tagged_members(self, "pref").items():
        old_val = getattr(self, name)
        if issubclass(type(old_val), HasPrefAtom):
            pref[name] = old_val.preferences_from_members()
        else:
            pref[name] = member_to_pref(self, member, old_val)
    return pref


def update_members_from_preferences(self: Atom, parameters: dict) -> None:
    """Use the string values given in the parameters to update the members

    This function will call itself on any tagged HasPrefAtom member.

    """
    for name, member in tagged_members(self, "pref").items():

        if name not in parameters or isinstance(member, Constant):
            continue

        old_val = getattr(self, name)
        if issubclass(type(old_val), HasPrefAtom):
            old_val.update_members_from_preferences(parameters[name])
        # This is meant to prevent updating fields which expect a custom
        # instance
        elif old_val is None:
            pass
        else:
            value = parameters[name]
            converted = member_from_pref(self, member, value)
            try:
                setattr(self, name, converted)
            except Exception as e:
                msg = "An exception occured when trying to set {} to {}"
                raise ValueError(msg.format(name, converted)) from e


HasPrefAtom.preferences_from_members = preferences_from_members
HasPrefAtom.update_members_from_preferences = update_members_from_preferences
