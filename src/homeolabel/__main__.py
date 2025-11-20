import sys
from PyQt5 import QtWidgets
from .app import HomeoLabelApp

def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = HomeoLabelApp(scaling=1.0)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
