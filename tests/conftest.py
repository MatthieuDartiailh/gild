# -----------------------------------------------------------------------------
# Copyright 2022 by Glaze Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Pytest fixtures.

"""
import os

from enaml.qt import QT_API

os.environ.setdefault("PYTEST_QT_API", QT_API)

pytest_plugins = ("glaze.testing.fixtures",)


def pytest_configure(config):
    config.addinivalue_line("markers", "ui: mark test involving ui display")
