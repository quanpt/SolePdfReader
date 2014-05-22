import sys, webbrowser, os, pprint, tempfile, subprocess, pyqtgraph as pg
import urllib, tarfile, logging as l, threading
from PyQt4 import QtGui, QtCore
from ui_mainwindow import *
from ui_about import *
from configuration import Configuration
from db import DB

l.basicConfig(format='[File "%(filename)s" line %(lineno)d - %(funcName)s - %(levelname)s] %(message)s', \
    level=l.INFO)

class ProvWindow(QtGui.QMainWindow, Ui_ProvWindow):
    def __init__(self, controller):
        QtGui.QMainWindow.__init__(self)
    
        self.controller = controller
        self.config = controller.config
        
        self.db = controller.db
        self.pidList = []
        
        # Set up the user interface from Designer.
        self.setupUi(self)
        self.graph.setCallback(self)
        
        self.initSetting()
        
        #~ self.on_actionOpen_Provenance_triggered()
        
    def initSetting(self):
        # GUI
        self.spinBoxDepth.setValue(self.config.db['depth'])
        self.lineEditTempFilter.setText(self.config.db['tempFilterText'])
        self.on_pushButtonRestoreFilter_clicked()
        
        # set up all checkboxes
        for k in self.config.db.keys():
            v = self.config.db[k]
            if isinstance(v, bool):
                label = k[0].upper()+k[1:]
                try:
                    getattr(self, 'checkBox' + label).setChecked(v)
                except AttributeError: # configure from old version
                    del self.config.db[k] # or pass to keep it?
        
        # left info graph
        p1 = self.contentGraph.plotItem
        pen1 = QtGui.QPen(QtCore.Qt.yellow, 0)
        p1.getAxis('left').setPen(pen1)
        pen2 = QtGui.QPen(QtCore.Qt.green, 0)
        p1.showAxis('right')
        p1.getAxis('right').setPen(pen2)
        self.contentGraph.plot2 = pg.ViewBox()
        p1.scene().addItem(self.contentGraph.plot2)
        p1.getAxis('right').linkToView(self.contentGraph.plot2)
        self.contentGraph.plot2.setXLink(p1)
        p1.vb.sigResized.connect(self.updateContentGraphViews)
        
        # full stat graph
        self.fullStatsGraph.legend = self.fullStatsGraph.plotItem.addLegend()
    
    def showFileInfo(self, fid, finfo):
        #~ self.content.setText("File info: %s" % self.db.getFileInfo(fid))
        self.content.setText("File info: %s" % finfo)
        self.statusbar.showMessage("File dbid: %s" % fid)
        self.tab.setCurrentWidget(self.mainTab)
        self.clearContentGraph()
        
    def showSockInfo(self, fid, finfo):
        #~ self.content.setText("File info: %s" % self.db.getFileInfo(fid))
        self.content.setText("Sock info: \n%s" % finfo)
        self.statusbar.showMessage("Sock dbid: %s" % fid)
        self.tab.setCurrentWidget(self.mainTab)
        self.clearContentGraph()

    def showProcessInfo(self, pid, info):
        
        self.currentShowPid = pid
        self.currentShowInfo = info
        self.currentShowDbid = info['dbid']
        if info['details'] is None:
            self.content.setText('Process info not available')
            self.currentPInfo = None
        else:
            content = "DBID: %s" % info['dbid'] + """
Parent Pid: %(ppid)s
Pid: %(pid)s
Path: %(path)s
Pwd: %(pwd)s
Args: %(args)s
Start Time: %(start)s
End Time: %(lexit)s
Nwcn: %(nwcn)s
Nwac: %(nwac)s""" % info['details']
            self.content.setText(content)
            
            self.currentPInfo = info['details']
            self.currentPInfo['pidkey'] = self.currentShowPid
            self.currentPInfo['dbid'] = info['dbid']
        
        self.drawStatisticGraph(pid, info['dbid'])
        
        self.statusbar.showMessage("Process dbid: %s" % pid)
        self.tab.setCurrentWidget(self.mainTab)
        
    def clearContentGraph(self):
        self.contentGraph.plotItem.clear()
        self.contentGraph.plot2.clear()
                
    STAT_utime = 13
    STAT_stime = 14
    STAT_vsize = 22
    STAT_rss = 23
    def drawStatisticGraph(self, pid, dbid):
        self.clearContentGraph()
        self.updateContentGraphViews()
        if dbid != self.db.dbid:
            return
        
        pinfoother = self.db.getProcessInfoOther(pid)
        data = []
        for k, v in sorted(pinfoother.items()):
            data.append([float(k)/1000000] + v.split(' '))
        if len(data) == 0:
            return

        minx = min([d[0] for d in data])
        xaxis = [d[0]-minx for d in data]
        p1 = self.contentGraph.plotItem.plot( \
            x=xaxis, y=[int(d[self.STAT_utime]) for d in data], \
            pen='y')
        p2 = pg.PlotCurveItem(x=xaxis, \
            y=[float(d[self.STAT_rss])/1048576 for d in data], \
            pen='g')
        self.contentGraph.plot2.addItem(p2)
        
        # update Legend once
        try:
            self.contentGraph.legend
        except NameError:
            self.contentGraph.legend = self.contentGraph.plotItem.addLegend()
            self.contentGraph.legend.addItem(p1, "User Time (second)")
            self.contentGraph.legend.addItem(p2, "Resident Memory (MB)")
    
    def updateContentGraphViews(self):
        ## view has resized; update auxiliary views to match
        p1 = self.contentGraph.plotItem
        p2 = self.contentGraph.plot2
        p2.setGeometry(p1.vb.sceneBoundingRect())
        p2.linkedViewChanged(p1.vb, p2.XAxis)
        
    def focusProcess(self, pid, dbid):
        if len(self.pidList)==0 or pid != self.pidList[-1][0]:
            self.graph.clear()
            self.drawProvGraph(self.db.getCurrentView(pid, dbid))
            self.pidList.append((pid, dbid))
        #~ if pid != self.db.root:
            #~ self.showProcessInfo(pid)
        self.graphTab.setCurrentWidget(self.provTab)
            
        
    def showError(self, msg):
        self.statusbar.showMessage("Error: " + msg)
        QtGui.QMessageBox(self).warning(self, "Error", "Error: " + msg)
        
    def drawProvGraph(self, graph):
        # processes
        for (pid, label, info) in graph.processes:
            self.graph.addProcNode(pid, label, info)
        for (p1, p2) in graph.pedges:
            self.graph.addProcEdge(p2, p1, 0)
        # files
        for fname, (label, info) in graph.files.iteritems():
            self.graph.addFileNode(fname, label, info)
        for (pid, fname, action) in graph.fedges:
            self.graph.addFileEdge(pid, fname, action)
        # sockets
        for (sock, (_, info)) in graph.socks.iteritems():
            self.graph.addSockNode(sock, info)
        for (pid, sock) in graph.scedges:
            self.graph.addConnectEdge(pid, sock)
        for (pid, sock) in graph.saedges:
            self.graph.addAcceptEdge(pid, sock)
        # center
        self.graph.setCenterNode(graph.root)
        
    def reloadProvGraph(self):
        self.graph.clear()
        if len(self.pidList) > 0:
            self.drawProvGraph(self.db.getCurrentView(self.pidList[-1][0], self.pidList[-1][1]))
        else:
            l.info("len self.pidList == 0")
        
    @QtCore.pyqtSlot()
    def on_actionRefresh_triggered(self):
        self.statusbar.showMessage("Graph refresh.")
        
    @QtCore.pyqtSlot()
    def on_actionBack_triggered(self):
        if len(self.pidList) > 1:
            self.pidList.pop() # remove the current one
            (pid, dbid) = self.pidList.pop()
            self.focusProcess(pid, dbid)
    
    @QtCore.pyqtSlot()
    def on_actionForward_triggered(self):
        pass
        
    @QtCore.pyqtSlot()
    def on_actionHelp_triggered(self):
        webbrowser.open("https://sites.google.com/site/pallysystem/pally")
        self.statusbar.showMessage("Help website has been opened externally.")
    
    @QtCore.pyqtSlot()
    def on_actionAbout_triggered(self):
        self.statusbar.showMessage("Show About Dialog.")
        about = QDialog(self)
        Ui_About().setupUi(about)
        about.exec_()
        
    @QtCore.pyqtSlot()
    def on_actionOpen_triggered(self):
        self.showError('hello')
        pass
        
    @QtCore.pyqtSlot()
    def on_actionOpen_Provenance_triggered(self):
        try:
            path = self.config.db['lastopendb']
        except KeyError:
            path = '/home/quanpt/assi/cde/mytest/net/cde-package/provenance.cde-root.1.log_db'
            #'/home/quanpt/assi/cde/mytest/nbest/cde-package/provenance.cde-root.1.log_db')
            #'/home/quanpt/assi/cde/mytest/bash/cde-package/provenance.cde-root-Y65bDAhpeDT_Z6fa9m4LFtO.1.log_db')
        
        dname = QtGui.QFileDialog.getExistingDirectory(self, 'Open DB Directory', path)
            
        if dname != "":
            self.openDir(dname)
                
    def openDir(self, dname):
        self.on_actionClose_triggered()
        if self.db.opendb(dname):
            self.statusbar.showMessage('DB opened.')
            self.pidList = []
            self.focusProcess(self.db.getRootChild(), self.db.dbid)
            self.config.db['lastopendb'] = dname
            self.show()
            return True
        else:
            return False
    
    @QtCore.pyqtSlot()
    def on_actionClose_triggered(self):
        self.db.close()
        self.content.setText('')
        self.graph.clear()
        self.statusbar.showMessage('DB closed.')

    @QtCore.pyqtSlot()
    def on_actionQuit_triggered(self):
        self.on_actionClose_triggered()
        self.controller.quit()
    
    @QtCore.pyqtSlot()
    def on_pushButtonEnableEditor_clicked(self):
        self.tab.setCurrentWidget(self.editTab)
        #~ QtGui.QMessageBox.information(self, "Not Implemented Yet", \
            #~ "This feature is not implemented yet!")
    
    @QtCore.pyqtSlot()
    def on_pushButtonReExecute_clicked(self):
        if self.currentPInfo is None:
            QtGui.QMessageBox.information(self, "Invalid process", \
                "This process cannot be re-executed!")
            return
            
        pwd = self.currentPInfo['pwd']
        args = self.currentPInfo['args'][2:-2].replace('", "', ' ')
        dbid = self.currentPInfo['dbid']
        dbfilename = self.db.dbfilename if dbid == '(null)' \
            else "provenance.cde-root.1.log.id" + dbid + "_db"
        
        # TODO: parse args properly (escape stuff)
        param = "-N " + dbfilename + " -P " + self.currentPInfo['pidkey']
        # TODO: option of replay network or not
        
        (osfd, fname) = tempfile.mkstemp()
        fd = os.fdopen(osfd, 'w')
        fd.write("#!/bin/sh\n" + \
            "cd " + self.db.cderoot + pwd + "\n" + \
            self.db.cderoot + "/../cde-exec " + param + " " + args)
        fd.close()
        print "xterm -hold -e /bin/sh " + fname
        self.db.close() # one process can open db only :(
        os.system("xterm -hold -e /bin/sh " + fname)
        os.system("xterm -hold -e /bin/cat " + fname)
        self.db.opendb(self.db.path)
        os.system("rm " + fname)
        
        #~ {'args': '["/usr/bin/java", "TestExecLs"]', 'pid': '22012', 'start': 'Wed Feb 26 11:20:42 2014', 
        #~ 'pwd': '/home/quanpt/assi/cde/mytest/javart', 'lexit': 'Unknown', 'path': '/usr/bin/java', 'ppid': '21992'}
        
    @QtCore.pyqtSlot(bool)
    def on_checkBoxShowFile_toggled(self, state):
        if (self.config.db['showProc'] or state):
            self.updateConfigReload('showFile', state)
        else:
            self.checkBoxShowFile.setChecked(not state)
            
    @QtCore.pyqtSlot(bool)
    def on_checkBoxShowProc_toggled(self, state):
        if (self.config.db['showFile'] or state):
            self.updateConfigReload('showProc', state)
        else:
            self.checkBoxShowProc.setChecked(not state)
        
    @QtCore.pyqtSlot(int)
    def on_spinBoxDepth_valueChanged(self, value):
        self.updateConfigReload('depth', value)
    @QtCore.pyqtSlot(bool)
    def on_checkBoxShowAll_toggled(self, state):
        self.updateConfigReload('showAll', state)
    @QtCore.pyqtSlot(bool)        
    def on_checkBoxTempFilter_toggled(self, state):
        self.updateConfigReload('tempFilter', state)
    @QtCore.pyqtSlot(bool)
    def on_checkBoxCommonFilter_toggled(self, state):
        self.updateConfigReload('commonFilter', state)
        
    def on_lineEditTempFilter_textEdited(self, state):
        if self.config.db['tempFilterText'] != str(state):
            self.config.db['tempFilterText'] = str(state)
            if self.config.db['tempFilter']:
                self.reloadProvGraph()
    
    def updateConfigReload(self, variable, state):
        try:
            if self.config.db[variable] != state:
                self.config.db[variable] = state
                self.reloadProvGraph()
        except KeyError:
            print "updateConfigReload - KeyError: ", variable, state
            self.config.db[variable] = state
            self.reloadProvGraph()
        #~ print "Config: variable, '->', state, self.config.db[variable]
    
    @QtCore.pyqtSlot()
    def on_pushButtonBack_clicked(self):
        self.on_actionBack_triggered()
    
    @QtCore.pyqtSlot()
    def on_pushButtonResetFilter_clicked(self):
        temp = Configuration()
        self.config.db['commonFilterList'] = list(temp.db['commonFilterList'])
        self.reloadProvGraph()
        
    def updateStatsGraphReload(self, variable, state):
        try:
            if self.config.db[variable] != state:
                self.config.db[variable] = state
                self.reloadStatsGraph()
        except KeyError:
            self.config.db[variable] = state
            self.reloadStatsGraph()
            
    def reloadStatsGraph(self):
        if len(self.pidList) > 0:
            self.fullStatsGraph.clear()
            self.drawFullStatsGraph(self.currentShowPid)
    
    STAT_nw_action = 1        
    STAT_nw_lenresult = 5
    STAT_GraphLabels = ["User Time (second)", "Resident Memory (MB)", \
        "I/O Read (kB)", "I/O Write (kB)", "No. of Threads", \
        "Network Send (kB)", "Network Receive (kB)"]
    def drawFullStatsGraph(self, pid):
        self.clearFullStatGraph()
        # self.updateFulStatsGraphViews()
        self.drawCPUMemGraph(pid, \
            self.config.db['graphCPU'], self.config.db['graphMem'])
        if self.config.db['graphThread']:
            self.drawThreadGraph(pid)
        if self.config.db['graphIO']:
            self.drawIOGraph(pid)
        if self.config.db['graphNetwork']:
            self.drawNetworkGraph(pid)
            
    def drawThreadGraph(self, pid):
        print "TODO: drawThreadGraph"
    def drawIOGraph(self, pid):
        print "TODO: drawIOGraph"
            
    def drawNetworkGraph(self, pid):
        pinfo = self.db.getProcessInfoNetwork(pid)
        data = []
        for k, v in sorted(pinfo.items()):
            data.append([float(k)/1000000] + v)
        if len(data) == 0:
            return
        # [[1390360745.094742, '1', '9', '5', '0', '5', 'hello'], ...]

        minx = min([d[0] for d in data])
        xaxis = [d[0]-minx for d in data]
        send = [[d[0]-minx, int(d[self.STAT_nw_lenresult])] for d in data if d[self.STAT_nw_action] == '0']
        receive = [[d[0]-minx, int(d[self.STAT_nw_lenresult])] for d in data if d[self.STAT_nw_action] == '3']
        
        p1 = self.fullStatsGraph.plotItem.plot( \
            x=[x for (x,_) in send], y=[y for (_,y) in send], pen='r')
        p2 = self.fullStatsGraph.plotItem.plot( \
            x=[x for (x,_) in receive], y=[y for (_,y) in receive], pen='b')

        # update Legend
        self.fullStatsGraph.legend.addItem(p1, self.STAT_GraphLabels[5])
        self.fullStatsGraph.legend.addItem(p2, self.STAT_GraphLabels[6])
        
    def drawCPUMemGraph(self, pid, cpuOn = True, memOn = True):
        if not cpuOn and not memOn:
            return
        pinfo = self.db.getProcessInfoOther(pid)
        data = []
        for k, v in sorted(pinfo.items()):
            data.append([float(k)/1000000] + v.split(' '))
        if len(data) == 0:
            return

        minx = min([d[0] for d in data])
        xaxis = [d[0]-minx for d in data]

        if cpuOn:
            p1 = self.fullStatsGraph.plotItem.plot( \
                x=xaxis, y=[int(d[self.STAT_utime]) for d in data], \
                pen='y')
            self.fullStatsGraph.legend.addItem(p1, self.STAT_GraphLabels[0])

        if memOn:
            p2 = self.fullStatsGraph.plotItem.plot( \
                x=xaxis, y=[float(d[self.STAT_rss])/1048576 for d in data], \
                pen='g')
            self.fullStatsGraph.legend.addItem(p2, self.STAT_GraphLabels[1])
        
    def clearFullStatGraph(self):
        self.fullStatsGraph.clear()
        for label in self.STAT_GraphLabels:
            self.fullStatsGraph.legend.removeItem(label)
            
    def updateFulStatsGraphViews(self):
        pass
            
    @QtCore.pyqtSlot(bool)
    def on_checkBoxGraphCPU_toggled(self, state):
        self.updateStatsGraphReload('graphCPU', state)
    @QtCore.pyqtSlot(bool)
    def on_checkBoxGraphMem_toggled(self, state):
        self.updateStatsGraphReload('graphMem', state)
    @QtCore.pyqtSlot(bool)
    def on_checkBoxGraphThread_toggled(self, state):
        self.updateStatsGraphReload('graphThread', state)
    @QtCore.pyqtSlot(bool)
    def on_checkBoxGraphNetwork_toggled(self, state):
        self.updateStatsGraphReload('graphNetwork', state)
    @QtCore.pyqtSlot(bool)
    def on_checkBoxGraphIO_toggled(self, state):
        self.updateStatsGraphReload('graphIO', state)
    @QtCore.pyqtSlot(int)
    def on_graphTab_currentChanged(self, state):
        if state == 1:
            self.reloadStatsGraph()
    
    @QtCore.pyqtSlot()
    def on_actionCopy_ID_triggered(self):
        msg = "\sole"
        item = "enter your text here"
        if self.currentShowDbid != "(null)":
            msg += "[dbid=" + self.currentShowDbid + "]"
        try:
            item = os.path.basename(self.currentShowInfo['details']['path'])
        except KeyError:
            pass
        msg += "{" + self.currentShowPid + "}{" + item + "}"
        l.info(msg)
        self.controller.clipcopy(msg)

    @QtCore.pyqtSlot()
    def on_pushButtonSaveFilter_clicked(self):
        self.config.db['commonFilterList'] = str(self.textEditFilter.toPlainText()).replace('/','\/').split('\n')
        l.info(self.config.db['commonFilterList'])
        self.reloadProvGraph()
            
    @QtCore.pyqtSlot()
    def on_pushButtonRestoreFilter_clicked(self):
        self.textEditFilter.setText('\n'.join(self.config.db['commonFilterList']).replace('\/','/'))
            
    def loadProvWindow(self, baseurl, filename, dbid):
        self.tempdbid = dbid
        worker = Worker(self, self.loadProvWindowThread, self.loadThreadDone, (baseurl, filename, dbid))
        worker.start()
    
    def loadProvWindowThread(self, baseurl, filename, dbid):
        if not 'dbdir' in self.config.db.keys():
            self.config.db['dbdir'] = {}
        try:
            self.dburl = baseurl + '/' + filename
            self.tempdir = self.config.db['dbdir'][self.dburl]
            l.info('reuse tempdir at ' + self.tempdir)
        except KeyError:
            l.info('downloading db ...')
            self.tempdir = tempfile.mkdtemp()
            l.info('tempdir db in ' + self.tempdir)
            urllib.urlretrieve(baseurl + '/' + filename, self.tempdir + '/' + filename)
            l.info('done download ' + baseurl + '/' + filename)
            tar = tarfile.open(self.tempdir + '/' + filename)
            tar.extractall(self.tempdir)
            tar.close()
            l.info('extract done')
            self.config.db['dbdir'][baseurl + '/' + filename] = self.tempdir
    
    def loadThreadDone(self):
        if self.tempdbid == '-1':
            if self.openDir(self.tempdir + '/provenance.cde-root.1.log_db'):
                pass
            else:
                # delete the cache
                self.config.db['dbdir'].pop(self.dburl, None)

    def showEntry(self, entry):
        #~ {'dbid': 'mydbid44', 'part': -1, 'type': -1, 'id': 'myid11'}
        #~ handle dbid, handle part, handle type, handle id
        self.focusProcess(entry['id'], entry['dbid'])

class Worker(QtCore.QThread):
    """
        The idea of this thread is to run a time consuming process without shutting down
        your gui.  Whatever starts this process needs to clean it up by emitting a "cleanUp()" 
        signal is prefered.
    """
    def __init__(self,parent,action,callback,args=[],kwargs={}):
        QtCore.QThread.__init__(self,parent)
        parent.connect(self,QtCore.SIGNAL("finished()"),callback)
        self.action = action
        self.args = args
        self.kwargs = kwargs
        self.data = None
    def run(self):
        try:
            self.data = self.action(*self.args,**self.kwargs)
        finally:
            self.connect(self.parent(),QtCore.SIGNAL("cleanUp()"),QtCore.SLOT("deleteLater()"))
    def cleanUp(self):
        self.deleteLater()
    def get(self):
        return self.data
