# -*- coding: utf-8 -*-

# Copyright (c) Tobie Nortje, Leon Thurner
# All rights reserved. Use of this source code is governed
# by a BSD-style license that can be found in the LICENSE file.
# File created by Tobie Nortje ---


#general
import sys
import time
import pandas as pd
from functools import partial

#pandapower
import pandapower as pp
import pandapower.networks as pnw

#pandapower gui
from element_windows import *

#qt
try:
    from PyQt5 import uic
    from PyQt5 import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtWebKitWidgets import QWebView
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    QT_VERSION = "5"
except ImportError:
    from PyQt4 import uic
    from PyQt4 import *
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4.QtWebKit import QWebView
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
    QT_VERSION = "4"

import pandapower.plotting as plot
import matplotlib.pyplot as plt

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

_GUI_VERSION = "dev 0"

def clickable(widget):

    class Filter(QObject):

        clicked = pyqtSignal()

        def eventFilter(self, obj, event):

            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True

            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


#         print("tab clicked!")

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
    def __init__(self):
        super(mainWindow, self).__init__()
        uic.loadUi('resources/ui/main.ui', self)

        self.mainPrintMessage("Welcome to pandapower version: " +
                              pp.__version__ +
                              "\nQt vesrion: " +
                              QT_VERSION +
                              "\nGUI version: " +
                              _GUI_VERSION  + "\n" +
                              "\nNetwork variable stored in : net")
        self.embedIpythonInterpreter()

        # collections builder setup
        self.lastBusSelected = None
        self.embedCollectionsBuilder()
        self.load_pandapower_network(createSampleNetwork, "GUI Example Network")
        self.initialiseCollectionsPlot()
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.ax.set_aspect('equal', 'datalim')
        self.ax.autoscale_view(True, True, True)

        self.collectionsDoubleClick = False
        self.tabWidget.setCurrentIndex(0) #set firtst tab

        # toolbar
        self.actionNew_Network.triggered.connect(self.mainEmptyClicked)
        self.actionLoad.triggered.connect(self.mainLoadClicked)
        self.actionSave.triggered.connect(self.mainSaveClicked)

        self.actionMV_oberrhein.triggered.connect(partial(self.load_pandapower_network, pnw.mv_oberrhein, "MV Oberrhein"))
        self.actionCase9.triggered.connect(partial(self.load_pandapower_network, pnw.case9, "IEEE Case 9"))

        self.actionAbout.triggered.connect(self.show_license)
        self.actionDocumentation.triggered.connect(self.show_docs)

        #main
        self.actionrunpp.triggered.connect(self.runpp)
        self.actionrunpp.triggered.connect(self.lossesSummary)
        self.actionrunpp.setIcon(QIcon('resources/icons/runpp.png'))

        self.actionrunppOptions.triggered.connect(self.runpp_options)
        self.actionrunppOptions.setIcon(QIcon('resources/icons/runpp_options.png'))

        # show initialised and updated element tables
        self.tabWidget_inspect.setCurrentIndex(0)
        self.show_element_table()
        self.set_table_tabs_inactive()
        self.tabWidget.currentChanged.connect(self.show_element_table)
        self.tabWidget.currentChanged.connect(self.set_table_tabs_inactive)
        self.tabWidget_inspect.currentChanged.connect(self.show_element_table)
        # self.tabWidget_inspect.currentChanged.connect(self.set_table_tabs_inactive)

        # show initialised and updated results tables
        self.tabWidget_result.setCurrentIndex(0)
        self.show_result_table()
        self.tabWidget_result.currentChanged.connect(self.show_result_table)
        # self.tabWidget_result.currentChanged.connect(self.set_table_tabs_inactive)

        # inspect
        # self.inspect_bus.clicked.connect(partial(self.show_element_table, "bus" ))
        # self.inspect_lines.clicked.connect(partial(self.show_element_table, "line" ))
        # self.inspect_load.clicked.connect(partial(self.show_element_table, "load"))
        # self.inspect_switch.clicked.connect(partial(self.show_element_table, "switch" ))
        # self.inspect_sgen.clicked.connect(partial(self.show_element_table, "sgen" ))
        # self.inspect_ext_grid.clicked.connect(partial(self.show_element_table, "ext_grid" ))
        # self.inspect_trafo.clicked.connect(partial(self.show_element_table, "trafo" ))
        # self.inspect_trafo3w.clicked.connect(partial(self.show_element_table, "trafo3w"))
        # self.inspect_gen.clicked.connect(partial(self.show_element_table, "gen" ))
        # self.inspect_shunt.clicked.connect(partial(self.show_element_table, "shunt"))
        # self.inspect_impedance.clicked.connect(partial(self.show_element_table, "impedance" ))
        # self.inspect_ward.clicked.connect(partial(self.show_element_table, "ward" ))
        # self.inspect_xward.clicked.connect(partial(self.show_element_table, "xward" ))
        # self.inspect_dcline.clicked.connect(partial(self.show_element_table, "dcline"))
        # self.inspect_measurement.clicked.connect(partial(self.show_element_table, "measurement" ))

        # self.inspect_bus.clicked.connect(partial(self.select_tab, "bus" ))
        # self.inspect_lines.clicked.connect(partial(self.select_tab, "line" ))
        # self.inspect_load.clicked.connect(partial(self.select_tab, "load"))
        # self.inspect_switch.clicked.connect(partial(self.select_tab, "switch" ))
        # self.inspect_sgen.clicked.connect(partial(self.select_tab, "sgen" ))
        # self.inspect_ext_grid.clicked.connect(partial(self.select_tab, "ext_grid" ))
        # self.inspect_trafo.clicked.connect(partial(self.select_tab, "trafo" ))
        # self.inspect_trafo3w.clicked.connect(partial(self.select_tab, "trafo3w"))
        # self.inspect_gen.clicked.connect(partial(self.select_tab, "gen" ))
        # self.inspect_shunt.clicked.connect(partial(self.select_tab, "shunt"))
        # self.inspect_impedance.clicked.connect(partial(self.select_tab, "impedance" ))
        # self.inspect_ward.clicked.connect(partial(self.select_tab, "ward" ))
        # self.inspect_xward.clicked.connect(partial(self.select_tab, "xward" ))
        # self.inspect_dcline.clicked.connect(partial(self.select_tab, "dcline"))
        # self.inspect_measurement.clicked.connect(partial(self.select_tab, "measurement" ))

        # # results
        # self.res_bus.clicked.connect(partial(self.show_result_table, "res_bus"))
        # self.res_lines.clicked.connect(partial(self.show_result_table, "res_line"))
        # self.res_load.clicked.connect(partial(self.show_result_table, "res_load"))
        # self.res_sgen.clicked.connect(partial(self.show_result_table, "res_sgen"))
        # self.res_ext_grid.clicked.connect(partial(self.show_result_table, "res_ext_grid"))
        # self.res_trafo.clicked.connect(partial(self.show_result_table, "res_trafo"))
        # self.res_trafo3w.clicked.connect(partial(self.show_result_table, "res_trafo3w"))
        # self.res_gen.clicked.connect(partial(self.show_result_table, "res_gen"))
        # self.res_shunt.clicked.connect(partial(self.show_result_table, "res_shunt"))
        # self.res_impedance.clicked.connect(partial(self.show_result_table, "res_sgen"))
        # self.res_ward.clicked.connect(partial(self.show_result_table, "res_ward"))
        # self.res_xward.clicked.connect(partial(self.show_result_table, "res_xward"))
        # self.res_dcline.clicked.connect(partial(self.show_result_table, "res_dcline"))

        #interpreter
        self.runTests.clicked.connect(self.runPandapowerTests)

        self.show()

    def show_license(self):
        license_text = open("LICENSE", "r")
        self.license = QMessageBox()
        self.license.setIcon(QMessageBox.Information)
        self.license.setWindowTitle("pandapower GUI")
        self.license.setText(license_text.read())
        self.license.show()

    def load_pandapower_network(self, network_function, name):
        net = network_function()
        self.load_network(net, name)

    def show_docs(self):
        self.docs = QWebView()
        self.docs.load(QUrl("https://pandapower.readthedocs.io"))
        self.docs.setWindowTitle("pandapower Documentation")
        self.docs.show()

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
                            whos to get list of variables \
                            \n =========== \n""")

        self.interpreter_vbox.addWidget(self.ipyConsole)
        self.ipyConsole.pushVariables({"pp": pp})

    def mainEmptyClicked(self):
        net = pp.create_empty_network()
        self.load_network(net, "Empty Network")

    def mainLoadClicked(self):
        file_to_open = ""
        file_to_open = QFileDialog.getOpenFileName(filter="*.xlsx, *.p")
        if file_to_open[0] != "":
            fn = file_to_open[0]
            if fn.endswith(".xlsx"):
                try:
                    net = pp.from_excel(file_to_open[0], convert=True)
                except:
                    print("couldn't open %s"%fn)
                    return
            elif file_to_open[0].endswith(".p"):
                try:
                    net = pp.from_pickle(file_to_open[0], convert=True)
                except:
                    print("couldn't open %s"%fn)
                    return
            self.load_network(net)

    def load_network(self, net, name):
        self.net = net
        if not "_runpp_options" in self.net:
            self.net._runpp_options = dict()
#        self.ipyConsole.executeCommand("del(net)")
        #self.ipyConsole.clearTerminal()
        self.ipyConsole.printText("\n\n"+"-"*40)
        self.ipyConsole.printText("\nNew net loaded \n")
        self.ipyConsole.printText("-"*40+"\n\n")
        self.ipyConsole.pushVariables({"net": self.net})
        self.ipyConsole.executeCommand("net")
        self.initialiseCollectionsPlot()
        self.mainPrintMessage(name + " loaded")
        self.mainPrintMessage(str(self.net))
        self.result_table.clear()
        self.element_table.clear()

    def mainSaveClicked(self):
        #filename = QFileDialog.getOpenFileName()
        filename = QFileDialog.getSaveFileName(self, 'Save net')
        print(filename[0])
        try:
            pp.to_excel(self.net, filename[0])
            self.mainPrintMessage("Saved case to: "+ filename[0])
        except:
            self.mainPrintMessage("Case not saved, maybe empty?")

    def runpp(self):
        try:
            pp.runpp(self.net, **self.net._runpp_options)
            self.mainPrintMessage(str(self.net))
        except pp.LoadflowNotConverged:
            self.mainPrintMessage("Power Flow did not Converge!")
        except:
            self.mainPrintMessage("Error occured - empty network?")


    def runpp_options(self):
        try:
            runppOptions(self.net, parent=self)
#            self.options.show()
        except Exception as e:
            print(e)

    def lossesSummary(self):
        """ print the losses in each element that has losses """
        # get total losses
        self.mainPrintMessage("Losses report generated:")
        losses = 0.0
        for i in self.net:
            if 'res' in i:
                if 'pl_kw' in self.net[i]:
                    if not self.net[i]['pl_kw'].empty:
                        print(i)
                        # self.main_message.append(i)
                        self.main_message.append(i)
                        self.main_message.append(
                            self.net[i]['pl_kw'].to_string())
                        print(self.net[i]['pl_kw'])
                        losses += self.net[i]['pl_kw'].sum()
        self.main_message.append("Total Losses (kW)")
        self.main_message.append(str(losses))

        # get total load
        total_load_kw = self.net.res_gen.sum() + self.net.res_sgen.sum() + \
            self.net.res_ext_grid.sum()
        self.main_message.append("Total nett load flowing in network")
        self.main_message.append(str(total_load_kw['p_kw']))

        # losses percentage
        self.main_message.append("% losses")
        loss_pct = losses / total_load_kw['p_kw']
        self.main_message.append(str(abs(loss_pct * 100)))

    def get_element_index(self):
        index = self.tabWidget_inspect.currentIndex()
        tab_list = {0: 'bus', 1: 'line', 2: 'switch', 3: 'load', 4: 'sgen', 5: 'ext_grid',
                    6: 'trafo', 7: 'trafo3w', 8: 'gen', 9: 'shunt', 10: 'impedance', 11: 'ward',
                    12: 'xward', 13: 'dcline', 14: 'measurement'}
        element = tab_list[index]
        return element

    def get_result_index(self):
        index = self.tabWidget_result.currentIndex()
        tab_list = {0: 'res_bus', 1: 'res_line', 2: 'res_load', 3: 'res_sgen', 4: 'res_ext_grid',
                    5: 'res_trafo', 6: 'res_trafo3w', 7: 'res_gen', 8: 'res_shunt', 9: 'res_ward',
                    10: 'res_xward', 11: 'res_dcline'}
        element = tab_list[index]
        return element

    def show_element_table(self):
        element = self.get_element_index()
        self.show_table(element, self.element_table)

    def show_result_table(self):
        element = self.get_result_index()
        self.show_table(element, self.result_table)

    def show_table(self, element, table_widget):
        table = self.net[element]
        table_widget.setColumnCount(len(table.columns) + 1)
        table_widget.setRowCount(len(table))
        header = ["index"] + table.columns.tolist()
        table_widget.setHorizontalHeaderLabels(header)
        for i, (idx, row) in enumerate(table.iterrows()):
            table_widget.setItem(i, 0, QTableWidgetItem(str(idx)))
            for k, value in enumerate(row.values, 1):
                print(i, k, value)
                table_widget.setItem(i, k, QTableWidgetItem(str(value)))
        table_widget.doubleClicked.connect(partial(self.table_doubleclicked, element, table_widget))

    def set_table_tabs_inactive(self):
        """
        Sets the tabs for selecting the tables inactive for all elements that are empty in net
        """
        par = []
        res = []
        for tb in list(self.net.keys()):
            if isinstance(self.net[tb], pd.DataFrame) and len(self.net[tb]) > 0:
                if 'res_' in tb:
                    res.append(tb)
                else:
                    par.append(tb)

        tab_list = {
            'bus': 0, 'dcline': 13, 'ext_grid': 5, 'gen': 8, 'impedance': 10, 'line': 1, 'load': 3,
            'measurement': 14, 'sgen': 4, 'shunt': 9, 'switch': 2, 'trafo': 6, 'trafo3w': 7,
            'ward': 11, 'xward': 12}
        for element in tab_list.keys():
            if element in par:
                self.tabWidget_inspect.setTabEnabled(tab_list[element], True)
            else:
                self.tabWidget_inspect.setTabEnabled(tab_list[element], False)
        res_tab_list = {
            'res_bus': 0, 'res_dcline': 11, 'res_ext_grid': 4, 'res_gen': 7, 'res_line': 1,
            'res_load': 2, 'res_sgen': 3, 'res_shunt': 8, 'res_trafo': 5, 'res_trafo3w': 6,
            'res_ward': 9, 'res_xward': 10}
        for result in res_tab_list.keys():
            if result in res:
                self.tabWidget_result.setTabEnabled(res_tab_list[result], True)
            else:
                self.tabWidget_result.setTabEnabled(res_tab_list[result], False)

    def table_doubleclicked(self, element, table_widget, cell):
        try:
            index = int(table_widget.item(cell.row(), 0).text())
            self.open_element_window(element, index)
        except Exception as e:
            print(e)

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
        self.collections = {}
        self.updateBusCollection()
        self.updateLineCollection()
        self.updateTrafoCollections()
        self.updateLoadCollections()
        self.updateExtGridCollections()
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

    def updateExtGridCollections(self, redraw=False):
        eg1, eg2 = plot.create_ext_grid_symbol_collection(self.net,
                                                    size=self.scale*0.05,
                zorder=2, picker=True,
                infofunc=lambda x: ("ext_grid", x))
        self.collections["ext_grid1"] = eg1
        self.collections["ext_grid2"] = eg2
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
        l1, l2 = plot.create_load_symbol_collection(self.net, size=self.scale*0.02,
                                                    picker=True,
                                                    infofunc=lambda x: ("load", x))
        self.collections["load1"] = l1
        self.collections["load2"] = l2
        if redraw:
            self.drawCollections()

    def updateGenCollections(self, redraw=False):
        l1, l2 = plot.create_gen_symbol_collection(self.net, size=self.scale*0.02,
                                                    picker=True,
                                                    infofunc=lambda x: ("gen", x))
        self.collections["gen1"] = l1
        self.collections["gen2"] = l2
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
                self.last = "doublecklicked"
                print("Double Clicked a ", element)
                self.open_element_window(element, index)
        else:
            self.collectionsSingleClickActions(event, element, index)


    def open_element_window(self, element, index):
        if element == "bus":
            print("will build bus")
            self.element_window = BusWindow(self.net
                                        , self.updateBusCollection
                                        , index=index)
        elif element == "line":
            print("will bild line")
            print(index)
            self.element_window = LineWindow(self.net,
                                              self.updateLineCollection,
                                              index=index)
        elif element == "load":
            self.element_window = LoadWindow(self.net,
                                              self.updateLoadCollections,
                                              index=index)
        elif element == "gen":
            self.element_window = GenWindow(self.net,
                                              self.updateGenCollections,
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
        elif self.create_gen.isChecked():
            try:
                self.gen_window = GenWindow(self.net,
                                              self.updateGenCollections,
                                              bus=index)
            except Exception as e:
                print(e)
            self.lastBusSelected = None


class runppOptions(QDialog):
    def __init__(self, net, parent=None):
        super(runppOptions, self).__init__(parent=parent)
        uic.loadUi('resources/ui/runpp_options.ui', self)
        self.net = net
        self.inits = {"flat": self.InitFlat, "dc": self.InitDC, "results": self.InitResults,
                      "auto":self.InitAuto}
        self.algos = {"nr": self.NewtonRaphson, "bf": self.BackwardForward}
        self.voltage_angles = {True: self.VoltageAnglesTrue, False: self.VoltageAnglesFalse,
                               "auto": self.VoltageAnglesAuto}
        self.set_parameters(**self.net._runpp_options)
        self.ok_button.clicked.connect(partial(self.exit_window, True, False))
        self.cancel_button.clicked.connect(partial(self.exit_window, False, False))
        self.run_button.clicked.connect(partial(self.exit_window, True, True))
        self.show()

    def set_parameters(self, **kwargs):
        init = kwargs.get("init", "auto")
        algorithm = kwargs.get("algorithm", "nr")
        voltage_angles = kwargs.get("calculate_voltage_angles", "auto")
        enforce_q_lims = kwargs.get("enforce_q_lims", False)
        voltage_dependent_loads = kwargs.get("voltage_dependent_loads", True)

        self.inits[init].setChecked(True)
        self.algos[algorithm].setChecked(True)
        self.voltage_angles[voltage_angles].setChecked(True)
        self.EnforceQLims.setChecked(enforce_q_lims)
        self.VoltageDependent.setChecked(voltage_dependent_loads)

    def get_parameters(self):
        for init, widget in self.inits.items():
            if widget.isChecked():
                self.net._runpp_options["init"] = init
        for algorithm, widget in self.algos.items():
            if widget.isChecked():
                self.net._runpp_options["algorithm"] = algorithm
        for voltage_angles, widget in self.voltage_angles.items():
            if widget.isChecked():
                self.net._runpp_options["calculate_voltage_angles"] = voltage_angles
        self.net._runpp_options["enforce_q_lims"] = self.EnforceQLims.isChecked()
        self.net._runpp_options["voltage_dependent_loads"] = self.VoltageDependent.isChecked()

    def exit_window(self, save, run):
        if save:
            self.get_parameters()
        if run:
            self.parent().runpp()
        self.close()

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
    app = 0
    app = QApplication(sys.argv)
    displaySplashScreen()
    window = mainWindow()
    sys.exit(app.exec_())
