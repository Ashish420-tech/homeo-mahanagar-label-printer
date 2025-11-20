import sys
import pytest
from PyQt5 import QtWidgets, QtTest

@pytest.fixture(scope="session")
def qapp_instance():
    """Ensure a single QApplication for all tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    return app

@pytest.fixture
def qtbot(qapp_instance):
    """Very small qtbot-like shim providing addWidget, wait and waitExposed."""
    class _QtBot:
        def addWidget(self, widget):
            widget.show()
            QtTest.QTest.qWait(20)
            return widget

        def wait(self, ms):
            QtTest.QTest.qWait(ms)

        def waitExposed(self, widget, timeout=1000):
            """Wait until a top-level window is exposed (visible on screen)."""
            return QtTest.QTest.qWaitForWindowExposed(widget, timeout)

    return _QtBot()