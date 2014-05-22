class Configuration():
    def __init__(self):
        #~ self.sole = {}
        #~ self.ptu = {}
        #~ self.gui = {}
        self.db = {'depth':3, 'showFile':True, 'showProc':True, 'showAll':False, \
            'commonFilter':True, \
            'commonFilterList':['\/proc\/', '.*\/lib\/', '\/etc\/', \
                '\/dev\/', '\/sys\/', '.*\/R\/x86_64-pc-linux-gnu-library\/', \
                '.*\/usr\/share\/', '.*\/usr\/lib64\/', '.*\/.ssh\/'], \
            'tempFilter':False, 'tempFilterText':'',
            'graphCPU':True, 'graphMem':True, 'graphThread':False, 
            'graphIO':False, 'graphNetwork':False}
    def update(self, newconfig):
        self.sole.update(newconfig.sole)
        self.ptu.update(newconfig.ptu)
        self.gui.update(newconfig.gui)
        self.db.update(newconfig.db)
       
