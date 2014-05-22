from leveldb import LevelDB, LevelDBError
from provgraph import *
from collections import deque
import os, re, sys, time, struct, socket, logging as l, socket as sk


l.basicConfig(format='[File "%(filename)s" line %(lineno)d - %(funcName)s - %(levelname)s] %(message)s', \
    level=l.INFO)

class DB(object):
    def __init__(self, app, config):
        self.app = app
        self.config = config

    def opendb(self, path):
        try:
            self.db = LevelDB(str(path), create_if_missing = False)
        except LevelDBError:
            self.db = None
            msg = "'" + path + "' not found or not a LevelDB database!"
            l.error(msg)
            self.app.showError(msg)
            return False
        try:
            self.root = self.db.Get('meta.root')
            self.fullns = self.db.Get('meta.fullns')
            self.agent = self.db.Get('meta.agent')
            self.namespace = self.db.Get('meta.namespace')
            self.cderoot = path + '/../' + self.namespace
            self.path = path
            self.dbfilename = os.path.basename(str(path))
            self.dbpath = os.path.dirname(os.path.realpath(str(path)))
            try:
                self.dbid = self.db.Get('meta.dbid')
            except KeyError:
                self.dbid = None
            l.debug("path: %s", path)
            l.debug("meta.nomalized: %s", self.db.Get('meta.nomalized')) # make sure "actual" attr added
            l.debug("root %s, fullns %s, agent %s, ns %s", \
                self.root, self.fullns, self.agent, self.namespace)
            
        except KeyError:
            self.db = None
            msg = "Leveldb '" + path + "' is not a valid PALLY db!"
            l.error(msg)
            self.app.showError(msg)
            return True
        return True
            
    def close(self):
        self.db = None
            
    def getFileInfo(self, fid):
        return "%s" % fid

    def getProcessInfoOther(self, pid):
        # prv.pid.$(pid.usec).stat.$usec -> $fullstring
        mydb = self.db
        res = {}
        for (k, v) in mydb.RangeIter(key_from='prv.pid.'+pid+'.stat.', key_to='prv.pid.'+pid+'.stat.zzz'):
            time = k.split('.')[-1]
            res[time] = v
        return res
        
    def getRootChild(self):
        return self.getOneChild(self.db, self.root)

    def getOneChild(self, mydb, pidkey):
        res = list(mydb.RangeIter(key_from='prv.pid.'+pidkey+'.actualexec.', \
            key_to='prv.pid.'+pidkey+'.actualexec.zzz'))

        if len(res) == 0:
            l.error(pidkey)

        l.debug('%s %s', pidkey, res[0][1])
        if len(res) > 1:
            print 'WARNING: too many ', pidkey, '\'s children: ', str(res), '\n'
            print 'WARNING: use PALLY as child\n'
            return self.root
        return res[0][1]

    def getCurrentView(self, pid, dbid):
        
        pgraph = ProveGraph()
        depth = self.config['depth']
        self.igorePaths = set()
        if dbid == self.dbid:
            self.printTreeDFS(pgraph, pid, depth, self.db)
        else:
            newdb = self.openDB(dbid)
            if not newdb is None:
                self.printTreeDFS(pgraph, pid, depth, newdb)
        #~ self.printTreeBFS(pgraph, pid, depth, tempFilter)
        l.info("ignorePaths: " + str(self.igorePaths))
        return pgraph
        
    #~ def printTreeBFS(self, pgraph, pid, depth, tempFilter): # not used anymore
        #~ tempFilter = '.*' + self.config['tempFilterText'] + '.*'
        #~ pidqueue = deque([pid])
        #~ lastpid = pid # store the last pid to process before going above given depth
        #~ 
        #~ while len(pidqueue) > 0:
            #~ 
            #~ pidkey = pidqueue.popleft()
        #~ 
            #~ #label = 'PID: ' + pidkey.split('.')[0] + "\\n" + \
            #~ path = getExecAttr(self.db, pidkey, 'path')
            #~ label = os.path.basename(path)
            #~ highlight = self.config['tempFilter'] and re.match(tempFilter, path)
            #~ pgraph.addProcNode(pidkey, label, highlight)
            #~ 
            #~ if self.config['showFile']:
                #~ # prv.iopid.$(actualppid.usec).actual.$action.$usec -> $filepath
                #~ for (k, path) in self.db.RangeIter(key_from='prv.iopid.'+pidkey+'.actual.', key_to='prv.iopid.'+pidkey+'.actual.zzz'):
                    #~ if self.config['commonFilter'] and self.isFilteredPath(path):
                        #~ continue
                    #~ highlight = self.config['tempFilter'] and re.match(tempFilter, path)
                    #~ pgraph.addFileNode(path, os.path.basename(path), highlight)
                    #~ pgraph.addFileEdge(pidkey, path, getFileAction(k))
            #~ 
            #~ if depth > 0: # still not reach graph leaf yet
                #~ # prv.pid.$(actualppid.usec).actualexec.$usec -> $(actualpid.usec)
                #~ for (k, v) in self.db.RangeIter(key_from='prv.pid.'+pidkey+'.actualexec.', key_to='prv.pid.'+pidkey+'.actualexec.zzz'):
                    #~ try:
                        #~ self.db.Get('prv.pid.'+v+'.ok') # assert process successfully run
                        #~ pgraph.addProcEdge(pidkey, v)
                        #~ pidqueue.append(v)
                    #~ except KeyError:
                        #~ l.error("DB.getCurrentView KeyError: %s", pidkey)
                        #~ 
                #~ if path[-4:] == '/ssh':
                    #~ dbid = getExecAttr(self.db, pidkey, 'dbid')
                    #~ self.printSSHNode(pgraph, pidkey, dbid, depth - 1)
            #~ 
            #~ if pidkey == lastpid:
                #~ if depth == 0 or len(pidqueue)==0:
                    #~ return pgraph
                #~ else:
                    #~ lastpid = pidqueue[-1]
                    #~ depth -= 1

    def getProcessInfoNetwork(self, pidkey):
        # prv.pid.$(pid.usec).sock.$usec.$action.$sockfd.$len_param.$flags.$len_resutl -> $memoryblock
        res = {}
        for (k, v) in self.db.RangeIter(key_from='prv.pid.'+pidkey+'.sock.', key_to='prv.pid.'+pidkey+'.sock.zzz'):
            (time, action, sockfd, len_param, flags, len_result) = k.split('.')[5:]
            res[time] = [action, sockfd, len_param, flags, len_result, v]
        return res
        
    def printTreeDFS(self, pgraph, pidkey, depth, mydb):
        tempFilter = '.*' + self.config['tempFilterText'] + '.*'
        pidpath = getExecAttr(mydb, pidkey, 'path')
        label = os.path.basename(pidpath)
        highlight = self.config['tempFilter'] and \
            (re.match(tempFilter, pidpath) or re.match(tempFilter, pidkey))
        pinfo = getProcessInfo(mydb, pidkey)
        if not pinfo is None:
            pinfo['ppid'] = pinfo['ppid'].split('.')[0]
            pinfo['pid'] = pinfo['pid'].split('.')[0]
            pinfo['start'] = time.ctime(int(pinfo['start'])/1000000)
            try:
                pinfo['lexit'] = time.ctime(int(pinfo['lexit'])/1000000)
            except KeyError:
                pinfo['lexit'] = 'Unknown'
        
        pgraph.addProcNode(pidkey, label, {'details':pinfo, 'hl':highlight, 'dbid':getDbId(mydb)})
        
        if self.config['showFile']:
            # prv.iopid.$(actualppid.usec).actual.$action.$usec -> $filepath
            for (k, fpath) in mydb.RangeIter(key_from='prv.iopid.'+pidkey+'.actual.', \
                    key_to='prv.iopid.'+pidkey+'.actual.zzz'):
                if (self.config['commonFilter'] and self.isFilteredPath(fpath)) or (k[-3:] == '.fd'):
                    continue
                highlight = self.config['tempFilter'] and re.match(tempFilter, fpath)
                pgraph.addFileNode(fpath, os.path.basename(fpath), \
                    {'details':fpath, 'hl':highlight, 'dbid':getDbId(mydb)})
                pgraph.addFileEdge(pidkey, fpath, getFileAction(k))

        if depth > 0: # still not reach graph leaf yet
            # prv.pid.$(actualppid.usec).actualexec.$usec -> $(actualpid.usec)
            for (k, v) in mydb.RangeIter(key_from='prv.pid.'+pidkey+'.actualexec.', \
                    key_to='prv.pid.'+pidkey+'.actualexec.zzz'):
                try:
                    mydb.Get('prv.pid.'+v+'.ok') # assert process successfully run
                    ppath = getExecAttr(mydb, v, 'path')
                    if self.config['commonFilter'] and self.isFilteredPath(ppath):
                        continue
                    pgraph.addProcEdge(pidkey, v)
                    self.printTreeDFS(pgraph, v, depth - 1, mydb)
                except KeyError:
                    l.error("printTreeDFS KeyError: %s", pidkey)

            if pidpath[-4:] == '/ssh':
                dbid = getExecAttr(mydb, pidkey, 'dbid')
                l.debug(dbid)
                self.printSSHNode(pgraph, pidkey, dbid, depth - 1)

    def printSSHNode(self, pgraph, pidkey, dbid, depth):
        newdb = self.openDB(dbid)
        if newdb is None:
            return
        newroot = newdb.Get('meta.root')
        l.debug(newroot)
        newpid = self.getOneChild(newdb, newroot)
        pgraph.addProcEdge(pidkey, newpid)
        self.printTreeDFS(pgraph, newpid, depth, newdb)
        

    def isFilteredPath(self, path):
        for pattern in self.config['commonFilterList']:
            if re.match(pattern, path) and path[-4:] != '/ssh':
                self.igorePaths.add(path)
                return True
        return False
        
    def openDB(self, dbid):
        dbpath = self.dbpath + '/provenance.cde-root.1.log.id' + dbid + '_db'
        try:
            newdb = LevelDB(str(dbpath), create_if_missing = False)
        except LevelDBError:
            newdb = None
            l.error("'%s' not found or not a LevelDB database!", dbpath)
        return newdb
        
def getFileAction(pidkey):
    return pidkey.split('.')[-2]

def getExecAttr(mydb, pidkey, attr):
    try:
        return mydb.Get('prv.pid.'+pidkey+'.'+attr)
    except KeyError:
        l.warning('getExecAttr prv.pid.%s.%s: error', pidkey, attr)
        return 'PALLY'

def getProcessInfo(mydb, pid):
    # prv.pid.$(pid.usec).parent -> $(ppid.usec)
    # prv.pid.$(ppid.usec).exec.$usec -> $(pid.usec)
    # prv.pid.$(pid.usec).[path, pwd, args] -> corresponding value of EXECVE
    try:
        res = { 'pid' :pid, \
                'ppid':mydb.Get('prv.pid.'+pid+'.parent'), \
                'path':mydb.Get('prv.pid.'+pid+'.path'), \
                'pwd' :mydb.Get('prv.pid.'+pid+'.pwd'), \
                'args':mydb.Get('prv.pid.'+pid+'.args'), \
                'start':mydb.Get('prv.pid.'+pid+'.start')}
        try:
            res['lexit'] = mydb.Get('prv.pid.'+pid+'.lexit')
        except KeyError:
            pass
            
        # prv.sock.$(pid.usec).newfd.$usec.$sockfd.$buflen.$urval
        #~ nwres = {}
        #~ for (k, v) in mydb.RangeIter(key_from='prv.sock.'+pid+'.newfd.', key_to='prv.sock.'+pid+'.newfd.zzz'):
            #~ (time, sockfd, buflen, result) = k.split('.')[5:]
            #~ addr = parseSockaddr(v)
            #~ nwres[time] = addr
        #~ res['nwcn'] = nwres
        
        # prv.pid.$(pid.usec).listenid.$listenid.accept.$acceptid.addr
        #~ nwres = {}
        #~ for (k, v) in mydb.RangeIter(key_from='prv.pid.'+pid+'.listenid.', key_to='prv.pid.'+pid+'.listenid.zzz'):
            #~ if k[-5:] == '.addr' and k.find('.accept.') > 0 and len(v) > 0:
                #~ (lid, _, aid, _) = k.split('.')[5:]
                #~ addr = parseSockaddr(v)
                #~ nwres[lid + '.' + aid] = addr
        #~ res['nwac'] = nwres
        
        # prv.sock.$(pid.usec).newfdips.$usec.$sockfd.$buflen.$urval
        nwcn = {}
        for (k, v) in mydb.RangeIter(key_from='prv.sock.'+pid+'.newfdips.', key_to='prv.sock.'+pid+'.newfdips.zzz'):
            (time, sockfd, buflen, result) = k.split('.')[5:]
            if result >= 0 and len(v) > 0:
                nwcn[time] = v
        res['nwcn'] = nwcn
        
        # prv.pid.$(pid.usec).skac.$usec.listenid.$listenid.accept.$acceptid.ips
        nwac = {}
        for (k, v) in mydb.RangeIter(key_from='prv.pid.'+pid+'.skac.', key_to='prv.pid.'+pid+'.skac.zzz'):
            if len(v) > 0:
                (time, _, lid, _, aid, _) = k.split('.')[5:]
                addr = v.split('.')
                addr = '.'.join([addr[x] for x in [2,3,0,1]]) # order: source, dest
                nwac[time] = addr
        res['nwac'] = nwac
        
        return res
    except KeyError:
        l.error( 'KeyError: %s\n', pid )
    return None

"""
struct sockaddr {
    unsigned short    sa_family;    // address family, AF_xxx
    char              sa_data[14];  // 14 bytes of protocol address
};

// IPv4 AF_INET sockets:

struct sockaddr_in {
    short            sin_family;   // e.g. AF_INET, AF_INET6
    unsigned short   sin_port;     // e.g. htons(3490)
    struct in_addr   sin_addr;     // see struct in_addr, below
    char             sin_zero[8];  // zero this if you want to
};

struct in_addr {
    unsigned long s_addr;          // load with inet_pton()
};

aws: host#: internal IP - external IP
1: 10.152.199.92 - 54.204.236.254
2: 10.185.210.251 - 54-205-73-120
3: 10.179.40.209 - 54.234.175.254
"""
def parseSockaddr(buf):
    addr = {'sa_family':struct.unpack('=H', buf[0:2])[0]}
    if addr['sa_family'] == socket.AF_INET:
        addr.update({'sin_port':struct.unpack('=H', buf[2:4])[0], \
            'sin_addr':socket.inet_ntoa(buf[4:8])})
    return addr

def getDbId(mydb):
    try:
        return mydb.Get('meta.dbid')
    except KeyError:
        return None

def getIpInfo(label):
    label = label.split('.')
    (source, dest) = [''.join([chr(int(label[y][2*x:2*x+2], 16)) for x in range(3,-1,-1)]) for y in [0,2]]
    return sk.inet_ntop(sk.AF_INET, source) + ':' + str(int(label[1], 16)) + '\n' + \
        sk.inet_ntop(sk.AF_INET, dest) + ':' + str(int(label[3], 16))
