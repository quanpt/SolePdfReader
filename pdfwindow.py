from PyQt4 import QtGui, QtCore, QtWebKit
from ui_pdfwindow import *
from controller import Controller
import logging as l, sys, os
from PyPDF2 import PdfFileReader

scriptdir = os.path.dirname(os.path.realpath(__file__))
if scriptdir[-3:]=='zip':
    scriptdir = os.path.dirname(scriptdir)
print scriptdir

l.basicConfig(format='[File "%(filename)s" line %(lineno)d - %(funcName)s - %(levelname)s] %(message)s', \
    level=l.INFO)

class PdfWindow(QtGui.QMainWindow, Ui_PdfWindow):
    def __init__(self, controller):
        QtGui.QMainWindow.__init__(self)
        
        self.controller = controller
        self.config = controller.config
        
        self.setupUi(self)
        
        self.actionOpen_PDF.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogOpenButton));
        self.actionClose.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogCloseButton));
        
        # create a webview widget (not available from qtdesigner ???)
        self.html = QtWebKit.QWebView()
        self.horizontalLayout.addWidget(self.html)
        
        # setup the webview, and capture click
        # need to remove right click reload, back, forward
        #~ self.html.page().action(QtWebKit.QWebPage.Reload).setVisible(False) 
        self.html.setContextMenuPolicy( QtCore.Qt.NoContextMenu)
        self.html.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateExternalLinks)
        self.connect(self.html, QtCore.SIGNAL("linkClicked(const QUrl&)"), self.linkClick)
        
        self.html.setHtml("<html><body></body></html>", QtCore.QUrl(''))
        
        self.on_actionOpen_PDF_triggered()
        
    @QtCore.pyqtSlot(QtCore.QUrl)
    def linkClick(self, url):
        try:
            baseurl = self.pdfinfo['/sole.baseurl'] + '/solelink.html?'
        except KeyError:
            l.warn('sole.baseurl info not found.')
            return
            
        url = str(url.toString())
        base = url[:len(baseurl)] #.replace('~',' ') somehow '~' is converted to space in pdfinfo
        if base == baseurl:
            #~ http://people.cs.uchicago.edu/~quanpt/solelink?dbid/mydbid44/type/mytype22/id/myid11/part/mypart33
            params = url[len(baseurl):].split('/')
            entry = {'dbid': '(null)', 'part': 'allpart', 'type': 'alltype', 'id': 'allid'}
            entry.update({params[i*2]:params[i*2+1] for i in range(len(params)/2)})
            if entry['dbid'] == '-1':
                entry['dbid'] = '(null)'
            if entry['part'] == 'allpart':
                entry['part'] = -1
            if entry['type'] == 'alltype':
                entry['type'] = -1
            if entry['id'] == 'allid':
                entry['id'] = -1
            l.info(entry)
            self.controller.showProvEntry(entry)
        else:
            l.info('pass url: ' + url)
        
    @QtCore.pyqtSlot()
    def on_actionOpen_PDF_triggered(self):
        #~ print self.html.page().mainFrame().evaluateJavaScript("SecondaryToolbar.openFileClick()")
        #~ return
        try:
            path = self.config.db['lastopenpdf']
        except KeyError:
            path = '/home/quanpt/temp/pdf/linky'
            #'/home/quanpt/assi/cde/mytest/nbest/cde-package/provenance.cde-root.1.log_db')
            #'/home/quanpt/assi/cde/mytest/bash/cde-package/provenance.cde-root-Y65bDAhpeDT_Z6fa9m4LFtO.1.log_db')
        
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open PDF file', path)
            
        if fname != "":
            self.on_actionClose_triggered()
            self.loadPdf(fname)
            self.config.db['lastopenpdf'] = fname
            pdftoread = PdfFileReader(open(fname, 'rb'))
            self.pdfinfo = pdftoread.getDocumentInfo()
            #~ l.info(self.pdfinfo)
            try:
                self.controller.loadProvWindow(self.pdfinfo["/sole.baseurl"], \
                    self.pdfinfo["/sole.file"], self.pdfinfo["/sole.dbid"])
            except KeyError:
                l.warn('pdfinfo error')
            
    def loadPdf(self, fname):
        url = scriptdir+'/pdf/web/viewer.html' + ('' if fname == '' else ('?file='+fname))
        self.html.hide()
        self.html.load(QtCore.QUrl(url))
        self.html.setZoomFactor(0)
        QtCore.QTimer.singleShot(700, self.updateview)

    def updateview(self):
        l.info('')
        self.html.setZoomFactor(1.0)
        self.html.show()
        

    @QtCore.pyqtSlot()
    def on_actionClose_triggered(self):
        l.info('')
        pass

    @QtCore.pyqtSlot()
    def on_actionQuit_triggered(self):
        self.on_actionClose_triggered()
        self.controller.quit()

# http://qt-project.org/wiki/Handling_PDF
