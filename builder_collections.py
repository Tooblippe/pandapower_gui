# -*- coding: utf-8 -*-

import sys
from PyQt4.uic import loadUiType
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

Ui_MainWindow, QMainWindow = loadUiType('builder_collections.ui')

import pandapower.plotting as plot
import pandapower as pp
import matplotlib.pyplot as plt

class NetworkBuilder(QMainWindow, Ui_MainWindow):
    def __init__(self, net):
        super(NetworkBuilder, self).__init__()
        self.setupUi(self)
        self.net = net
        self.create_main_frame()
        self.initialize_plot()
        self.last_bus = None


    def initialize_plot(self):
        self.collections = {}
        self.update_bus_collection()
        self.update_line_collection()
        self.update_trafo_collections()
        self.draw_collections()
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.ax.set_aspect('equal', 'datalim')
        self.ax.autoscale_view(True, True, True)

    def draw_collections(self):
        self.ax.clear()
        for name, c in self.collections.items():
            self.ax.add_collection(c)
        self.canvas.draw()

    def update_bus_collection(self):
        self.collections["bus"] = plot.create_bus_collection(net, size=0.2, zorder=2, picker=True,
                                 color="k", infofunc=lambda x: ("bus", x))

    def update_line_collection(self):
        self.collections["line"] = plot.create_line_collection(net, zorder=1, linewidths=2,
                                        picker=False, use_line_geodata=False, color="k")

    def update_trafo_collections(self):
        t1, t2 = plot.create_trafo_symbol_collection(self.net)
        self.collections["trafo1"] = t1
        self.collections["trafo2"] = t2

    def create_main_frame(self):
        self.dpi = 100
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_bgcolor("white")
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('pick_event', self.on_pick)
        mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.gridLayout.addWidget(self.canvas)
        self.gridLayout.addWidget(mpl_toolbar)
        self.fig.subplots_adjust(left=0.0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.04)

    def on_press(self, event):
        if self.Bus.isChecked():
            pp.create_bus(self.net, vn_kv=0.4, geodata=(event.xdata, event.ydata))
            self.update_bus_collection()
            self.draw_collections()


    def on_pick(self, event):
        collection = event.artist
        element, idx = collection.info[event.ind[0]]
        if element != "bus":
            return
        if self.Line.isChecked():
            if self.last_bus is None:
                self.last_bus = idx
            elif self.last_bus != idx:
                pp.create_line(self.net, self.last_bus, idx, length_km=1.0, std_type="NAYY 4x50 SE")
                self.last_bus = None
                self.update_line_collection()
                self.draw_collections()
        if self.Trafo.isChecked():
            if self.last_bus is None:
                self.last_bus = idx
            elif self.last_bus != idx:
                pp.create_transformer(self.net, self.last_bus, idx, std_type="0.25 MVA 10/0.4 kV")
                self.last_bus = None
                self.update_trafo_collections()
                self.draw_collections()

def main(net):
   app = QApplication(sys.argv)
   ex = SliderWidget(net)
   ex.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, 10, geodata=(5,10))
    b2 = pp.create_bus(net, 0.4, geodata=(5,15))
    b3 = pp.create_bus(net, 0.4, geodata=(0,22))
    b4 = pp.create_bus(net, 0.4, geodata=(8, 20))

    pp.create_line(net, b2, b3, 2.0, std_type="NAYY 4x50 SE")
    pp.create_line(net, b2, b4, 2.0, std_type="NAYY 4x50 SE")
    pp.create_transformer(net, b1, b2, std_type="0.63 MVA 10/0.4 kV")

    app = QApplication(sys.argv)
    ex = NetworkBuilder(net)
    self = ex
#    self.redraw_collections()
    ex.show()
    sys.exit(app.exec_())
#    main(net)