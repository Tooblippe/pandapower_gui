import sys

import os
os.environ['QT_API'] = 'pyqt'
import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

from PyQt4 import QtGui, uic
import pandapower as pp
import pandapower.networks



from PyQt4.QtGui  import *
# Import the console machinery from ipython
from qtconsole.rich_ipython_widget import RichJupyterWidget as RichIPythonWidget 
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

import code

net = pp.create_empty_network()
######
class QIPythonWidget(RichIPythonWidget):
    """ Convenience class for a live IPython console widget. We can replace the standard banner using the customBanner argument"""
    def __init__(self,customBanner=None,*args,**kwargs):
        if customBanner!=None: self.banner=customBanner
        super(QIPythonWidget, self).__init__(*args,**kwargs)
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel() 
            guisupport.get_app_qt4().exit()            
        self.exit_requested.connect(stop)

    def pushVariables(self,variableDict):
        """ Given a dictionary containing name / value pairs, push those variables to the IPython console widget """
        self.kernel_manager.kernel.shell.push(variableDict)
    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()    
    def printText(self,text):
        """ Prints some plain text to the console """
        self._append_plain_text(text)        
    def executeCommand(self,command):
        """ Execute a command in the frame of the console widget """
        self._execute(command,False)


class ExampleWidget(QWidget):
    """ Main GUI Widget including a button and IPython Console widget inside vertical layout """
    def __init__(self, parent=None):
        super(ExampleWidget, self).__init__(parent)
        layout = QVBoxLayout(self)
        self.button = QPushButton('Another widget')
        ipyConsole = QIPythonWidget(customBanner="Welcome to the embedded ipython console\n")
        layout.addWidget(self.button)
        layout.addWidget(ipyConsole)       
         
        # This allows the variable foo and method print_process_id to be accessed from the ipython console
        ipyConsole.pushVariables({"foo":43,"print_process_id":print_process_id})
        ipyConsole.printText("The variable 'foo' and the method 'print_process_id()' are available. Use the 'whos' command for information.")                           




##############33
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017 by University of Kassel and Fraunhofer Institute for Wind Energy and
# Energy System Technology (IWES), Kassel. All rights reserved. Use of this source code is governed
# by a BSD-style license that can be found in the LICENSE file.
# File created my Massimo Di Pierro

from itertools import combinations
from cgi import escape
import json

class Raw(object):
    def __init__(self, html):
        self.html = html

class Tag(object):
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kwargs):
        attr = ' '+' '.join('%s="%s"' % (k,escape(v)) for k,v in kwargs.items())
        contents = ''.join(a.html if isinstance(a, Raw) else escape(str(a)) for a in args)
        return Raw('<%s%s>%s</%s>' % (self.name, attr.rstrip(), contents, self.name))

def to_html(net, respect_switches=True, include_lines=True, include_trafos=True, show_tables=True):

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

    style = 'tr:first {background:#e1e1e1;} th,td {text-align:center; border:1px solid #e1e1e1;}'

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

#############
class MyWindow(QtGui.QTabWidget):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('builder.ui', self)
        self.net = pp.create_empty_network()
        self.main_message.setText("<H1> Hallo, start by clicking Load Network and then Solve.. inspect and check results </H1>")
        #embed interpreter
        self.ipyConsole = QIPythonWidget(customBanner="Welcome to the embedded ipython console\n")
        self.ipyConsole = QIPythonWidget(customBanner="variable net containts network")
        self.interpreter_vbox.addWidget(self.ipyConsole)
        self.ipyConsole.pushVariables({"net":self.net})

        #show
        self.show()

        #signals
        #main
        self.main_empty.clicked.connect(self.main_empty_clicked)
        self.main_load.clicked.connect(self.main_load_clicked)
        self.main_solve.clicked.connect(self.main_solve_clicked)
        self.main_basic.clicked.connect(self.main_basic_clicked)

        #instepct
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
        self.res_switch.clicked.connect(self.res_switch_clicked)
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
        self.res_measurement.clicked.connect(self.res_measurement_clicked)

    #main

    def main_empty_clicked(self):
        self.net = pp.create_empty_network()
        self.ipyConsole.pushVariables({"net":self.net})
        self.main_message.setText(str(self.net))

    def main_load_clicked(self):
        self.net = pandapower.networks.example_simple()
        #self.net = pandapower.networks.create_cigre_network_mv(with_der="pv_wind")
        #self.net = pandapower.networks.case9241pegase()
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



    #inspect
    def inspect_bus_clicked(self):
        self.inspect_message.setText(str(self.net.bus))

    def inspect_lines_clicked(self):
        self.inspect_message.setText(str(self.net.line))

    def inspect_switch_clicked(self):
        self.inspect_message.setText(str(self.net.switch))

    def inspect_load_clicked(self):
        self.inspect_message.setText(str(self.net.load))

    def inspect_sgen_clicked(self):
        self.inspect_message.setText(str(self.net.sgen))

    def inspect_ext_grid_clicked(self):
        self.inspect_message.setText(str(self.net.ext_grid))

    def inspect_trafo_clicked(self):
        self.inspect_message.setText(str(self.net.trafo))

    def inspect_trafo3w_clicked(self):
        self.inspect_message.setText(str(self.net.trafo3w))

    def inspect_gen_clicked(self):
        self.inspect_message.setText(str(self.net.gen))

    def inspect_shunt_clicked(self):
        self.inspect_message.setText(str(self.net.shunt))

    def inspect_ward_clicked(self):
        self.inspect_message.setText(str(self.net.ward))

    def inspect_xward_clicked(self):
        self.inspect_message.setText(str(self.net.xward))

    def inspect_dcline_clicked(self):
        self.inspect_message.setText(str(self.net.dcline))

    def inspect_measurement_clicked(self):
        self.inspect_message.setText(str(self.net.measurement))

    #html
    def show_report(self):
        self.html_webview.setHtml(to_html(self.net))

    #res
    def res_bus_clicked(self):
        self.res_message.setText(str(self.net.res_bus))

    def res_lines_clicked(self):
        self.res_message.setText(str(self.net.res_line))

    def res_switch_clicked(self):
        self.res_message.setText(str(self.net.res_switch))

    def res_load_clicked(self):
        self.res_message.setText(str(self.net.res_load))

    def res_sgen_clicked(self):
        self.res_message.setText(str(self.net.res_sgen))

    def res_ext_grid_clicked(self):
        self.res_message.setText(str(self.net.res_ext_grid))

    def res_trafo_clicked(self):
        self.res_message.setText(str(self.net.res_trafo))

    def res_trafo3w_clicked(self):
        self.res_message.setText(str(self.net.res_trafo3w))

    def res_gen_clicked(self):
        self.res_message.setText(str(self.net.res_gen))

    def res_shunt_clicked(self):
        self.res_message.setText(str(self.net.res_shunt))

    def res_ward_clicked(self):
        self.res_message.setText(str(self.net.res_ward))

    def res_xward_clicked(self):
        self.res_message.setText(str(self.net.res_xward))

    def res_dcline_clicked(self):
        self.res_message.setText(str(self.net.res_dcline))

    def res_measurement_clicked(self):
        self.res_message.setText(str(self.net.res_measurement))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())
