import os, db, pickle
from configuration import Configuration
from provwindow import ProvWindow
from PyQt4 import QtGui

class Controller():
    def __init__(self, app):
        self.app = app
        self.__windows = []
        self.config = Configuration()
        self.loadSetting()
        self.db = db.DB(self, self.config.db)
        self.provwindow = None
        
    def clipcopy(self, msg):
        clipboard = self.app.clipboard()
        clipboard.setText(msg)
        
    def showError(self, msg):
        QtGui.QMessageBox(None).warning(None, "Error", "Error: " + msg)

    def loadSetting(self):
        self.configFile = os.path.expanduser("~/.solegui.conf")
        if os.path.isdir(os.path.expanduser("~/.config")):
            self.configFile = os.path.expanduser("~/.config/solegui.conf")
        if os.path.exists(self.configFile):
            pklFile = open(self.configFile, 'rb')
            try:
                newconfig = pickle.load(pklFile)
            except Exception:
                newconfig = Configuration()
            newconfig.db['commonFilterList'].extend(self.config.db['commonFilterList'])
            newconfig.db['commonFilterList'] = list(set(newconfig.db['commonFilterList']))
            self.config.db.update(newconfig.db)
            pklFile.close()
            
    def quit(self):
        self.saveSetting()
        QtGui.QApplication.quit()
            
    def saveSetting(self):
        output = open(self.configFile, 'wb')
        pickle.dump(self.config, output)
        output.close()
        
    def addWindow(self, window):
        self.__windows.append(window)
        if isinstance(window, ProvWindow):
            self.provwindow = window

    def showWindows(self):
        desktop = QtGui.QApplication.desktop()
        screen = desktop.screenNumber()
        srect = desktop.availableGeometry(screen)
        w = srect.width()
        h = srect.height()
        for current_child_window in self.__windows:
            if isinstance(current_child_window, ProvWindow):
                current_child_window.resize(3 * w / 5, h)
                current_child_window.move(2 * w / 5 + srect.x(), srect.y())
                current_child_window.show()
            else: # pdf window
                current_child_window.resize(3 * w / 5, h)
                current_child_window.move(srect.x(), srect.y())
                current_child_window.show()
             
    def loadProvWindow(self, baseurl, filename, dbid):
        self.provwindow.loadProvWindow(baseurl, filename, dbid)
             
    def showProvEntry(self, entry):
        try:
            self.provwindow.showEntry(entry)
        except AttributeError:
            print "not load prov window yet???"
