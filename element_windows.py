# -*- coding: utf-8 -*-
"""
Created on Sat Jun 03 17:57:27 2017

@author: thurner
"""

try:
    from PyQt5 import uic
    from PyQt5 import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    _QT_VERSION = "5"
except ImportError:
    from PyQt4 import uic
    from PyQt4 import *
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
    _QT_VERSION = "4"

import pandapower as pp

# Base Element Window Class

class ElementWindow(QWidget):
    def __init__(self, net, element, create_function,
                 update_collection_function, **kwargs):
        super(ElementWindow, self).__init__()
        self.update_collection_function = update_collection_function
        self.create_function = create_function
        self.net = net
        self.element = element
        self.initialize_window()
        self.initialize_parameters(**kwargs)
        self.ok.clicked.connect(self.ok_clicked)
        self.cancel.clicked.connect(self.close)
        self.show()

    def initialize_parameters(self, **kwargs):
        print(kwargs)
        self.index = kwargs.get('index', None)
        if self.index is None:
            self.set_parameters(**kwargs)
        else:
            param = dict(self.net[self.element].loc[self.index])
            self.set_parameters(**param)

    def ok_clicked(self):
        if self.index is None:
            self.create_element()
        else:
            self.update_element()
        self.update_collection_function(True)
        self.close()

    def create_element(self):
        param = self.get_parameters()
        self.index = self.create_function(self.net, **param)
        print("created %s"%self.element)

    def update_element(self):
        print("getting")
        param = self.get_parameters()
        print(param)
        self.net[self.element].loc[self.index, param.keys()] = param.values()
        print("updated %s parameters"%self.element)

# Line Window Class
class LineWindow(ElementWindow):
    """ add a standard line """
    def __init__(self, net, update_function, **kwargs):
        super(LineWindow, self).__init__(net, "line"
                                         , update_collection_function=update_function
                                         , create_function=pp.create_line
                                         , **kwargs)

    def initialize_window(self):
        uic.loadUi('resources/ui/add_s_line.ui', self)
        for stdLineType in pp.std_types.available_std_types(self.net).index:
            self.standard_type.addItem(stdLineType)
        for availableBus in self.net.bus.index:
            self.from_bus.addItem(str(availableBus))
            self.to_bus.addItem(str(availableBus))

    def get_parameters(self):
        return {"from_bus": int(self.from_bus.currentText()),
                "to_bus": int(self.to_bus.currentText()),
                "length_km": float(self.length_km.toPlainText()),
                "std_type": self.standard_type.currentText(),
                 "name": self.name.toPlainText()}

    def set_parameters(self, **kwargs):
        self.name.setText(kwargs.get("name", ""))
        self.length_km.setText(str(kwargs.get("length_km", 1)))
        to_bus = self.to_bus.findText(str(kwargs.get("from_bus", "")))
        self.to_bus.setCurrentIndex(to_bus)
        from_bus = self.from_bus.findText(str(kwargs.get("to_bus", "")))
        self.from_bus.setCurrentIndex(from_bus)
        std_type = self.standard_type.findText(kwargs.get("std_type", ""))
        self.standard_type.setCurrentIndex(std_type)

class LoadWindow(ElementWindow):
    """ add a standard line """
    def __init__(self, net, update_function, **kwargs):
        super(LoadWindow, self).__init__(net, "load"
                                         , update_collection_function=update_function
                                         , create_function=pp.create_load
                                         , **kwargs)

    def initialize_window(self):
        uic.loadUi('resources/ui/add_load.ui', self)
        for availableBus in self.net.bus.index:
            self.bus.addItem(str(availableBus))

    def get_parameters(self):
        return {"bus": int(self.bus.currentText()),
                "p_kw": float(self.p_kw.toPlainText()),
                "q_kvar": float(self.q_kvar.toPlainText()),
                 "name": self.name.toPlainText()}

    def set_parameters(self, **kwargs):
        self.name.setText(kwargs.get("name", ""))
        bus = self.bus.findText(str(kwargs.get("bus", "")))
        self.bus.setCurrentIndex(bus)
        self.p_kw.setText(str(kwargs.get("p_kw", 0)))
        self.q_kvar.setText(str(kwargs.get("q_kvar", 0)))

# Bus Window Class

class BusWindow(ElementWindow):
    def __init__(self, net, update_function, **kwargs):
        super(BusWindow, self).__init__(net, "bus"
                                         , update_collection_function = update_function
                                         , create_function= pp.create_bus
                                         , **kwargs)
    def initialize_window(self):
        uic.loadUi('resources/ui/add_bus.ui', self)

    def initialize_parameters(self, **kwargs):
        self.index = kwargs.get('index', None)
        if self.index is None:
            self.set_parameters(**kwargs)
        else:
            params = self.net[self.element].loc[self.index]
            geotab = "%s_geodata"%self.element
            params["geodata"] = self.net[geotab].loc[self.index].values
            self.set_parameters(**params)

    def set_parameters(self, **kwargs):
        print(kwargs)
        self.vn_kv.setText(str(kwargs.get("vn_kv", 0.4)))
        self.name.setText(kwargs.get("name", "Bus"))
        geodata = kwargs.get("geodata", (0, 0))
        print(geodata)
        self.x_coord.setText(str(geodata[0]))
        self.y_coord.setText(str(geodata[1]))

    def get_parameters(self):
        return {"vn_kv": float(self.vn_kv.toPlainText()),
                 "name": self.name.toPlainText(),
                 "geodata": (float(self.x_coord.toPlainText()),
                              float(self.y_coord.toPlainText()))}

    def update_element(self):
        param = self.get_parameters()
        geo_param = {"x": param["geodata"][0], "y": param["geodata"][1]}
        del param["geodata"]
        self.net[self.element].loc[self.index, param.keys()] = param.values()
        self.net["%s_geodata"%self.element].loc[self.index, geo_param.keys()] = geo_param.values()
        print("updated %s parameters"%self.element)



class GenWindow(ElementWindow):
    """ add a standard gen """
    def __init__(self, net, update_function, **kwargs):
        super(GenWindow, self).__init__(net, "gen",
                                        update_collection_function=update_function,
                                        create_function=pp.create_gen,
                                        **kwargs)

    def initialize_window(self):
        uic.loadUi('resources/ui/add_gen.ui', self)
        for availableBus in self.net.bus.index:
            self.bus.addItem(str(availableBus))

    def get_parameters(self):
        return {"bus": int(self.bus.currentText()),
                "p_kw": float(self.p_kw.toPlainText()),
                 "name": self.name.toPlainText()}

    def set_parameters(self, **kwargs):
        self.name.setText(kwargs.get("name", ""))
        bus = self.bus.findText(str(kwargs.get("bus", "")))
        self.bus.setCurrentIndex(bus)
        self.p_kw.setText(str(kwargs.get("p_kw", 0)))


class ExtGridWindow(ElementWindow):
    """ add an external grid """
    def __init__(self, net, update_function, **kwargs):
        super(ExtGridWindow, self).__init__(net, "ext_grid",
                                        update_collection_function=update_function,
                                        create_function=pp.create_gen,
                                        **kwargs)

    def initialize_window(self):
        uic.loadUi('resources/ui/add_ext_grid_s.ui', self)
        for availableBus in self.net.bus.index:
            self.bus.addItem(str(availableBus))

    def get_parameters(self):
        return {"bus": int(self.bus.currentText()),
                "vm_pu": float(self.vm_pu.toPlainText()),
                 "name": self.name.toPlainText()}

    def set_parameters(self, **kwargs):
        self.name.setText(kwargs.get("name", ""))
        bus = self.bus.findText(str(kwargs.get("bus", "")))
        self.bus.setCurrentIndex(bus)
        self.vm_pu.setText(str(kwargs.get("vm_pu", 0)))
