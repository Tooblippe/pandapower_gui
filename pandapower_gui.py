# -*- coding: utf-8 -*-

# Copyright (c) Tobie Nortje, Leon Thurner
# All rights reserved. Use of this source code is governed
# by a BSD-style license that can be found in the LICENSE file.
# File created by Tobie Nortje ---


import sys
import time
from functools import partial

from PyQt5 import uic
from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

# interpreter
#from qtconsole.rich_ipython_widget import RichJupyterWidget as RichIPythonWidget
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

# collections and plotting from turner
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from element_windows import *

try:
    import plotting as plot
    print("Using local copy plotting for now")
except ImportError:
    import pandapower.plotting as plot
    print("Using pandapower module plotting")

import pandapower as pp
import pandapower.networks as pn
from pandapower.html import _net_to_html as to_html

#plotting
import matplotlib.pyplot as plt

#from sa_line_types import create_sa_line_types as new_types
print("Using PyQt 5")
_WHICH_QT = "5"
_GUI_VERSION = "dev 0"

class QIPythonWidget(RichJupyterWidget):
    """
        Convenience class for a live IPython console widget.
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

class mainWindow(QMainWindow):
    """ Create main window """
    def __init__(self, net):
        super(mainWindow, self).__init__()
        uic.loadUi('resources/ui/builder.ui', self)

        self.net = net
        self.mainPrintMessage("Welcome to pandapower version: " +
                              pp.__version__ +
                              "\nQt vesrion: " +
                              _WHICH_QT +
                              "\nGUI version: " +
                              _GUI_VERSION  + "\n" +
                              "\nNetwork variable stored in : net")

        self.mainPrintMessage(str(self.net))
        self.embedIpythonInterpreter()

        # collections builder setup
        self.lastBusSelected = None
        self.embedCollectionsBuilder()
        self.initialiseCollectionsPlot()
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.ax.set_aspect('equal', 'datalim')
        self.ax.autoscale_view(True, True, True)
        
        self.collectionsDoubleClick = False
        # set firtst tab
        self.tabWidget.setCurrentIndex(0)
        self.show()

        # signals
        # main
        self.main_empty.clicked.connect(self.mainEmptyClicked)
        self.main_load.clicked.connect(self.mainLoadClicked)
        self.main_save.clicked.connect(self.mainSaveClicked)
        self.main_solve.clicked.connect(self.mainSolveClicked)
        self.main_losses.clicked.connect(self.lossesSummary)

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
        self.html_show.clicked.connect(self.showHtmlReport)

        # results
        self.res_bus.clicked.connect(self.res_bus_clicked)
        self.res_lines.clicked.connect(self.res_lines_clicked)
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

        #interpreter
        self.runTests.clicked.connect(self.runPandapowerTests)

    def printLineSeperator(self, ch="=", n=40):
        """ prints some characters """
        return ch*n+"\n"

    def mainPrintMessage(self, message):
        #self.main_message.append(self.printLineSeperator())
        self.main_message.append(message)
        self.main_message.append(self.printLineSeperator())

    def embedIpythonInterpreter(self):
        """ embed an IPyton QT Console Interpreter """
        self.ipyConsole = QIPythonWidget(
            customBanner="""Welcome to the console\nType \
                            whos to get lit of variables \
                            \n =========== \n""")

        self.interpreter_vbox.addWidget(self.ipyConsole)
        self.ipyConsole.pushVariables({"net": self.net, "pp": pp})

    def embedCollectionsBuilder(self):
        self.network_builder = QNetworkBuilderWidget(self.net)
        self.build_vbox.addWidget(self.network_builder)

    def mainEmptyClicked(self):
        self.net = pp.create_empty_network()
        self.clearMainCollectionBuilder()
        self.ipyConsole.pushVariables({"net": self.net})
        self.mainPrintMessage("New empty network created and available in variable 'net' ")

    def mainLoadClicked(self):
        file_to_open = ""
        file_to_open = QFileDialog.getOpenFileName(filter="*.xlsx, *.p")
        if file_to_open[0] != "":
            fn = file_to_open[0]
            if fn.endswith(".xlsx"):
                try:
                    self.net = pp.from_excel(file_to_open[0], convert=True)
                except:
                    print("couldn't open %s"%fn)
                    return
            elif file_to_open[0].endswith(".p"):
                try:
                    self.net = pp.from_pickle(file_to_open[0], convert=True) 
                except:
                    print("couldn't open %s"%fn)
                    return
            #self.net = pn.case1888rte()
            self.ipyConsole.executeCommand("del(net)")
            #self.ipyConsole.clearTerminal()
            self.ipyConsole.printText("\n\n"+"-"*40)
            self.ipyConsole.printText("\nNew net loaded \n")
            self.ipyConsole.printText("-"*40+"\n\n")
            self.ipyConsole.pushVariables({"net": self.net})
            self.ipyConsole.executeCommand("net")
            self.initialiseCollectionsPlot()
            self.mainPrintMessage(file_to_open[0] + " loaded")
            self.mainPrintMessage(str(self.net))

    def mainSaveClicked(self):
        #filename = QFileDialog.getOpenFileName()
        filename = QFileDialog.getSaveFileName(self, 'Save net')
        print(filename[0])
        try:
            pp.to_excel(self.net, filename[0])
            self.mainPrintMessage("Saved case to: "+ filename[0])
        except:
            self.mainPrintMessage("Case not saved, maybe empty?")

    def mainSolveClicked(self):
        try:
            if not pp.runpp(self.net):
                self.mainPrintMessage(str(self.net))
            else:
                self.mainPrintMessage("Case dit not solve")
        except:
            self.mainPrintMessage("Case not solved, or empty case?")

    def lossesSummary(self):
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
        self.mainPrintMessage("Losses report generated. Check Report tab.")


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
    def showHtmlReport(self):
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

    # interpreter
    def runPandapowerTests(self):
        self.ipyConsole.executeCommand("import pandapower.test as test")
        self.ipyConsole.executeCommand("print('Running tests ...')")
        #self.ipyConsole.executeCommand("test.run_all_tests()")
    
    # collections
    def initialiseCollectionsPlot(self):
        print("Inialise Collections")
        self.xmin = self.net.bus_geodata.x.min()
        self.xmax = self.net.bus_geodata.x.max()
        self.ymin = self.net.bus_geodata.y.min()
        self.ymax = self.net.bus_geodata.y.max()
        self.scale = max((self.xmax - self.xmin), (self.ymax - self.ymin))
        print(self.scale)
        self.collections = {}
        self.updateBusCollection()
        self.updateLineCollection()
        self.updateTrafoCollections()
        self.updateLoadCollections()
        print(self.collections)
        self.drawCollections()


    def drawCollections(self):
        self.ax.clear()
        for name, c in self.collections.items():
            if c is not None:
                self.ax.add_collection(c)
        self.ax.set_xlim((self.xmin*0.98, self.xmax*1.02))
        self.ax.set_ylim((self.ymin*0.98, self.ymax*1.02))
        self.canvas.draw()
        print("Drew Collections")

    def updateBusCollection(self, redraw=False):
        bc = plot.create_bus_collection(self.net, size=self.scale*0.01,
                zorder=2, picker=True, color="black",  patch_type="rect", 
                infofunc=lambda x: ("bus", x))
        self.collections["bus"] = bc

        if redraw:
            self.drawCollections()

    def updateLineCollection(self, redraw=False):
        lc = plot.create_line_collection(self.net, zorder=1, linewidths=1,
                 picker=True, use_line_geodata=False, color="green",
                 infofunc=lambda x: ("line", x))
        self.collections["line"] = lc
        if redraw:
            self.drawCollections()
            
    def updateTrafoCollections(self, redraw=False):
        t1, t2 = plot.create_trafo_symbol_collection(self.net, picker=True,
                         size=self.scale*0.02, infofunc=lambda x: ("trafo", x))
        self.collections["trafo1"] = t1
        self.collections["trafo2"] = t2
        if redraw:
            self.drawCollections()
            
    def updateLoadCollections(self, redraw=False):
        l1, l2 = plot.create_load_symbol_collection(self.net, size= 0.25,
                                                    picker=True,
                                                    infofunc=lambda x: ("load", x))
        self.collections["load1"] = l1
        self.collections["load2"] = l2
        if redraw:
            self.drawCollections()

    def clearMainCollectionBuilder(self):
        self.ax.clear()
        print("figure cleared")
        self.collections = {}
        self.drawCollections()


    def embedCollectionsBuilder(self):
        self.dpi = 100
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
#        self.ax.set_axis_bgcolor("white")
        # when a button is pressed on the canvas?
        self.canvas.mpl_connect('button_press_event', self.onCollectionsClick)
        #self.canvas.mpl_connect('button_release_event', self.onCollectionsClick)
        self.canvas.mpl_connect('pick_event', self.onCollectionsPick)
        mpl_toolbar = NavigationToolbar(self.canvas, self.main_build_frame)
        self.gridLayout.addWidget(self.canvas)
        self.gridLayout.addWidget(mpl_toolbar)
        self.fig.subplots_adjust(
            left=0.0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.04)
        self.dragged = None

    def onCollectionsClick(self, event):
        print("clicked")
        self.collectionsDoubleClick = event.dblclick
        self.last = "clicked"
        if self.create_bus.isChecked():
            geodata = (event.xdata, event.ydata)
            try:
                self.bus_window = BusWindow(self.net
                                            , self.updateBusCollection
                                            , geodata=geodata)
            except Exception as inst:
                print(inst)


    def onCollectionsPick(self, event):
        if self.collectionsDoubleClick == False:
            QTimer.singleShot(200,
                              partial(self.performcollectionsSingleClickActions, event))

    def performcollectionsSingleClickActions(self, event):
        print("picked")
        collection = event.artist
        element, index = collection.info[event.ind[0]]
        print("====", event.ind[0])
        print("====", collection)   
        print("single")
        if self.collectionsDoubleClick:
            #ignore second click of collectionsDoubleClick
            if self.last == "doublecklicked":
                self.last = "clicked"
            else:
                self.collectionsDoubleClickAction(event, element, index)
        else:
            self.collectionsSingleClickActions(event, element, index)


    def collectionsDoubleClickAction(self, event, element, index):
        #what to do when double clicking on an element
        print("Double Clicked a ", element)
        self.last = "doublecklicked"
        if element == "bus":
            print("will build bus")
            self.bus_window = BusWindow(self.net
                                        , self.updateBusCollection
                                        , index=index)
        elif element == "line":
            print("will bild line")
            print(index)
            self.line_window = LineWindow(self.net,
                                              self.updateLineCollection,
                                              index=index)               
        elif element == "load":
            self.load_window = LoadWindow(self.net,
                                              self.updateLoadCollections,
                                              index=index)
        elif element == "trafo":
            print("trafo doubleclicked")
            
    def collectionsSingleClickActions(self, event, element, index):
        #what to do when single clicking on an element
        if element != "bus":
            return
        if self.create_line.isChecked():
            if self.lastBusSelected is None:
                self.lastBusSelected = index
            elif self.lastBusSelected != index:
                #pp.create_line(self.net, self.lastBusSelected, index, length_km=1.0, std_type="NAYY 4x50 SE")
                self.build_message.setText(str(self.lastBusSelected)+"-"+str(index))
                self.line_window = LineWindow(self.net,
                                              self.updateLineCollection,
                                              from_bus=self.lastBusSelected,
                                              to_bus=index)
                self.lastBusSelected = None
        elif self.create_trafo.isChecked():
            if self.lastBusSelected is None:
                self.lastBusSelected = index
            elif self.lastBusSelected != index:
                pp.create_transformer(self.net, self.lastBusSelected, index, std_type="0.25 MVA 10/0.4 kV")
                self.lastBusSelected = None
                self.updateTrafoCollections()
                self.drawCollections()
        elif self.create_load.isChecked():
            try:
                self.load_window = LoadWindow(self.net,
                                              self.updateLoadCollections,
                                              bus=index)
            except Exception as e:
                print(e)
            self.lastBusSelected = None            



def displaySplashScreen(n=2):
    """ Create and display the splash screen """
    splash_pix = QPixmap('resources/icons_components/splash.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
    time.sleep(n)
    splash.hide()


def createSampleNetwork():
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=20., name="HV", geodata=(5, 30))
    b2 = pp.create_bus(net, vn_kv=0.4, name="MV", geodata=(5, 28))
    b3 = pp.create_bus(net, vn_kv=0.4, name="Load Bus", geodata=(5, 22))

    #create bus elements
    pp.create_ext_grid(net, bus=b1, vm_pu=1.02, name="Grid Connection")
    pp.create_load(net, bus=b3, p_kw=100, q_kvar=50, name="Load")

    #create branch elements
    tid = pp.create_transformer(net, hv_bus=b1, lv_bus=b2, std_type="0.4 MVA 20/0.4 kV",
                                name="Trafo")
    pp.create_line(net, from_bus=b2, to_bus=b3, length_km=0.1, name="Line",
                   std_type="NAYY 4x50 SE")

    return net

if __name__ == '__main__':
    app = QApplication(sys.argv)
    displaySplashScreen()
    window = mainWindow(createSampleNetwork())
    sys.exit(app.exec_())
