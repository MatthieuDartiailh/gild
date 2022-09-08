# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2022 Gild Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Minimal tests for the custom widgets.

"""
import enaml
import pytest

from gild.testing.util import show_and_close_widget


@pytest.mark.ui
def test_dict_tree_view(gild_qtbot):
    """Test the ConditionalTask view."""
    with enaml.imports():
        from .test_dict_tree_view import Main
    show_and_close_widget(gild_qtbot, Main())


@pytest.mark.ui
def test_list_str_widget(gild_qtbot):
    """Test the ConditionalTask view."""
    with enaml.imports():
        from .test_list_str_widget import Main
    show_and_close_widget(gild_qtbot, Main())


@pytest.mark.ui
def test_tree_widget(gild_qtbot):
    """Test the ConditionalTask view."""
    with enaml.imports():
        from .test_tree_widget import Main
    show_and_close_widget(gild_qtbot, Main())
