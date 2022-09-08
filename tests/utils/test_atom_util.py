# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2022 Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the Atom utility functions and HasPrefAtom object.

"""
from collections import OrderedDict

import pytest
from atom.api import Constant, Enum, Float, Int, List, Str, Typed, Value

from gild.utils.atom_util import (
    HasPrefAtom,
    member_from_pref,
    member_to_pref,
    tagged_members,
)


class _Aaux(HasPrefAtom):

    int_ = Int().tag(pref=True)


class _Faux(HasPrefAtom):

    int_ = Int().tag(pref=False)


class _Aux(HasPrefAtom):

    string = Str().tag(pref=True)
    float_n = Float().tag(pref=True)
    enum = Enum("a", "b").tag(pref=True)
    enum_float = Enum(1.0, 2.0).tag(pref=True)
    list_ = List(Float()).tag(pref=True)
    value = Value().tag(pref=True)
    const = Constant("r").tag(pref=True)

    atom = Typed(_Aaux).tag(pref=True)

    no_tag = Int()

    def _default_atom(self):
        return _Aaux()


def test_false_from_pref_softerror():
    aux = _Faux()
    with pytest.raises(NotImplementedError):
        member_from_pref(aux, aux.get_member(str("int_")), "a")


def test_false_to_pref_softerror():
    aux = _Faux()
    try:
        member_to_pref(aux, aux.get_member(str("int_")), "a")
    except NotImplementedError:
        assert True is True


def test_tagged_members1():
    aux = _Aux()
    members = sorted(tagged_members(aux, "pref").keys())
    test = sorted(
        ["string", "float_n", "enum", "enum_float", "list_", "atom", "value", "const"]
    )
    assert members == test


def test_tagged_members3():
    aux = _Aux()
    members = sorted(tagged_members(aux).keys())
    test = sorted(
        [
            "string",
            "float_n",
            "enum",
            "enum_float",
            "list_",
            "atom",
            "no_tag",
            "value",
            "const",
        ]
    )
    assert members == test


def test_member_from_pref1():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(str("string")), "a") == "a"


def test_member_from_pref2():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(str("float_n")), 1.0) == 1.0


def test_member_from_pref3():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(str("enum")), "a") == "a"


def test_member_from_pref4():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(str("enum_float")), 1.0) == 1.0


def test_member_from_pref5():
    aux = _Aux()
    member = aux.get_member(str("list_"))
    assert member_from_pref(aux, member, [1.0, 2.0]) == [1.0, 2.0]


def test_member_from_pref7():
    aux = _Aux()
    member = aux.get_member(str("value"))
    assert member_from_pref(aux, member, "test.test") == "test.test"


def test_member_to_pref1():
    aux = _Aux()
    assert member_to_pref(aux, aux.get_member(str("string")), "a") == "a"


def test_member_to_pref2():
    aux = _Aux()
    assert member_to_pref(aux, aux.get_member(str("float_n")), 1.0) == 1.0


def test_member_to_pref3():
    aux = _Aux(enum=str("a"))
    assert member_to_pref(aux, aux.get_member(str("enum")), "a") == "a"


def test_member_to_pref4():
    aux = _Aux()
    assert member_to_pref(aux, aux.get_member(str("enum_float")), 1.0) == 1.0


def test_member_to_pref5():
    aux = _Aux()
    member = aux.get_member(str("list_"))
    assert member_to_pref(aux, member, [1.0, 2.0]) == [1.0, 2.0]


def test_member_to_pref7():
    aux = _Aux()
    member = aux.get_member(str("value"))
    assert member_to_pref(aux, member, "test.test") == "test.test"


def test_update_members_from_pref():
    aux = _Aux()
    pref = {
        "float_n": 1.0,
        "enum": "a",
        "enum_float": 1.0,
        "list_": [2.0, 5.0],
        "atom": {"int_": 2},
        "const": "r",
    }
    aux.update_members_from_preferences(pref)
    assert aux.float_n == 1.0
    assert aux.enum == "a"
    assert aux.enum_float == 1.0
    assert aux.list_ == [2.0, 5.0]
    assert aux.atom.int_ == 2

    aux.atom = None
    pref = {"atom": {"int_": 2}}
    aux.update_members_from_preferences(pref)
    assert aux.atom is None

    pref = {"enum": "c"}
    with pytest.raises(ValueError):
        aux.update_members_from_preferences(pref)


def test_pref_from_members():
    aux = _Aux()
    pref = aux.preferences_from_members()
    assert pref["string"] == ""
    assert pref["float_n"] == 0.0
    assert pref["enum"] == "a"
    assert pref["enum_float"] == 1.0
    assert pref["list_"] == []
    assert pref["atom"] == {"int_": 0}
