#!/usr/bin/python

import sys, provwindow, pdfwindow, controller
from PyQt4 import QtGui

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    ctrl = controller.Controller(app)
    
    ctrl.addWindow(provwindow.ProvWindow(ctrl))
    ctrl.addWindow(pdfwindow.PdfWindow(ctrl))
    ctrl.showWindows()
    
    sys.exit(app.exec_())

# check CLIexample.py and Legend.py MultiplePlotAxes.py PlotAutoRange.py ScaleBar.py
# of pyqtgraph
