# -*- coding: utf-8 -*-

# Copyright (c) .....
# All rights reserved. Use of this source code is governed
# by a BSD-style license that can be found in the LICENSE file.
# File created by Tobie Nortje


import sys
import os
import time
import json
import sip

from itertools import combinations
# try:
#     import PyQt4
#     sip.setapi("QString", 2)
#     sip.setapi("QVariant", 2)
#     from PyQt4 import uic
#     from PyQt4.QtGui import *
#     from PyQt4.QtCore import *
#     from PyQt4.uic import loadUiType
#     print("Using PyQt 4")
#     _WHICH_QT = "4"
# except ImportError:
from PyQt5 import uic
from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
print("Using PyQt 5")
_WHICH_QT = "5"


# interpreter
#from qtconsole.rich_ipython_widget import RichJupyterWidget as RichIPythonWidget
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

# collections and plotting from turner
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

#Ui_MainWindow, QMainWindow = loadUiType('_dev_branch/builder_collections.ui')
import pandapower.plotting as plot
import pandapower as pp
import pandapower.networks as pn
from pandapower.html import _net_to_html as to_html

#plotting
import matplotlib.pyplot as plt

from sa_line_types import create_sa_line_types as new_types

class QIPythonWidget(RichJupyterWidget):
    """ Convenience class for a live IPython console widget.
        We can replace the standard banner using the customBanner argument
    """

    def __init__(self, customBanner=None, *args, **kwargs):
        if customBanner != None:
            self.banner = customBanner
        super(QIPythonWidget, self).__init__(*args, **kwargs)
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            "stop"
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()
        self.exit_requested.connect(stop)

    def pushVariables(self, variableDict):
        """ Given a dictionary containing name /
            value pairs, push those variables to the IPython console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()

    def printText(self, text):
        """ Prints some plain text to the console """
        self._append_plain_text(text)

    def executeCommand(self, command):
        """ Execute a command in the frame of the console widget """
        self._execute(command, False)

class add_ext_grid_window(QWidget):
    """ add external grid window """

    def __init__(self, net):
        super(add_ext_grid_window, self).__init__()
        uic.loadUi('resources/ui/add_ext_grid.ui', self)
        self.add_ext_grid.clicked.connect(self.add_ext_grid_clicked)
        self.net = net

    def add_ext_grid_clicked(self):
        """ Add the external grid """
        #(0,0) = (1,1)
        bus = self.parameter_table.item(1, 2)
        vm_pu = self.parameter_table.item(2, 2)
        # print(bus.text())
        # print(vm_pu.text())
        message = pp.create_ext_grid(self.net, bus=int(
            bus.text()), vm_pu=float(vm_pu.text()))
        print(message)


class add_bus_window(QWidget):
    """ add a bus """

    def __init__(self, net, geodata):
        super(add_bus_window, self).__init__()
        uic.loadUi('resources/ui/add_bus.ui', self)
        self.add_bus.clicked.connect(self.add_bus_clicked)
        self.net = net
        self.geodata = geodata

    def add_bus_clicked(self):
        """ Add a bus """
        message = pp.create_bus(self.net, vn_kv=self.vn_kv.toPlainText(),
                                name=self.name.toPlainText(), geodata=self.geodata)
        print(message)


class add_s_line_window(QWidget):
    """ add a standard line """

    def __init__(self, net):
        super(add_s_line_window, self).__init__()
        uic.loadUi('resources/ui/add_s_line.ui', self)
        self.add_s_line.clicked.connect(self.add_s_line_clicked)
        self.net = net

    def add_s_line_clicked(self):
        """ Adds a line """
        from_bus = int(self.from_bus.toPlainText())
        to_bus = int(self.to_bus.toPlainText())
        length_km = float(self.length_km.toPlainText())
        standard_type = self.standard_type.toPlainText()
        name = self.name.toPlainText()
        message = pp.create_line(self.net, from_bus=from_bus, to_bus=to_bus,
                                 length_km=length_km, std_type=standard_type, name=name)
        print(message)


class add_load_window(QWidget):
    """ load window """

    def __init__(self, net):
        super(add_load_window, self).__init__()
        uic.loadUi('resources/ui/add_load.ui', self)
        self.add_load.clicked.connect(self.add_load_clicked)
        self.net = net

    def add_load_clicked(self):
        """ add a load """
        print(self.net.bus)
        message = pp.create_load(net=self.net, bus=int(self.bus_number.toPlainText()),
                                 p_kw=self.p_kw.toPlainText(), q_kvar=self.q_kvar.toPlainText())
        print(message)


class pandapower_main_window(QTabWidget):
    """ Create main window """
    def __init__(self, net):
        super(pandapower_main_window, self).__init__()
        uic.loadUi('resources/ui/builder.ui', self)
        self.net = net
        self.main_message.setText("Welcome to pandapower version: " +
                                  pp.__version__ + "\nQt vesrion: " + _WHICH_QT +
                                  "\nNetwork variable stored in : net")
        self.embed_interpreter()

        # collections builder setup
        self.last_bus = None
        self.create_main_collections_builder_frame()
        self.initialize_collections_plot()

        # show
        self.show()

        # signals
        # main
        self.main_empty.clicked.connect(self.main_empty_clicked)
        self.main_load.clicked.connect(self.main_load_clicked)
        self.main_save.clicked.connect(self.main_save_clicked)
        self.main_solve.clicked.connect(self.main_solve_clicked)
        # temp assign to losses
        # self.main_basic.clicked.connect(self.main_basic_clicked)
        self.main_basic.clicked.connect(self.losses_summary)

        # inspect
        self.inspect_bus.clicked.connect(self.inspect_bus_clicked)
        self.inspect_lines.clicked.connect(self.inspect_lines_clicked)
        self.inspect_switch.clicked.connect(self.inspect_switch_clicked)
        self.inspect_load.clicked.connect(self.inspect_load_clicked)
        self.inspect_sgen.clicked.connect(self.inspect_sgen_clicked)
        self.inspect_ext_grid.clicked.connect(self.inspect_ext_grid_clicked)
        self.inspect_trafo.clicked.connect(self.inspect_trafo_clicked)
        self.inspect_trafo3w.clicked.connect(self.inspect_trafo3w_clicked)
        self.inspect_gen.clicked.connect(self.inspect_gen_clicked)
        self.inspect_shunt.clicked.connect(self.inspect_shunt_clicked)
        self.inspect_impedance.clicked.connect(self.inspect_sgen_clicked)
        self.inspect_ward.clicked.connect(self.inspect_ward_clicked)
        self.inspect_xward.clicked.connect(self.inspect_xward_clicked)
        self.inspect_dcline.clicked.connect(self.inspect_dcline_clicked)
        self.inspect_measurement.clicked.connect(
            self.inspect_measurement_clicked)

        # html
        self.html_show.clicked.connect(self.show_report)

        # results
        self.res_bus.clicked.connect(self.res_bus_clicked)
        self.res_lines.clicked.connect(self.res_lines_clicked)
        # self.res_switch.clicked.connect(self.res_switch_clicked)
        self.res_load.clicked.connect(self.res_load_clicked)
        self.res_sgen.clicked.connect(self.res_sgen_clicked)
        self.res_ext_grid.clicked.connect(self.res_ext_grid_clicked)
        self.res_trafo.clicked.connect(self.res_trafo_clicked)
        self.res_trafo3w.clicked.connect(self.res_trafo3w_clicked)
        self.res_gen.clicked.connect(self.res_gen_clicked)
        self.res_shunt.clicked.connect(self.res_shunt_clicked)
        self.res_impedance.clicked.connect(self.res_sgen_clicked)
        self.res_ward.clicked.connect(self.res_ward_clicked)
        self.res_xward.clicked.connect(self.res_xward_clicked)
        self.res_dcline.clicked.connect(self.res_dcline_clicked)
        # self.res_measurement.clicked.connect(self.res_measurement_clicked)

        # build
        self.build_ext_grid.clicked.connect(self.build_ext_grid_clicked)
        self.build_bus.clicked.connect(self.build_bus_clicked)
        self.build_load.clicked.connect(self.build_load_clicked)
        # need to split lines and parameter lines.. change the form to deal
        # with it
        self.build_lines.clicked.connect(self.build_s_line_clicked)

    def embed_interpreter(self):
        """ embed an Ipyton QT Console Interpreter """
        self.ipyConsole = QIPythonWidget(
            customBanner="Welcome to the pandapower console\nType whos to get lit of variables \n =========== \n")
        self.interpreter_vbox.addWidget(self.ipyConsole)
        self.ipyConsole.pushVariables({"net": self.net, "pp": pp})

    def embed_collections_builder(self):
        self.network_builder = QNetworkBuilderWidget(self.net)
        self.build_vbox.addWidget(self.network_builder)

    def main_empty_clicked(self):
        self.net = pp.create_empty_network()
        new_types(self.net)
        self.ipyConsole.pushVariables({"net": self.net})
        self.main_message.setText(
            "New empty network created and available in variable 'net' ")

    def main_load_clicked(self):
        file_to_open = ""
        file_to_open = QFileDialog.getOpenFileName()
        print(file_to_open)
        if file_to_open[0] != "":
            net = None
            net = pp.from_excel(file_to_open[0], convert=True)
            #self.net = pn.case1888rte()
            self.ipyConsole.pushVariables({"net": self.net})
            self.main_message.setText(str(self.net))

    def main_save_clicked(self):
        #filename = QFileDialog.getOpenFileName()
        filename = QFileDialog.getSaveFileName(self, 'Save net')
        print(filename[0])
        pp.to_excel(self.net, filename[0])
        self.main_message.setText("saved "+ filename[0])

    def main_solve_clicked(self):
        if not pp.runpp(self.net):
            self.main_message.setText(str(self.net))
        else:
            self.main_message.setText("Not Solved")

    def main_basic_clicked(self):
        self.main_message.setText(str(pandapower.lf_info(self.net)))
        pandapower.lf_info(self.net)

    def losses_summary(self):
        """ print the losses in each element that has losses """
        # get total losses
        losses = 0.0
        for i in self.net:
            if 'res' in i:
                if 'pl_kw' in self.net[i]:
                    if not self.net[i]['pl_kw'].empty:
                        print(i)
                        # self.report_message.append(i)
                        self.report_message.append(i)
                        self.report_message.append(
                            self.net[i]['pl_kw'].to_string())
                        print(self.net[i]['pl_kw'])
                        losses += self.net[i]['pl_kw'].sum()
        self.report_message.append("Total Losses (kW)")
        self.report_message.append(str(losses))

        # get total load
        total_load_kw = self.net.res_gen.sum() + self.net.res_sgen.sum() + \
            self.net.res_ext_grid.sum()
        self.report_message.append("Total nett load flowing in network")
        self.report_message.append(str(total_load_kw['p_kw']))

        # losses percentage
        self.report_message.append("% losses")
        loss_pct = losses / total_load_kw['p_kw']
        self.report_message.append(str(abs(loss_pct * 100)))

    # inspect
    def inspect_bus_clicked(self):
        self.inspect_message.setText(str(self.net.bus.to_html()))

    def inspect_lines_clicked(self):
        self.inspect_message.setText(str(self.net.line.to_html()))

    def inspect_switch_clicked(self):
        self.inspect_message.setText(str(self.net.switch.to_html()))

    def inspect_load_clicked(self):
        self.inspect_message.setText(str(self.net.load.to_html()))

    def inspect_sgen_clicked(self):
        self.inspect_message.setText(str(self.net.sgen.to_html()))

    def inspect_ext_grid_clicked(self):
        self.inspect_message.setText(str(self.net.ext_grid.to_html()))

    def inspect_trafo_clicked(self):
        self.inspect_message.setText(str(self.net.trafo.to_html()))

    def inspect_trafo3w_clicked(self):
        self.inspect_message.setText(str(self.net.trafo3w.to_html()))

    def inspect_gen_clicked(self):
        self.inspect_message.setText(str(self.net.gen.to_html()))

    def inspect_shunt_clicked(self):
        self.inspect_message.setText(str(self.net.shunt.to_html()))

    def inspect_ward_clicked(self):
        self.inspect_message.setText(str(self.net.ward.to_html()))

    def inspect_xward_clicked(self):
        self.inspect_message.setText(str(self.net.xward.to_html()))

    def inspect_dcline_clicked(self):
        self.inspect_message.setText(str(self.net.dcline.to_html()))

    def inspect_measurement_clicked(self):
        self.inspect_message.setText(str(self.net.measurement.to_html()))

    # html
    def show_report(self):
        self.html_webview.setHtml(to_html(self.net))

    # res
    def res_bus_clicked(self):
        self.res_message.setHtml(str(self.net.res_bus.to_html()))

    def res_lines_clicked(self):
        self.res_message.setHtml(str(self.net.res_line.to_html()))

    # def res_switch_clicked(self):
    #    self.res_message.setHtml(str(self.net.res_switch.to_html()))

    def res_load_clicked(self):
        self.res_message.setHtml(str(self.net.res_load.to_html()))

    def res_sgen_clicked(self):
        self.res_message.setHtml(str(self.net.res_sgen.to_html()))

    def res_ext_grid_clicked(self):
        self.res_message.setHtml(str(self.net.res_ext_grid.to_html()))

    def res_trafo_clicked(self):
        self.res_message.setHtml(str(self.net.res_trafo.to_html()))

    def res_trafo3w_clicked(self):
        self.res_message.setHtml(str(self.net.res_trafo3w.to_html()))

    def res_gen_clicked(self):
        self.res_message.setHtml(str(self.net.res_gen.to_html()))

    def res_shunt_clicked(self):
        self.res_message.setHtml(str(self.net.res_shunt.to_html()))

    def res_ward_clicked(self):
        self.res_message.setHtml(str(self.net.res_ward.to_html()))

    def res_xward_clicked(self):
        self.res_message.setHtml(str(self.net.res_xward.to_html()))

    def res_dcline_clicked(self):
        self.res_message.setHtml(str(self.net.res_dcline.to_html()))

    # def res_measurement_clicked(self):
    #    self.res_message.setHtml(str(self.net.res_measurement.to_html()))

    # build
    def build_ext_grid_clicked(self):
        self.build_ext_grid_window = add_ext_grid_window(self.net)
        self.build_ext_grid_window.show()

    def build_bus_clicked(self, geodata):
        self.build_bus_window = add_bus_window(self.net, geodata)
        self.build_bus_window.show()

    def build_load_clicked(self):
        self.build_load_window = add_load_window(self.net)
        self.build_load_window.show()

    def build_s_line_clicked(self):
        self.build_s_line_window = add_s_line_window(self.net)
        self.build_s_line_window.show()

    # collections
    def initialize_collections_plot(self):
        self.collections = {}
        # if not self.last_bus is None:
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
        self.collections["bus"] = plot.create_bus_collection(self.net, size=0.2, zorder=2, picker=True,
                                                             color="k", infofunc=lambda x: ("bus", x))

    def update_line_collection(self):
        self.collections["line"] = plot.create_line_collection(self.net, zorder=1, linewidths=2,
                                                               picker=False, use_line_geodata=False, color="k")

    def update_trafo_collections(self):
        t1, t2 = plot.create_trafo_symbol_collection(self.net)
        self.collections["trafo1"] = t1
        self.collections["trafo2"] = t2

    def create_main_collections_builder_frame(self):
        self.dpi = 100
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_bgcolor("white")
        # when a button is pressed on the canvas?
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('pick_event', self.on_pick)
        mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.gridLayout.addWidget(self.canvas)
        self.gridLayout.addWidget(mpl_toolbar)
        self.fig.subplots_adjust(
            left=0.0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.04)

    def on_press(self, event):
        if self.Bus.isChecked():
            self.build_bus_clicked(geodata=(event.xdata, event.ydata))
            # pp.create_bus(self.net, vn_kv=0.4, geodata=(event.xdata,
            # event.ydata)
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
                pp.create_line(self.net, self.last_bus, idx,
                               length_km=1.0, std_type="NAYY 4x50 SE")
                self.last_bus = None
                self.update_line_collection()
                self.draw_collections()
        if self.Trafo.isChecked():
            if self.last_bus is None:
                self.last_bus = idx
            elif self.last_bus != idx:
                pp.create_transformer(
                    self.net, self.last_bus, idx, std_type="0.25 MVA 10/0.4 kV")
                self.last_bus = None
                self.update_trafo_collections()
                self.draw_collections()


def splash(n=2):
     # Create and display the splash screen
    splash_pix = QPixmap('resources/icons_components/splash.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
    time.sleep(n)
    splash.hide()


if __name__ == '__main__':
    # temp collections
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, 10, geodata=(5, 10))
    b2 = pp.create_bus(net, 0.4, geodata=(5, 15))
    b3 = pp.create_bus(net, 0.4, geodata=(0, 22))
    b4 = pp.create_bus(net, 0.4, geodata=(8, 20))

    pp.create_line(net, b2, b3, 2.0, std_type="NAYY 4x50 SE")
    pp.create_line(net, b2, b4, 2.0, std_type="NAYY 4x50 SE")
    pp.create_transformer(net, b1, b2, std_type="0.63 MVA 10/0.4 kV")

    app = QApplication(sys.argv)
    splash()
    window = pandapower_main_window(net)
    sys.exit(app.exec_())
