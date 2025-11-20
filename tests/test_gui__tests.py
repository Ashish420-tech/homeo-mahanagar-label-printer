# tests/test_gui.py
# GUI tests for HomeoLabelApp using pytest-qt (qtbot)
# Ensure pytest-qt is installed: pip install pytest-qt

import os
import builtins
import pytest
from PyQt5 import QtWidgets

# Import the app class from your app file name
# Adjust the module name if you renamed the file
import importlib.util
import importlib.machinery

APP_FILENAME = 'homeo_label_printer_font_9_scaled.py'


def load_app_class():
    spec = importlib.util.spec_from_file_location('homeo_app', os.path.join(os.getcwd(), APP_FILENAME))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, 'HomeoLabelApp'):
        return mod.HomeoLabelApp
    raise RuntimeError('HomeoLabelApp not found in module')


@pytest.fixture(scope='session')
def qapp_instance():
    """Provide a QApplication for tests when pytest-qt's builtin isn't used.
    pytest-qt normally provides a qtbot fixture that creates a qapp for tests.
    This fixture can be used if needed, but most tests will use qtbot.
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app
    # Do not call app.quit() here; pytest-qt handles cleanup when using qtbot


def test_preview_updates_and_suggestions(qtbot):
    HomeoLabelApp = load_app_class()
    # Create the widget
    w = HomeoLabelApp(scaling=1.0)
    qtbot.addWidget(w)

    # Ensure widget shows without errors
    w.show()
    qtbot.waitExposed(w)

    # Type a medicine name that's in the default remedies (Arnica should be present)
    w.medicine_search.setText('Arnica')
    qtbot.wait(200)

    # Suggestions table should populate rows
    rows = w.suggestion_table.rowCount()
    assert rows > 0, 'Suggestion table did not populate for "Arnica"'

    # Click the first suggestion programmatically
    item = w.suggestion_table.item(0, 0)
    assert item is not None
    # Simulate click
    w.on_suggestion_clicked(0, 0)
    qtbot.wait(100)

    # After selecting, preview labels should update
    assert any(lbl.text().strip() for lbl in w.preview_labels), 'Preview labels are empty after selection'


def test_auto_print_and_print_invocation(qtbot, monkeypatch, tmp_path):
    HomeoLabelApp = load_app_class()
    w = HomeoLabelApp(scaling=1.0)
    qtbot.addWidget(w)
    w.show()
    qtbot.waitExposed(w)

    # Prevent actual printing: monkeypatch send_pdf_to_printer to just create a marker file
    called = {'ok': False, 'path': None}

    def fake_send(pdf_file, fitlines):
        called['ok'] = True
        called['path'] = pdf_file
        # create the file to simulate PDF output
        open(pdf_file, 'a').close()
        return True

    monkeypatch.setattr(type(w), 'send_pdf_to_printer', lambda self, pdf_file, fitlines: fake_send(pdf_file, fitlines))

    # Monkeypatch QInputDialog for add_new_medicine to avoid modal dialog
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getText', lambda *args, **kwargs: ('MyNewMed', True))

    # Fill all required fields to trigger auto-print
    w.medicine_search.setText('MyNewMed')
    w.potency_input.setCurrentText('30C')
    w.dose_input.setCurrentText('1 tablet')
    w.time_input.setCurrentText('Morning')
    w.shop_input.setCurrentText('TestShop')
    w.branch_phone_input.setCurrentText('012345')

    # Enable auto-print and call check
    w.auto_print_checkbox.setChecked(True)
    # Run the auto-check which schedules a QTimer; trigger directly to avoid timing
    w.check_and_auto_print()

    # Allow event loop to process
    qtbot.wait(500)

    assert called['ok'] is True, 'send_pdf_to_printer was not invoked'
    assert called['path'] is not None
    assert os.path.exists(called['path']), 'PDF file was not created by fake_send'


def test_add_new_medicine_persists(monkeypatch, qtbot, tmp_path):
    HomeoLabelApp = load_app_class()
    # Use a temporary remedies file to avoid touching user's real file
    spec = importlib.util.spec_from_file_location('homeo_app', os.path.join(os.getcwd(), APP_FILENAME))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Create app instance
    w = mod.HomeoLabelApp(scaling=1.0)
    qtbot.addWidget(w)

    # Monkeypatch the remedies file path to a temp file before load
    temp_rem = tmp_path / 'remedies.xlsx'
    # Create an initial minimal remedies.xlsx
    import pandas as pd
    df = pd.DataFrame({'latin_col': ['Testus'], 'common_col': ['Test']})
    df.to_excel(str(temp_rem), index=False, engine='openpyxl')

    w.remedies_file = str(temp_rem)
    # Reload remedies into the instance
    w.load_remedies()

    # Now simulate Add New Medicine with a patched QInputDialog
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getText', lambda *args, **kwargs: ('UniqueMedNameXYZ', True))
    w.add_new_medicine()

    # Reload file to confirm new medicine present
    import pandas as pd
    df2 = pd.read_excel(str(temp_rem), engine='openpyxl')
    assert any('UniqueMedNameXYZ' in str(x) for x in df2['common_col'])
