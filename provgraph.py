class ProveGraph():
    def __init__(self):
        self.root = None
        self.processes = []     # list of string of leveldb id
        self.files = {}         # list of (should-be distinct) string of paths
        self.socks = {}         # list of (should-be distinct) string of ips (source ip, dest ip, ports)
        self.pedges = []        # list of edge process --> process
        self.fedges = []        # list of edge process <-> file
        self.scedges = []        # list of edge process -> sock
        self.saedges = []        # list of edge process <- sock
        self.hlprocesses = {}   # highlight processes
        self.hlfiles = {}       # highlight processes
    
    def addProcNode(self, pid, label, info):
        #~ print "addProcNode ", label
        if self.root == None:
            self.root = pid
        self.processes.append((pid, label, info))
        if info['hl']:
            self.hlprocesses[pid]=True
        try:
            for (k, v) in info['details']['nwcn'].iteritems():
                self.socks[v] = (v, info) # overwite info from accept if needed
                self.scedges.append((pid, v))
                
            for (k, v) in info['details']['nwac'].iteritems():
                if not v in self.socks:
                    self.socks[v] = (v, info)
                self.saedges.append((pid, v))
        except:
            pass
        
    def addProcEdge(self, pid1, pid2):
        #~ print "addProcEdge ", pid1, pid2
        self.pedges.append((pid1, pid2))
        
    def addFileNode(self, fname, label, info):
        #~ print "addFileNode ", label
        self.files[fname] = (label, info)
        if info['hl']:
            self.hlfiles[fname]=True
        
    def addFileEdge(self, pid, fname, action):
        #~ print "addFileEdge ", pid, fname, action
        self.fedges.append((pid, fname, action))

    def __str__(self):
        return "Processes: %s\nFiles: %s\nProcess edges: %s\nFile edges: %s\n" % \
            (self.processes, self.files, self.pedges, self.fedges)
