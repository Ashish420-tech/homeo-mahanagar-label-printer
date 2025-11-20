import os
import importlib.util
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Helper: load module from several likely filenames
def load_app_module():
    candidates = [
        'homeo_label_printer_font9_responsive.py',
        'homeo_label_printer_font9_scaled.py',
        'homeo_label_printer_font_9_scaled.py',
        'homeo_label_printer_font9.py',
        'homeo_label.py',
    ]
    base = os.getcwd()
    for name in candidates:
        path = os.path.join(base, name)
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location('homeo_app', path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError('Could not find app module. Place one of the expected filenames in the project root.')


def test_split_medicine_name_simple():
    mod = load_app_module()
    assert hasattr(mod, 'split_medicine_name')
    a, b = mod.split_medicine_name('Arnica', '30C', max_chars=18)
    assert isinstance(a, str)
    assert isinstance(b, str)
    assert '30C' in b


def test_split_medicine_name_long():
    mod = load_app_module()
    longname = 'VeryLongMedicineName ThatKeepsGoing AndGoing'
    a, b = mod.split_medicine_name(longname, '200C', max_chars=10)
    assert a != ''
    assert b != ''
    assert '200C' in b


def test_fit_lines_to_box_basic(tmp_path):
    mod = load_app_module()
    assert hasattr(mod, 'fit_lines_to_box')
    pdf = tmp_path / 'tmp.pdf'
    c = canvas.Canvas(str(pdf), pagesize=(50 * mm, 30 * mm))
    lines = ['HELLO WORLD', '30C', 'One Two Three Four Five']
    out = mod.fit_lines_to_box(lines, c, 'Helvetica', 9, max_width_mm=44)
    assert isinstance(out, list)
    for item in out:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], str)
        assert isinstance(item[1], (int, float))
    c.save()
    assert pdf.exists()
