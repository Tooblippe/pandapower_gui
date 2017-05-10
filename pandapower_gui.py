import sys
from PyQt4 import QtGui, uic

class MyWindow(QtGui.QDialog):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('resources/ui/pandapower_main.ui', self)
        self.show()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())