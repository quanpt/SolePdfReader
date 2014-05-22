from PyQt4 import *
from node import *
from edge import *
import math, random, hashlib, logging as l, db

l.basicConfig(format='[File "%(filename)s" line %(lineno)d - %(funcName)s - %(levelname)s] %(message)s', \
    level=l.INFO)

SOCK_EDGE = 10
    
class GraphWidget(QtGui.QGraphicsView):
    
    procdict = {}
    filedict = {}
    sockdict = {}
    nodepos = {}

    def __init__(self, parent):
        super(GraphWidget, self).__init__()
        self.timerId = 0

        scene = QtGui.QGraphicsScene(self)
        scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        scene.setSceneRect(-200, -200, 400, 400)
        self.setScene(scene)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QtGui.QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        
        self.scale(0.8, 0.8)
        self.setMinimumSize(400, 400)
        self.setWindowTitle("Elastic Nodes")
        
    def setCallback(self, app):
        self.app = app
    
    def addNode(self, node):
        self.scene().addItem(node)
        try:
            node.setPos(self.nodepos[node.dbid])
        except KeyError:
            node.setPos(random.randint(-self.width()/2, self.width()/2), \
                random.randint(-self.height()/2, self.height()/2))
        
    def addProcNode(self, pid, label, info):
        node = ProcessNode(self, pid, label, info)
        self.procdict[pid] = node
        self.addNode(node)
        
    def addProcEdge(self, pid1, pid2, rel):
        try:
            node1 = self.procdict[pid1]
            node2 = self.procdict[pid2]
            self.scene().addItem(Edge(node1, node2, rel))
        except KeyError:
            print "Error: cannot find pid %s or %s\n" % (pid1, pid2)
        
    def setCenterNode(self, pid):
        if pid != None:
            self.centerNode = self.procdict[pid]
            self.centerNode.setPos(0, 0)
            
    def addFileNode(self, fname, label, info):
        node = FileNode(self, fname, label, info)
        self.filedict[fname] = node
        self.addNode(node)
            
    def addFileEdge(self, pid, fname, action):
        pnode = self.procdict[pid]
        fnode = self.filedict[fname]
        self.scene().addItem(Edge(pnode, fnode, action))
        
    def addSockNode(self, sock, info):
        node = SocketNode(self, sock, sock, info)
        self.sockdict[sock] = node
        self.addNode(node)
        
    def addConnectEdge(self, pid, sock):
        pnode = self.procdict[pid]
        snode = self.sockdict[sock]
        self.scene().addItem(Edge(pnode, snode, SOCK_EDGE))
        
    def addAcceptEdge(self, pid, sock):
        try:
            pnode = self.procdict[pid]
            snode = self.sockdict[sock]
            self.scene().addItem(Edge(snode, pnode, SOCK_EDGE))
        except KeyError:
            l.warn('%s:\n %s', pid, db.getIpInfo(sock))

    def itemMoved(self):
        if not self.timerId:
            self.timerId = self.startTimer(1000 / 25)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Up:
            self.centerNode.moveBy(0, -20)
        elif key == QtCore.Qt.Key_Down:
            self.centerNode.moveBy(0, 20)
        elif key == QtCore.Qt.Key_Left:
            self.centerNode.moveBy(-20, 0)
        elif key == QtCore.Qt.Key_Right:
            self.centerNode.moveBy(20, 0)
        elif key == QtCore.Qt.Key_Plus:
            self.scaleView(1.2)
        elif key == QtCore.Qt.Key_Minus:
            self.scaleView(1 / 1.2)
        elif key == QtCore.Qt.Key_Space or key == QtCore.Qt.Key_Enter:
            for item in self.scene().items():
                if isinstance(item, Node):
                    item.setPos(-150 + QtCore.qrand() % 300, -150 + QtCore.qrand() % 300)
        else:
            super(GraphWidget, self).keyPressEvent(event)

    def timerEvent(self, event):
        nodes = [item for item in self.scene().items() if isinstance(item, Node)]
        if len(nodes) > 100:
            self.killTimer(self.timerId)
            self.timerId = 0
            return

        for node in nodes:
            if node != self.centerNode:
                node.calculateForces()

        itemsMoved = False
        for node in nodes:
            if node.advance():
                itemsMoved = True

        if not itemsMoved:
            self.killTimer(self.timerId)
            self.timerId = 0

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, -event.delta() / 240.0))

    def drawBackground(self, painter, rect):
        # Shadow.
        sceneRect = self.sceneRect()
        rightShadow = QtCore.QRectF(sceneRect.right(), sceneRect.top() + 5, 5,
                sceneRect.height())
        bottomShadow = QtCore.QRectF(sceneRect.left() + 5, sceneRect.bottom(),
                sceneRect.width(), 5)
        if rightShadow.intersects(rect) or rightShadow.contains(rect):
	        painter.fillRect(rightShadow, QtCore.Qt.darkGray)
        if bottomShadow.intersects(rect) or bottomShadow.contains(rect):
	        painter.fillRect(bottomShadow, QtCore.Qt.darkGray)

        # Fill.
        #~ gradient = QtGui.QLinearGradient(sceneRect.topLeft(),
                #~ sceneRect.bottomRight())
        #~ gradient.setColorAt(0, QtCore.Qt.white)
        #~ gradient.setColorAt(1, QtCore.Qt.lightGray)
        #~ painter.fillRect(rect.intersect(sceneRect), QtGui.QBrush(gradient))
        #~ painter.setBrush(QtCore.Qt.NoBrush)
        #~ painter.drawRect(sceneRect)

        # Text.
        """textRect = QtCore.QRectF(sceneRect.left() + 4, sceneRect.top() + 4,
                sceneRect.width() - 4, sceneRect.height() - 4)
        message = "Click and drag the nodes around, and zoom with the " \
                "mouse wheel or the '+' and '-' keys"

        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QtCore.Qt.lightGray)
        painter.drawText(textRect.translated(2, 2), message)
        painter.setPen(QtCore.Qt.black)
        painter.drawText(textRect, message)"""

    def scaleView(self, scaleFactor):
        factor = self.matrix().scale(scaleFactor, scaleFactor).mapRect(QtCore.QRectF(0, 0, 1, 1)).width()

        if factor < 0.07 or factor > 100:
            return

        self.scale(scaleFactor, scaleFactor)

    def resizeEvent(self, event):
        w = self.width() * 1.2
        h = self.height() * 1.2
        self.scene().setSceneRect(-w/2, -h/2, w, h)

    def clear(self):
        # save current position
        nodes = [item for item in self.scene().items() if isinstance(item, Node)]

        for node in nodes:
            if node != self.centerNode:
                self.nodepos[node.dbid] = node.pos()
        self.scene().clear()
