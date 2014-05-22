from PyQt4 import QtGui
from PyQt4 import QtCore
import db

def adjustQRectF(rect, adjustxy, adjustwh):
    return QtCore.QRectF(rect.x() + adjustxy, rect.y() + adjustxy, \
        rect.width() + adjustwh, rect.height() + adjustwh)

colorList = [QtCore.Qt.cyan, QtCore.Qt.darkCyan, QtCore.Qt.red, \
        QtCore.Qt.darkRed, QtCore.Qt.magenta, QtCore.Qt.darkMagenta, \
        QtCore.Qt.green, QtCore.Qt.darkGreen, QtCore.Qt.yellow, \
        QtCore.Qt.darkYellow, QtCore.Qt.blue, QtCore.Qt.darkBlue]
string2color = {}
colorCount = 0

def getColorFromStr(aString):
    global colorCount
    if aString in string2color:
        return string2color[aString]
    else:
        string2color[aString] = colorList[colorCount]
        colorCount = 0 if colorCount == (len(colorList) - 1) else (colorCount + 1)
        return string2color[aString]
        

class Node(QtGui.QGraphicsItem):
    
    Type = QtGui.QGraphicsItem.UserType + 1
    targetDx = 600
    targetDy = 600
    okLength = 360000
    epsilon = 5
    optimalrect = QtCore.QRectF(-50,-30,100,60)
    dbid = -1
    
    def __init__(self, graphWidget, label, highlight):
        super(Node, self).__init__()
        
        self.app = graphWidget.app
        self.label = label
        self.highlight = highlight

        self.graph = graphWidget
        self.edgeList = []
        self.newPos = QtCore.QPointF()

        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)

    def type(self):
        return Node.Type

    def addEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList

    def calculateForces(self):
        if not self.scene() or self.scene().mouseGrabberItem() is self:
            self.newPos = self.pos()
            return
    
        # Sum up all forces pushing this item away.
        xvel = 0.0
        yvel = 0.0
        for item in self.scene().items():
            if not isinstance(item, Node):
                continue

            line = QtCore.QLineF(self.mapFromItem(item, 0, 0),
                    QtCore.QPointF(0, 0))
            dx = line.dx()
            dy = line.dy()
            l = 2.0 * (dx * dx + dy * dy)
            if l > 0 and l < self.okLength:
                xvel += (dx * self.targetDx) / l
                yvel += (dy * self.targetDy) / l
        
        # and pushing from wall
        dd = self.scene().width()/2 - QtCore.qAbs(self.x()) + 10
        if QtCore.qAbs(dd) > 0 and QtCore.qAbs(dd) < self.targetDx:
            xvel += -self.x() / dd
        dd = self.scene().height()/2 - QtCore.qAbs(self.y()) + 10
        if QtCore.qAbs(dd) > 0 and QtCore.qAbs(dd) < self.targetDy:
            yvel += -self.y() / dd

        # Now subtract all forces pulling items together.
        weight = (len(self.edgeList) + 1) * 10.0
        for edge in self.edgeList:
            if edge.sourceNode() is self:
                pos = self.mapFromItem(edge.destNode(), 0, 0)
            else:
                pos = self.mapFromItem(edge.sourceNode(), 0, 0)
            xvel += pos.x() / weight
            yvel += pos.y() / weight
    
        if QtCore.qAbs(xvel) < self.epsilon and QtCore.qAbs(yvel) < self.epsilon:
            xvel = yvel = 0.0

        sceneRect = self.scene().sceneRect()
        self.newPos = self.pos() + QtCore.QPointF(xvel, yvel)
        self.newPos.setX(min(max(self.newPos.x(), sceneRect.left() + 10), sceneRect.right() - 10))
        self.newPos.setY(min(max(self.newPos.y(), sceneRect.top() + 10), sceneRect.bottom() - 10))

    def advance(self):
        if self.newPos == self.pos():
            return False

        self.setPos(self.newPos)
        return True

    def boundingRect(self):
        adjust = 2.0
        return adjustQRectF(self.optimalrect, -adjust, adjust)
            

    def shape(self):
        path = QtGui.QPainterPath()
        #path.addEllipse(-10, -10, 20, 20)
        path.addRect(self.optimalrect)
        return path

    def paint(self, painter, option, widget):
        painter.setPen(QtCore.Qt.NoPen)
        
        painter.setBrush(QtCore.Qt.lightGray)
        borderColor = QtCore.Qt.gray if self.info['dbid'] is None or self.info['dbid'] == '(null)' \
            else getColorFromStr(self.info['dbid'])
        painter.setPen(QtGui.QPen(borderColor, 0))
        #painter.drawRect(self.optimalrect)
        self.paintShape(painter)

        textColor = QtCore.Qt.yellow if self.highlight else QtCore.Qt.black
        painter.setPen(QtGui.QPen(textColor))
        painter.drawText(adjustQRectF(self.optimalrect, 10, -20), \
        #painter.drawText(self.optimalrect, \
            QtCore.Qt.AlignCenter & QtCore.Qt.TextWordWrap, \
            self.label)
        
    def paintShape(self, painter):
        print "Implement me!"

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edgeList:
                edge.adjust()
            self.graph.itemMoved()

        return super(Node, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(Node, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(Node, self).mouseReleaseEvent(event)
        
class FileNode(Node):
    Type = QtGui.QGraphicsItem.UserType + 2
    def __init__(self, graphWidget, dbid, label, info):
        super(FileNode, self).__init__(graphWidget, label, info['hl'])
        self.dbid = dbid
        self.info = info

    def paintShape(self, painter):
        painter.drawEllipse(self.optimalrect)
    
    def mousePressEvent(self, event):
        super(FileNode, self).mousePressEvent(event)
        self.app.showFileInfo(self.dbid, self.info['details'])
        #~ self.app.showFileInfo(self.dbid)
        
class ProcessNode(Node):
    Type = QtGui.QGraphicsItem.UserType + 3
    def __init__(self, graphWidget, dbid, label, info):
        super(ProcessNode, self).__init__(graphWidget, label, info['hl'])
        self.dbid = dbid
        self.info = info
    
    def paintShape(self, painter):
        painter.drawRect(self.optimalrect)

    def mousePressEvent(self, event):
        super(ProcessNode, self).mousePressEvent(event)
        self.app.showProcessInfo(self.dbid, self.info)
        #~ self.app.showProcessInfo(self.dbid)
        
    def mouseDoubleClickEvent(self, event):
        self.app.focusProcess(self.dbid, self.info['dbid'])

class SocketNode(Node):
    Type = QtGui.QGraphicsItem.UserType + 4
    def __init__(self, graphWidget, dbid, label, info):
        if label.startswith('..'):
            label = label[2:]
        else:
            label = db.getIpInfo(label)
        super(SocketNode, self).__init__(graphWidget, label, False)
        self.dbid = dbid
        self.info = info

    def paintShape(self, painter):
        painter.drawEllipse(self.optimalrect)
    
    def mousePressEvent(self, event):
        super(SocketNode, self).mousePressEvent(event)
        self.app.showSockInfo(self.dbid, self.label)
        #~ self.app.showFileInfo(self.dbid)
