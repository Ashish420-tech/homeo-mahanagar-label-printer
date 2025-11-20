import os

# --- data directory resolution (project-root/data) ---
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))        # src/homeolabel
ROOT_DIR = os.path.abspath(os.path.join(PACKAGE_DIR, '..', '..'))    # repo root
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RECORDS_DIR = os.path.join(DATA_DIR, 'records')
os.makedirs(RECORDS_DIR, exist_ok=True)
# --- end data dir snippet ---
# homeo_label_printer_font9_responsive.py
"""
Responsive Homeopathy Label Generator
- Handles varying window sizes (including 1280x1024) without overlapping
- Uses layout-based sizing instead of fixed widths/heights where possible
- Dynamically recalculates UI font sizes on window resize (resizeEvent)
- Keeps printing logic and 9pt base print font unchanged

Notes:
- The UI scales based on two factors: the monitor DPI scaling (from Qt) and a window-size ratio.
- Avoids setFixedWidth/Height for critical widgets; uses minimum sizes + expanding policies.
"""
import sys
import os

import json
import logging
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QCompleter, QTableWidgetItem, QMessageBox, QSizePolicy
from pathlib import Path
import platform
import win32print
import win32ui
import win32api
import win32con
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import traceback
import tempfile
import time
import subprocess
import shutil

# Enable Qt high-DPI scaling before creating QApplication
try:
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
except Exception:
    pass

# DPI awareness (Windows) -- keep for GDI/printing correctness
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

# Ensure records dir + logging
os.makedirs("records", exist_ok=True)
logging.basicConfig(filename="records/error_log.txt", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_system_scaling(app=None):
    try:
        if app is None:
            app = QtWidgets.QApplication.instance()
            if app is None:
                return 1.0
        screen = app.primaryScreen()
        if not screen:
            return 1.0
        logical_dpi = screen.logicalDotsPerInch()
        scaling = logical_dpi / 96.0
        return max(0.75, min(scaling, 3.0))
    except Exception:
        return 1.0


def fit_lines_to_box(lines, c, fontname, base_fontsize, max_width_mm, min_fontsize=6):
    out_lines = []
    max_width = max_width_mm * mm
    for text in lines:
        words = str(text).split()
        if not words:
            out_lines.append(("", base_fontsize))
            continue
        running = words[0]
        font_size = base_fontsize
        for word in words[1:]:
            test_str = running + " " + word
            c.setFont(fontname, font_size)
            str_width = c.stringWidth(test_str, fontname, font_size)
            if str_width <= max_width:
                running = test_str
            else:
                actual_size = font_size
                while actual_size > min_fontsize and c.stringWidth(running, fontname, actual_size) > max_width:
                    actual_size -= 1
                out_lines.append((running, actual_size))
                running = word
        actual_size = font_size
        while actual_size > min_fontsize and c.stringWidth(running, fontname, actual_size) > max_width:
            actual_size -= 1
        out_lines.append((running, actual_size))
    return out_lines


def split_medicine_name(name, potency, max_chars=18):
    words = name.strip().split()
    line1 = ""
    line2 = ""
    for word in words:
        if len((line1 + " " + word).strip()) <= max_chars or not line1:
            if line1:
                line1 += " "
            line1 += word
        else:
            if line2:
                line2 += " "
            line2 += word
    if line2:
        line2 = f"{line2} {potency}".strip()
    else:
        line2 = potency
    return line1, line2


# --- Sumatra detection + PDF->printer helper ---
def find_sumatra_exe():
    path_exe = shutil.which("SumatraPDF.exe") or shutil.which("sumatrapdf.exe") or shutil.which("SumatraPDF")
    if path_exe:
        return path_exe
    program_files = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]
    for base in program_files:
        if not base:
            continue
        candidate = os.path.join(base, "SumatraPDF", "SumatraPDF.exe")
        if os.path.exists(candidate):
            return candidate
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    for name in ("SumatraPDF.exe", "sumatrapdf.exe"):
        c = os.path.join(script_dir, name)
        if os.path.exists(c):
            return c
    return None


def print_pdf_to_printer(pdf_path, printer_name, wait_seconds=2, log=logging):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)
    if not printer_name:
        raise ValueError("Printer name required")

    args = f'"{printer_name}"'
    try:
        rc = win32api.ShellExecute(0, "printto", pdf_path, args, ".", 0)
        rc_int = int(rc)
        if rc_int > 32:
            log.info(f"ShellExecute printto succeeded (code {rc_int}) for '{printer_name}'")
            time.sleep(wait_seconds)
            return True
        else:
            log.warning(f"ShellExecute returned code {rc_int}; falling back to Sumatra.")
    except Exception as e:
        log.warning(f"ShellExecute printto failed: {e}. Trying Sumatra fallback.")

    sumatra = find_sumatra_exe()
    if sumatra:
        try:
            cmd = [sumatra, "-print-to", printer_name, pdf_path]
            log.info(f"Running Sumatra: {' '.join(cmd)}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40)
            if proc.returncode == 0:
                log.info("Sumatra printed successfully.")
                time.sleep(wait_seconds)
                return True
            else:
                stdout = proc.stdout.decode(errors="ignore")
                stderr = proc.stderr.decode(errors="ignore")
                log.error(f"Sumatra returned {proc.returncode}. stdout:{stdout} stderr:{stderr}")
        except Exception as e:
            log.error(f"Sumatra printing failed: {e}")

    raise RuntimeError(
        "Printing failed: ShellExecute(printto) failed and SumatraPDF fallback unavailable/failed. "
        "Install SumatraPDF (portable) and place SumatraPDF.exe in Program Files or the application folder, "
        "or configure a PDF viewer that supports the 'printto' verb. Alternatively open the PDF manually and print."
    )


# --- GDI direct printing (safe CreateFont usage) ---
def print_label_direct(printer_name, fit_lines, base_font_size=9, label_w_mm=50, label_h_mm=30):
    if not printer_name:
        raise ValueError("Printer name required")
    hprinter = None
    try:
        hprinter = win32print.OpenPrinter(printer_name)
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Homeopathy Label")
        hDC.StartPage()

        dpi_x = hDC.GetDeviceCaps(win32con.LOGPIXELSX)
        dpi_y = hDC.GetDeviceCaps(win32con.LOGPIXELSY)

        page_width_px = int(label_w_mm / 25.4 * dpi_x)
        page_height_px = int(label_h_mm / 25.4 * dpi_y)

        margin_x = int(2 * dpi_x / 25.4)  # 2mm margin
        margin_y = int(2 * dpi_y / 25.4)

        # Draw rectangle border
        hDC.Rectangle((margin_x, margin_y, page_width_px - margin_x, page_height_px - margin_y))

        x_center = page_width_px // 2
        y = margin_y + int(3 * dpi_y / 25.4)  # start ~3mm from top

        for text, fontsize in fit_lines:
            font_height = -int(fontsize * dpi_y / 72.0)
            font_spec = {"name": "Arial", "height": font_height, "weight": 400}
            try:
                font = win32ui.CreateFont(font_spec)
            except Exception:
                font = win32ui.CreateFont({"name": "Arial", "height": font_height})
            hDC.SelectObject(font)
            text_width = hDC.GetTextExtent(text)[0]
            hDC.TextOut(int(x_center - text_width // 2), int(y), text)
            y += int(fontsize * dpi_y / 72.0 * 1.15)

        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
    finally:
        if hprinter:
            try:
                win32print.ClosePrinter(hprinter)
            except Exception:
                pass


# ---------------- Main app (responsive UI + auto-print) ----------------
class HomeoLabelApp(QtWidgets.QWidget):
    BASE_WINDOW = (1280, 720)  # reference size used to compute window ratio

    def __init__(self, scaling=1.0):
        super().__init__()
        self.setWindowTitle("🏥 Homeopathy Label Generator (Responsive)")
        self.setWindowFlags(QtCore.Qt.Window)

        # start not-maximized so resize events work predictably; user can maximize
        self.resize(*self.BASE_WINDOW)

        self.scaling = scaling if scaling and scaling > 0 else 1.0
        self.base_print_font = 9

        # UI base sizes (pre-scaling)
        self._ui = {
            'search_font_pt': 14,
            'label_font_pt': 20,
            'preview_font_pt': 15,
            'suggestion_font_pt': 13,
            'button_font_pt': 15,
            'control_font_pt': 12,
            'preview_min_width': 260,
            'suggestion_min_width': 480,
            'suggestion_min_height': 180,
            'spacing': 8,
        }

        self.records_folder = "records"
        os.makedirs(self.records_folder, exist_ok=True)
        self.excel_file = os.path.join(self.records_folder, 'records.xlsx')
        self.autocomplete_file = os.path.join(self.records_folder, 'autocomplete.json')
        self.remedies_file = 'remedies.xlsx'
        self.df_remedies = None
        self.load_remedies()
        self.autocomplete_data = self.load_autocomplete()
        self.record_buffer = []
        self.auto_print_enabled = True

        self.init_ui()
        # Apply initial scaled styling
        self.apply_scaled_style()

    def load_remedies(self):
        if not os.path.exists(self.remedies_file):
            df = pd.DataFrame({
                'latin_col': ['Arnica montana', 'Bryonia alba', 'Atropa belladonna'],
                'common_col': ['Arnica', 'Bryonia', 'Belladonna']
            })
            df.to_excel(self.remedies_file, index=False, engine="openpyxl")
        try:
            self.df_remedies = pd.read_excel(self.remedies_file, engine="openpyxl")
            self.df_remedies.fillna('', inplace=True)
            logging.info("Remedies loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load remedies.xlsx: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load remedies.xlsx:{e}")

    def load_autocomplete(self):
        if os.path.exists(self.autocomplete_file):
            try:
                with open(self.autocomplete_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Autocomplete file load failed: {e}")
                return {}
        return {}

    def _window_ratio(self):
        # Ratio relative to BASE_WINDOW; helps adapt font sizes to tall/narrow windows
        w = max(1, self.width())
        h = max(1, self.height())
        rw = w / self.BASE_WINDOW[0]
        rh = h / self.BASE_WINDOW[1]
        # Use geometric mean to avoid extremes
        return (rw * rh) ** 0.5

    def scaled_pt(self, pt):
        # Combines system DPI scaling and window size ratio
        win_ratio = self._window_ratio()
        value = pt * self.scaling * win_ratio
        return max(6, int(round(value)))

    def apply_scaled_style(self):
        # Update fonts and sizes for widgets according to current scale
        try:
            sf = self.scaled_pt
            self.medicine_search.setStyleSheet(f"font-size:{sf(self._ui['search_font_pt'])}pt; padding:6px;")
            self.selected_medicine_label.setStyleSheet(f"font-size:{sf(self._ui['label_font_pt'])}pt;")
            self.suggestion_table.setStyleSheet(f"font-size:{sf(self._ui['suggestion_font_pt'])}pt;")
            self.add_new_btn.setStyleSheet(f"font-size:{sf(self._ui['control_font_pt'])}pt; padding:6px;")
            self.print_btn.setStyleSheet(f"font-size:{sf(self._ui['button_font_pt'])}pt; padding:8px;")
            self.direct_print_btn.setStyleSheet(f"font-size:{sf(self._ui['button_font_pt'])}pt; padding:8px;")
            self.auto_print_checkbox.setStyleSheet(f"font-size:{sf(self._ui['control_font_pt'])}pt;")
            self.status.setStyleSheet(f"font-size:{sf(self._ui['control_font_pt'])}pt; color: darkgreen;")
            # Preview labels font depends on calculated print fitting; set a reasonable default
            for lbl in self.preview_labels:
                lbl.setStyleSheet(f"font-size:{sf(self._ui['control_font_pt'])}pt;")
            # Minimum sizes
            self.preview_frame.setMinimumWidth(self._ui['preview_min_width'] * self.scaling)
            self.suggestion_table.setMinimumWidth(self._ui['suggestion_min_width'] * self.scaling)
            self.suggestion_table.setMinimumHeight(self._ui['suggestion_min_height'] * self.scaling)
            self.suggestion_table.horizontalHeader().setDefaultSectionSize(max(80, int(self.width() * 0.25)))
        except Exception:
            logging.exception("apply_scaled_style failed")

    def init_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setSpacing(self._ui['spacing'])

        left_panel = QtWidgets.QVBoxLayout()
        left_panel.setSpacing(self._ui['spacing'])

        self.medicine_search = QtWidgets.QLineEdit()
        self.medicine_search.setPlaceholderText("Type medicine name (Latin or Common)")
        self.medicine_search.textChanged.connect(self.update_suggestions)

        lbl_find = QtWidgets.QLabel("Find Medicine")
        left_panel.addWidget(lbl_find)
        left_panel.addWidget(self.medicine_search)

        self.suggestion_table = QtWidgets.QTableWidget()
        self.suggestion_table.setColumnCount(2)
        self.suggestion_table.setHorizontalHeaderLabels(["Common Name", "Latin Name"])
        self.suggestion_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.suggestion_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.suggestion_table.setWordWrap(True)
        self.suggestion_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        header = self.suggestion_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.suggestion_table.cellClicked.connect(self.on_suggestion_clicked)

        lbl_suggest = QtWidgets.QLabel("Suggestions")
        left_panel.addWidget(lbl_suggest)
        left_panel.addWidget(self.suggestion_table)

        self.add_new_btn = QtWidgets.QPushButton("Add New Medicine")
        self.add_new_btn.setToolTip("Add a medicine not in the list")
        self.add_new_btn.clicked.connect(self.add_new_medicine)
        left_panel.addWidget(self.add_new_btn)
        left_panel.addStretch()

        right_panel = QtWidgets.QVBoxLayout()
        right_panel.setSpacing(self._ui['spacing'])

        self.selected_medicine_label = QtWidgets.QLabel("MEDICINE: ")
        right_panel.addWidget(self.selected_medicine_label)

        form = QtWidgets.QFormLayout()
        form.setSpacing(self._ui['spacing'])

        self.potency_input = QtWidgets.QComboBox(); self.potency_input.setEditable(True)
        pot_list = self.autocomplete_data.get("potency", [])
        self.potency_input.addItems(pot_list)
        self.potency_input.setCompleter(QCompleter(pot_list))
        self.potency_input.currentTextChanged.connect(self.check_and_auto_print)
        form.addRow("Potency:", self.potency_input)

        self.dose_input = QtWidgets.QComboBox(); self.dose_input.setEditable(True)
        dose_list = self.autocomplete_data.get("dose", [])
        self.dose_input.addItems(dose_list)
        self.dose_input.setCompleter(QCompleter(dose_list))
        self.dose_input.currentTextChanged.connect(self.check_and_auto_print)
        form.addRow("Dose:", self.dose_input)

        self.time_input = QtWidgets.QComboBox(); self.time_input.setEditable(True)
        time_list = self.autocomplete_data.get("time", [])
        self.time_input.addItems(time_list)
        self.time_input.setCompleter(QCompleter(time_list))
        self.time_input.currentTextChanged.connect(self.check_and_auto_print)
        form.addRow("Time:", self.time_input)

        self.shop_input = QtWidgets.QComboBox(); self.shop_input.setEditable(True)
        shop_list = self.autocomplete_data.get("shop", [])
        self.shop_input.addItems(shop_list)
        self.shop_input.setCompleter(QCompleter(shop_list))
        self.shop_input.currentTextChanged.connect(self.check_and_auto_print)
        form.addRow("Shop Name:", self.shop_input)

        self.branch_phone_input = QtWidgets.QComboBox(); self.branch_phone_input.setEditable(True)
        branch_list = self.autocomplete_data.get("branch", [])
        self.branch_phone_input.addItems(branch_list)
        self.branch_phone_input.setCompleter(QCompleter(branch_list))
        self.branch_phone_input.currentTextChanged.connect(self.check_and_auto_print)
        form.addRow("Branch/Phone:", self.branch_phone_input)

        right_panel.addLayout(form)

        # Preview frame - allow it to expand but set a sensible minimum
        self.preview_frame = QtWidgets.QFrame()
        self.preview_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.preview_frame.setStyleSheet("background-color:#f8f8f8; border:2px solid #888;")
        self.preview_frame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        preview_layout = QtWidgets.QVBoxLayout(self.preview_frame)
        self.preview_labels = []
        for i in range(8):
            lbl = QtWidgets.QLabel("")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setWordWrap(True)
            preview_layout.addWidget(lbl)
            self.preview_labels.append(lbl)

        right_panel.addWidget(QtWidgets.QLabel("Label Preview"))
        right_panel.addWidget(self.preview_frame)

        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setSpacing(self._ui['spacing'])
        controls_layout.addWidget(QtWidgets.QLabel(f"Font Size: {self.base_print_font}pt"))
        self.printer_combo = QtWidgets.QComboBox()
        self.refresh_printers()
        controls_layout.addWidget(QtWidgets.QLabel("Printer:"))
        controls_layout.addWidget(self.printer_combo)
        self.printer_refresh_btn = QtWidgets.QPushButton("Refresh")
        self.printer_refresh_btn.clicked.connect(self.refresh_printers)
        controls_layout.addWidget(self.printer_refresh_btn)
        right_panel.addLayout(controls_layout)

        self.auto_print_checkbox = QtWidgets.QCheckBox("Auto Print")
        self.auto_print_checkbox.setChecked(True)
        self.auto_print_checkbox.stateChanged.connect(self.toggle_auto_print)
        right_panel.addWidget(self.auto_print_checkbox)

        btn_layout = QtWidgets.QHBoxLayout()
        self.print_btn = QtWidgets.QPushButton("Manual Preview PDF")
        self.print_btn.clicked.connect(self.print_label)
        btn_layout.addWidget(self.print_btn)
        self.direct_print_btn = QtWidgets.QPushButton("Manual Print")
        self.direct_print_btn.clicked.connect(self.manual_print_label_and_direct)
        btn_layout.addWidget(self.direct_print_btn)
        right_panel.addLayout(btn_layout)

        self.status = QtWidgets.QLabel("Ready - Auto Print Enabled")
        right_panel.addWidget(self.status)
        right_panel.addStretch()

        main_layout.addLayout(left_panel, 3)
        main_layout.addLayout(right_panel, 1)

        # Connect resize handling
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Resize:
            # Re-apply scaling as window size changes
            self.apply_scaled_style()
        return super().eventFilter(obj, event)

    def toggle_auto_print(self, state):
        self.auto_print_enabled = (state == QtCore.Qt.Checked)
        if self.auto_print_enabled:
            self.status.setText("Ready - Auto Print Enabled")
            self.status.setStyleSheet("color: darkgreen;")
        else:
            self.status.setText("Ready - Auto Print Disabled")
            self.status.setStyleSheet("color: orange;")

    def check_and_auto_print(self):
        self.update_preview()
        if not self.auto_print_enabled:
            return
        med_name = self.medicine_search.text().strip()
        potency = self.potency_input.currentText().strip()
        dose = self.dose_input.currentText().strip()
        time_val = self.time_input.currentText().strip()
        shop = self.shop_input.currentText().strip()
        branch = self.branch_phone_input.currentText().strip()
        if med_name and potency and dose and time_val and shop and branch:
            QtCore.QTimer.singleShot(150, self.print_label_and_direct)

    def print_label_and_direct(self):
        med_name = self.medicine_search.text().strip().upper()
        potency = self.potency_input.currentText().upper()
        line1, line2 = split_medicine_name(med_name, potency, max_chars=18)
        line3 = f"{self.dose_input.currentText()}   {self.time_input.currentText()}"
        line4 = f"{self.shop_input.currentText()}"
        line5 = f"{self.branch_phone_input.currentText()}"
        raw_lines = [line1, line2, line3, line4, line5]
        try:
            width_mm, height_mm = 50, 30
            pdf_file = os.path.join(self.records_folder, "label.pdf")
            c = canvas.Canvas(pdf_file, pagesize=(width_mm * mm, height_mm * mm))
            c.setLineWidth(1)
            c.rect(2 * mm, 2 * mm, (width_mm - 4) * mm, (height_mm - 4) * mm)
            y = height_mm * mm - (0.12 * height_mm * mm)
            fitlines = fit_lines_to_box(raw_lines, c, "Helvetica", self.base_print_font, max_width_mm=44)
            for text, fsize in fitlines:
                c.setFont("Helvetica", fsize)
                c.drawCentredString((width_mm / 2) * mm, y, text)
                y -= (fsize * 1.15)
            c.save()
            self.send_pdf_to_printer(pdf_file, fitlines)
            self.status.setText("Label PDF generated and print attempted.")
        except Exception as e:
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Print failed: {e}")
            self.status.setText(f"Error: {e}")

    def manual_print_label_and_direct(self):
        self.print_label_and_direct()

    def send_pdf_to_printer(self, pdf_file, fitlines):
        self.refresh_printers()
        printer_name = self.printer_combo.currentText()
        if not printer_name:
            QMessageBox.warning(self, "Printer Required", "Select a printer first.")
            return
        try:
            print_pdf_to_printer(pdf_file, printer_name, wait_seconds=2)
            self.status.setText(f"Label sent to printer: {printer_name}")
            return
        except Exception as e_pdf:
            logging.warning(f"PDF->printer failed: {e_pdf}")
            try:
                print_label_direct(printer_name, fitlines, base_font_size=self.base_print_font)
                self.status.setText(f"GDI printed to {printer_name} (fallback).")
            except Exception as e_gdi:
                logging.error(traceback.format_exc())
                QMessageBox.critical(self, "Direct Print Failed", f"PDF printing failed and GDI fallback also failed.PDF error: {e_pdf}GDI error: {e_gdi}")
                self.status.setText("Print failed (both PDF and GDI).")

    def update_suggestions(self):
        text = self.medicine_search.text().lower().strip()
        self.suggestion_table.setRowCount(0)
        if not text:
            return
        for _, row in self.df_remedies.iterrows():
            common = str(row['common_col'])
            latin = str(row['latin_col'])
            if text in common.lower() or text in latin.lower():
                row_idx = self.suggestion_table.rowCount()
                self.suggestion_table.insertRow(row_idx)
                item_common = QTableWidgetItem(common)
                item_common.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                item_common.setFlags(item_common.flags() & ~QtCore.Qt.ItemIsEditable)
                item_common.setToolTip(common)
                item_latin = QTableWidgetItem(latin)
                item_latin.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                item_latin.setFlags(item_latin.flags() & ~QtCore.Qt.ItemIsEditable)
                item_latin.setToolTip(latin)
                self.suggestion_table.setItem(row_idx, 0, item_common)
                self.suggestion_table.setItem(row_idx, 1, item_latin)
        # Let the table decide row heights for wrapped text
        self.suggestion_table.resizeRowsToContents()

    def on_suggestion_clicked(self, row, column):
        item = self.suggestion_table.item(row, column)
        if item:
            self.medicine_search.setText(item.text())
            self.update_selected_medicine()

    def add_new_medicine(self):
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Add New Medicine", "Enter medicine name:")
        if ok and new_name.strip():
            self.save_new_medicine(new_name.strip())
            self.medicine_search.setText(new_name.strip())
            self.update_suggestions()

    def update_selected_medicine(self):
        self.update_preview()

    def update_preview(self):
        med_name = self.medicine_search.text().strip().upper()
        potency = self.potency_input.currentText().upper()
        line1, line2 = split_medicine_name(med_name, potency, max_chars=18)
        line3 = f"{self.dose_input.currentText()}   {self.time_input.currentText()}"
        line4 = f"{self.shop_input.currentText()}"
        line5 = f"{self.branch_phone_input.currentText()}"
        raw_lines = [line1, line2, line3, line4, line5]

        temp_c = canvas.Canvas("dummy.pdf")
        preview_lines = fit_lines_to_box(raw_lines, temp_c, "Helvetica", self.base_print_font, max_width_mm=44)

        for lbl in self.preview_labels:
            lbl.setText("")

        for i, (txt, size) in enumerate(preview_lines):
            if i < len(self.preview_labels):
                # clamp preview font size so it doesn't become tiny or huge
                psize = max(6, min(size, 20))
                self.preview_labels[i].setText(txt)
                self.preview_labels[i].setStyleSheet(f"font-size:{self.scaled_pt(psize)}pt;")
        temp_c.save()

    def save_new_medicine(self, med_name):
        exists = ((self.df_remedies['common_col'].str.lower() == med_name.lower()) |
                  (self.df_remedies['latin_col'].str.lower() == med_name.lower())).any()
        if not exists:
            new_row = {'common_col': med_name, 'latin_col': med_name}
            self.df_remedies = pd.concat([self.df_remedies, pd.DataFrame([new_row])], ignore_index=True)
            self.df_remedies.to_excel(self.remedies_file, index=False, engine='openpyxl')
            logging.info(f"New medicine added: {med_name}")

    def print_label(self):
        med_name = self.medicine_search.text().strip().upper()
        potency = self.potency_input.currentText().upper()
        line1, line2 = split_medicine_name(med_name, potency, max_chars=18)
        line3 = f"{self.dose_input.currentText()}   {self.time_input.currentText()}"
        line4 = f"{self.shop_input.currentText()}"
        line5 = f"{self.branch_phone_input.currentText()}"
        raw_lines = [line1, line2, line3, line4, line5]
        try:
            width_mm, height_mm = 50, 30
            pdf_file = os.path.join(self.records_folder, "label.pdf")
            c = canvas.Canvas(pdf_file, pagesize=(width_mm * mm, height_mm * mm))
            c.setLineWidth(1)
            c.rect(2 * mm, 2 * mm, (width_mm - 4) * mm, (height_mm - 4) * mm)
            y = height_mm * mm - (0.12 * height_mm * mm)
            fitlines = fit_lines_to_box(raw_lines, c, "Helvetica", self.base_print_font, max_width_mm=44)
            for text, fsize in fitlines:
                c.setFont("Helvetica", fsize)
                c.drawCentredString((width_mm / 2) * mm, y, text)
                y -= (fsize * 1.15)
            c.save()
            os.startfile(pdf_file)
            self.status.setText("Label preview opened.")
        except Exception as e:
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"PDF Print failed: {e}")
            self.status.setText(f"Error: {e}")

    def refresh_printers(self):
        try:
            if hasattr(self, 'printer_combo'):
                self.printer_combo.clear()
                printers = [printer[2] for printer in win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
                self.printer_combo.addItems(printers)
                logging.info(f"Refreshed printer list: {printers}")
                QtWidgets.QApplication.processEvents()
        except Exception as e:
            logging.error(f"Failed to refresh printers: {e}")

    def check_printer_ready(self, printer_name):
        if not printer_name:
            return False
        try:
            printer_handle = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(printer_handle, 2)
            win32print.ClosePrinter(printer_handle)
            status = printer_info.get('Status', 0)
            if status == 0 and (printer_info.get('Attributes', 0) & win32print.PRINTER_ATTRIBUTE_LOCAL):
                return True
            logging.warning(f"Printer '{printer_name}' status: {status}, attributes: {printer_info.get('Attributes')}")
            return False
        except Exception as e:
            logging.error(f"Printer check failed: {e}")
            return False


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    scaling = get_system_scaling(app)
    w = HomeoLabelApp(scaling)
    w.show()
    sys.exit(app.exec_())

