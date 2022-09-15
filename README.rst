Gild: tools for developing plugin based application in Enaml
============================================================

Gild is collection of tools and basic plugin to ease the development of plugin
based application within the Enaml framework.

Most of Gild was first developed as part of Exopy and have been extracted when
it appeared clear they could be useful in other applications.

Installation
------------

Gild relies on the Qt backend of Enaml and like Enaml itself it supports both
Qt5 and Qt6 using either PyQt or PySide bindings. Which bindings to use has to be selected at installation time::

    pip install gild[qt5-pyqt]
    pip install gild[qt5-pyside]
    pip install gild[qt6-pyqt]
    pip install gild[qt6-pyside]
