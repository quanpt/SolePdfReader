# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_pdfwindow.ui'
#
# Created: Fri Mar 28 12:12:02 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_PdfWindow(object):
    def setupUi(self, PdfWindow):
        PdfWindow.setObjectName(_fromUtf8("PdfWindow"))
        PdfWindow.resize(496, 306)
        self.centralwidget = QtGui.QWidget(PdfWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        PdfWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(PdfWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 496, 27))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        PdfWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(PdfWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        PdfWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(PdfWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        PdfWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionOpen_PDF = QtGui.QAction(PdfWindow)
        self.actionOpen_PDF.setObjectName(_fromUtf8("actionOpen_PDF"))
        self.actionClose = QtGui.QAction(PdfWindow)
        self.actionClose.setObjectName(_fromUtf8("actionClose"))
        self.actionQuit = QtGui.QAction(PdfWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.menuFile.addAction(self.actionOpen_PDF)
        self.menuFile.addAction(self.actionClose)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())
        self.toolBar.addAction(self.actionOpen_PDF)
        self.toolBar.addAction(self.actionClose)
        self.toolBar.addSeparator()

        self.retranslateUi(PdfWindow)
        QtCore.QMetaObject.connectSlotsByName(PdfWindow)

    def retranslateUi(self, PdfWindow):
        PdfWindow.setWindowTitle(_translate("PdfWindow", "MainWindow", None))
        self.menuFile.setTitle(_translate("PdfWindow", "File", None))
        self.toolBar.setWindowTitle(_translate("PdfWindow", "toolBar", None))
        self.actionOpen_PDF.setText(_translate("PdfWindow", "&Open PDF...", None))
        self.actionOpen_PDF.setShortcut(_translate("PdfWindow", "Ctrl+O", None))
        self.actionClose.setText(_translate("PdfWindow", "Close", None))
        self.actionClose.setShortcut(_translate("PdfWindow", "Ctrl+W", None))
        self.actionQuit.setText(_translate("PdfWindow", "&Quit", None))
        self.actionQuit.setShortcut(_translate("PdfWindow", "Ctrl+Q", None))

