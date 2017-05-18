# -*- coding: utf-8 -*-

# Copyright (c) .....
# All rights reserved. Use of this source code is governed
# by a BSD-style license that can be found in the LICENSE file.
# File created by Tobie Nortje


import sys
import time
import os
from itertools import combinations
from cgi import escape
import json
import sip
import pandapower as pp
import pandapower.networks
from functools import partial

try:
    from pandapower.html import _net_to_html as to_html
    print("Using net_to_html from version >> 1.3.0")
except ImportError:
    print("Will be using build in to_html function, will be deprecated")

try:
    import PyQt4
    sip.setapi("QString", 2)
    sip.setapi("QVariant", 2)
    from PyQt4 import uic
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
    from PyQt4.uic import loadUiType
    print("Using PyQt 4")
    _WHICH_QT = "4"
except ImportError:
    from PyQt5 import uic
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtWidgets import QApplication, QTabWidget, QSplashScreen, QWidget
    from PyQt5.QtCore import Qt
    print("Using PyQt 5")
    _WHICH_QT = "5"


#interpreter
from qtconsole.rich_ipython_widget import RichJupyterWidget as RichIPythonWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

#collections and plotting from turner
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
Ui_MainWindow, QMainWindow = loadUiType('_dev_branch/builder_collections.ui')
import pandapower.plotting as plot
import pandapower as pp
import matplotlib.pyplot as plt





class QIPythonWidget(RichIPythonWidget):
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


class Raw(object):
    def __init__(self, html):
        self.html = html


class Tag(object):
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kwargs):
        attr = ' '+' '.join('%s="%s"' % (k, escape(v)) for k, v in kwargs.items())
        contents = ''.join(a.html if isinstance(a, Raw) else escape(str(a)) for a in args)
        return Raw('<%s%s>%s</%s>' % (self.name, attr.rstrip(), contents, self.name))


def to_html2(net, respect_switches=True, include_lines=True, include_trafos=True, show_tables=True):
    """
     Converts a pandapower network into an html page which contains a simplified representation
     of a network's topology, reduced to nodes and edges. Busses are being represented by nodes
     (Note: only buses with in_service = 1 appear in the graph), edges represent physical
     connections between buses (typically lines or trafos).

     INPUT:
        **net** (pandapowerNet) - variable that contains a pandapower network


     OPTIONAL:
        **respect_switches** (boolean, True) - True: open line switches are being considered
                                                     (no edge between nodes)
                                               False: open line switches are being ignored

        **include_lines** (boolean, True) - determines, whether lines get converted to edges

        **include_trafos** (boolean, True) - determines, whether trafos get converted to edges

        **show_tables** (boolean, True) - shows pandapower element tables

     EXAMPLE:

         from pandapower.html import to_html
         html = to_html(net, respect_switches = False)
         open('C:\\index.html', "w").write(html)

    """
    nodes = [{'id':int(id), 'label':str(id)} for id in net.bus[net.bus.in_service==1].index]
    edges = []

    if include_lines:
        # lines with open switches can be excluded
        nogolines = set(net.switch.element[(net.switch.et == "l") &  (net.switch.closed == 0)]) \
                    if respect_switches else set()
        edges += [{'from':int(fb),
                       'to':int(tb),
                       'label':'weight %f, key: %i, type %s, capacity: %f, path: %i' %
                       (l, idx, 'l', imax, 1)}
                      for fb, tb, l, idx, inservice, imax in
                      list(zip(net.line.from_bus, net.line.to_bus, net.line.length_km,
                               net.line.index, net.line.in_service, net.line.max_i_ka))
                      if inservice == 1 and not idx in nogolines]
        edges += [{'from':int(fb),
                   'to':int(tb),
                   'label': 'key: %i, type %s, path: %i' %(idx, 'i', 1)}
                  for fb, tb, idx, inservice in
                  list(zip(net.impedance.from_bus, net.impedance.to_bus,
                           net.impedance.index, net.impedance.in_service))
                  if inservice == 1]

    if include_trafos:
        nogotrafos = set(net.switch.element[(net.switch.et == "t") & (net.switch.closed == 0)])
        edges += [{'from':int(hvb),
                   'to':int(lvb),
                   'label':'weight %f, key: %i, type %s' % (0, idx, 't')}
                  for hvb, lvb, idx, inservice in
                  list(zip(net.trafo.hv_bus, net.trafo.lv_bus,
                           net.trafo.index, net.trafo.in_service))
                  if inservice == 1 and not idx in nogotrafos]
        for trafo3, t3tab in net.trafo3w.iterrows():
            edges += [{'from':int(bus1),
                       'to':int(bus2),
                       'label':'weight %f, key: %i, type %s' % (0, trafo3, 't3')}
                      for bus1, bus2 in combinations([t3tab.hv_bus,t3tab.mv_bus, t3tab.lv_bus], 2)
                      if t3tab.in_service]

    # add bus-bus switches
    bs = net.switch[(net.switch.et == "b") &
                    ((net.switch.closed == 1) | (not respect_switches))]
    edges += [{'from':int(b),
               'to':int(e),
               'label':'weight %f, key: %i, type %s' % (0, i, 's')}
              for b, e, i in list(zip(bs.bus, bs.element, bs.index))]

    HTML, HEAD, STYLE, BODY, DIV = Tag('html'), Tag('head'), Tag('style'), Tag('body'), Tag('div')
    TABLE, TR, TH, TD, SCRIPT = Tag('table'), Tag('tr'), Tag('th'), Tag('td'), Tag('script')
    H2 = Tag('h2')

    style = '''
            table {border-collapse: collapse;width: 100%;}
            tr:first {background:#e1e1e1;}
            th,td {text-align:left; border:1px solid #e1e1e1;}
            th {background-color: #4CAF50;color: white;}
            tr:nth-child(even){background-color: #f2f2f2;}
            '''

    script = "var data = {nodes: new vis.DataSet(%s), edges: new vis.DataSet(%s)};" % (
        json.dumps(nodes), json.dumps(edges))
    script += "var container = document.getElementById('net');"
    script += "var network = new vis.Network(container, data, {zoomable: false});"

    tables = []
    if show_tables:
        for name in ['bus', 'trafo', 'line', 'load', 'ext_grid',
                     'res_bus', 'res_trafo', 'res_line', 'res_load', 'res_ext_grid']:
            item = getattr(net, name)
            table = TABLE(TR(*map(TH, item.columns)),
                          *[TR(*map(TD, row)) for row in item.values])
            tables.append(DIV(H2(name), table))

    page = HTML(
        HEAD(STYLE(style)),
        BODY(DIV(*tables),DIV(id='net',style="border:1px solid #f1f1f1;max-width:90%")),
        SCRIPT(src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.18.1/vis.min.js"),
        SCRIPT(Raw(script))
        )
    return page.html

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
        #print(bus.text())
        #print(vm_pu.text())
        message = pp.create_ext_grid(self.net, bus=int(bus.text()), vm_pu=float(vm_pu.text()))
        print(message)

class add_bus_window(QWidget):
    """ add a bus """
    def __init__(self, net, geodata, update, index=None):
        super(add_bus_window, self).__init__()
        uic.loadUi('resources/ui/add_bus.ui', self)
        self.ok.clicked.connect(self.ok_action)
        self.cancel.clicked.connect(self.close)
        self.geodata = geodata
        self.index = index
        self.net = net
        self.update = update
        if self.index is not None:
            self.vn_kv.setText(str(self.net.bus.vn_kv.at[self.index]))
            self.name.setText(str(self.net.bus.name.at[self.index]))

    def ok_action(self):
        """ Add a bus """
        vn_kv = self.vn_kv.toPlainText()
        name = self.name.toPlainText()
        if self.index is None:
            pp.create_bus(self.net, vn_kv=vn_kv, name=name, geodata=self.geodata)
            self.update(True)
        else:
            self.net.bus.loc[self.index, ["vn_kv", "name"]] = [vn_kv, name]
        self.close()



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
                                  pp.__version__ + "\nQt vesrion: "+_WHICH_QT +
                                  "\nNetwork variable stored in : net")
        self.embed_interpreter()

        #collections builder setup
        self.last_bus = None
        self.create_main_frame()
        self.initialize_plot()
        self.doubleclick = False


        #show
        self.show()

        #signals
        #main
        self.main_empty.clicked.connect(self.main_empty_clicked)
        self.main_load.clicked.connect(self.main_load_clicked)
        self.main_solve.clicked.connect(self.main_solve_clicked)
        #temp assign to losses
        #self.main_basic.clicked.connect(self.main_basic_clicked)
        self.main_basic.clicked.connect(self.losses_summary)

        #inspect
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
        self.inspect_measurement.clicked.connect(self.inspect_measurement_clicked)

        #html
        self.html_show.clicked.connect(self.show_report)

        #results
        self.res_bus.clicked.connect(self.res_bus_clicked)
        self.res_lines.clicked.connect(self.res_lines_clicked)
        #self.res_switch.clicked.connect(self.res_switch_clicked)
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
        #self.res_measurement.clicked.connect(self.res_measurement_clicked)

        #build
        self.build_ext_grid.clicked.connect(self.build_ext_grid_clicked)
        self.build_bus.clicked.connect(self.build_bus_clicked)
        self.build_load.clicked.connect(self.build_load_clicked)
        # need to split lines and parameter lines.. change the form to deal with it
        self.build_lines.clicked.connect(self.build_s_line_clicked)

    def embed_interpreter(self):
        """ embed an Ipyton QT Console Interpreter """
        self.ipyConsole = QIPythonWidget(customBanner="Welcome to the pandapower console\nType whos to get lit of variables \n =========== \n")
        self.interpreter_vbox.addWidget(self.ipyConsole)
        self.ipyConsole.pushVariables({"net":self.net, "pp":pandapower})

    def embed_collections_builder(self):
        self.network_builder = QNetworkBuilderWidget(self.net)
        self.build_vbox.addWidget(self.network_builder)

    def main_empty_clicked(self):
        self.net = pp.create_empty_network()
        self.ipyConsole.pushVariables({"net":self.net})
        self.main_message.setText("New empty network created and available in variable 'net' ")

    def main_load_clicked(self):
        #self.net = pandapower.networks.example_simple()
        #self.net = pandapower.networks.create_cigre_network_mv(with_der="pv_wind")
        #self.net = pandapower.networks.case9241pegase()
        import pandapower.networks as pn
        self.net = pn.case1888rte()
        self.ipyConsole.pushVariables({"net":self.net})
        self.main_message.setText(str(self.net))

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
                        #self.report_message.append(i)
                        self.report_message.append(i)
                        self.report_message.append(self.net[i]['pl_kw'].to_string())
                        print(self.net[i]['pl_kw'])
                        losses += self.net[i]['pl_kw'].sum()
        self.report_message.append("Total Losses (kW)")
        self.report_message.append(str(losses))

        # get total load
        total_load_kw = self.net.res_gen.sum() + self.net.res_sgen.sum() + self.net.res_ext_grid.sum()
        self.report_message.append("Total nett load flowing in network")
        self.report_message.append(str(total_load_kw['p_kw']))

        #losses percentage
        self.report_message.append("% losses")
        loss_pct = losses / total_load_kw['p_kw']
        self.report_message.append(str(abs(loss_pct*100)))

    #inspect
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

    #html
    def show_report(self):
        self.html_webview.setHtml(to_html(self.net))

    #res
    def res_bus_clicked(self):
        self.res_message.setHtml(str(self.net.res_bus.to_html()))

    def res_lines_clicked(self):
        self.res_message.setHtml(str(self.net.res_line.to_html()))

    #def res_switch_clicked(self):
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

    #def res_measurement_clicked(self):
    #    self.res_message.setHtml(str(self.net.res_measurement.to_html()))

    #build
    def build_ext_grid_clicked(self):
        self.build_ext_grid_window = add_ext_grid_window(self.net)
        self.build_ext_grid_window.show()

    def build_bus_clicked(self, geodata, index=None):
        self.build_bus_window = add_bus_window(self.net, geodata=geodata, index=index,
                                               update=self.update_bus_collection)
        self.build_bus_window.show()

    def build_load_clicked(self):
        self.build_load_window = add_load_window(self.net)
        self.build_load_window.show()

    def build_s_line_clicked(self):
        self.build_s_line_window = add_s_line_window(self.net)
        self.build_s_line_window.show()

    #collections
    def initialize_plot(self):
        self.collections = {}
        #if not self.last_bus is None:
        self.update_bus_collection()
        self.update_load_collections()
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

    def update_bus_collection(self, redraw=False):
        self.collections["bus"] = plot.create_bus_collection(self.net, size=0.2, zorder=2, picker=True,
                                 color="k", infofunc=lambda x: ("bus", x))
        if redraw:
            self.draw_collections()

    def update_line_collection(self):
        self.collections["line"] = plot.create_line_collection(self.net, zorder=1, linewidths=2,
                                        picker=False, use_line_geodata=False, color="k")

    def update_trafo_collections(self):
        t1, t2 = plot.create_trafo_symbol_collection(self.net)
        self.collections["trafo1"] = t1
        self.collections["trafo2"] = t2

    def update_load_collections(self):
        l1, l2 = plot.create_load_symbol_collection(self.net)
        self.collections["load1"] = l1
        self.collections["load2"] = l2

    def create_main_frame(self):
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
        self.fig.subplots_adjust(left=0.0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.04)

    def on_press(self, event):
        self.doubleclick = event.dblclick
        self.last = "clicked"
        if self.Bus.isChecked():
            self.build_bus_clicked(geodata=(event.xdata, event.ydata))

    def on_pick(self, event):
        if self.doubleclick == False:
            QTimer.singleShot(500,
                               partial(self.performSingleClickAction, event))

    def performSingleClickAction(self, event):
        collection = event.artist
        element, index = collection.info[event.ind[0]]
        if self.doubleclick:
            #ignore second click of doubleclick
            if self.last == "doublecklicked":
                self.last = "clicked"
            else:
                self.DoubleClickAction(event, element, index)
        else:
            self.SingleClickAction(event, element, index)



    def DoubleClickAction(self, event, element, index):
        #what to do when double clicking on an element
        self.last = "doublecklicked"
        if element == "bus":
            self.build_bus_clicked(geodata=None, index=index)

    def SingleClickAction(self, event, element, index):
        #what to do when single clicking on an element
        if element != "bus":
            return
        if self.Line.isChecked():
            if self.last_bus is None:
                self.last_bus = index
            elif self.last_bus != index:
                pp.create_line(self.net, self.last_bus, index, length_km=1.0, std_type="NAYY 4x50 SE")
                self.last_bus = None
                self.update_line_collection()
                self.draw_collections()
        if self.Trafo.isChecked():
            if self.last_bus is None:
                self.last_bus = index
            elif self.last_bus != index:
                pp.create_transformer(self.net, self.last_bus, index, std_type="0.25 MVA 10/0.4 kV")
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
    #temp fix for local to html
    try:
        #use to_html function in versions > 1.3.0
        to_html
    except:
        #use local html function in this file
        to_html = to_html2

    #temp collections
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, 10, geodata=(5,10))
    b2 = pp.create_bus(net, 0.4, geodata=(5,15))
    b3 = pp.create_bus(net, 0.4, geodata=(0,22))
    b4 = pp.create_bus(net, 0.4, geodata=(8, 20))
    pp.create_load(net, b4, p_kw=200)

    pp.create_line(net, b2, b3, 2.0, std_type="NAYY 4x50 SE")
    pp.create_line(net, b2, b4, 2.0, std_type="NAYY 4x50 SE")
    pp.create_transformer(net, b1, b2, std_type="0.63 MVA 10/0.4 kV")

    app = QApplication(sys.argv)
    splash()
    window = pandapower_main_window(net)
    sys.exit(app.exec_())
