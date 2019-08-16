from typing import Any, Callable, List, Tuple, Dict
from collections import *

from PIL import Image, ImageQt, ImageDraw

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import numpy as np

from binder import *
from ActionBrush import ActionBrush
from ActionFill import ActionFill

# Flood fill
# GrabCut (https://docs.opencv.org/3.4/d8/d83/tutorial_py_grabcut.html)
#	https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
# https://www.cc.gatech.edu/~aagrawal307/magic.pdf

# TODO: change events to send np arrays instead of QPoints
# TODO: Undo/Redo
# TODO: cursor per tool
# TODO: Tool shortcuts
# TODO: Tool options menu
# TODO: Switch visible tools depending on active layer type

################################################################################
class LayerBitmap:
	def __init__(self):
		self.mask = None
		self.label = "This is the layer label"
		self.visible = True
################################################################################
class EditArea(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.binds = BindSystem()
		
		self.setMouseTracking(True)
		self.curPos = QPoint()
		self.oldPos = QPoint()
		self.points = []
		
		self.base = QImage("test3.jpg")
		
		self.canvas = QImage(self.base.width(), self.base.height(), QImage.Format_RGBA8888)
		self.canvas.fill(Qt.transparent)
		
		#self.layers = []
		#self.layers.append(LayerBitmap())
		#self.activeLayer = layers[0]
		
		self.mask = np.zeros((self.base.height(), self.base.width()), dtype=np.uint8)
		
		self.actions = {}
		self.actions[ActionBrush] = ActionBrush(self.mask)
		self.actions[ActionFill] = ActionFill(self.mask)
		
		self.activeAction = self.actions[ActionBrush]
		
	def setAction(self, action):
		self.activeAction = self.actions[action]
		
	def resizeEvent(self, event: QResizeEvent):
		self.scaledScale = min(self.width() / self.base.width(), self.height() / self.base.height())
		self.scaledSize = self.base.size() * self.scaledScale
		self.scaledOffset = (self.size() - self.scaledSize) / 2
		self.scaledOffset = QPoint(self.scaledOffset.width(), self.scaledOffset.height())
		
	def mousePosToCanvasPos(self, pos: QPoint):
		return (pos - self.scaledOffset) / self.scaledScale
		
	def updateBindSystems(self, inp: Input, val: Any):
		self.binds.update(inp, val)
		self.activeAction.binds.update(inp, val)
		self.update()
		
	def mousePressEvent(self, event: QMouseEvent):
		self.updateBindSystems(Input(InputType.MOUSE, event.button()), (True, self.mousePosToCanvasPos(event.pos()))) # TODO: make proper custom event for this?
			
	def mouseReleaseEvent(self, event: QMouseEvent):
		self.updateBindSystems(Input(InputType.MOUSE, event.button()), (False, self.mousePosToCanvasPos(event.pos()))) # TODO: make proper custom event for this?
			
	def wheelEvent(self, event: QWheelEvent):
		self.updateBindSystems(Input(InputType.MOUSE_WHEEL), event.angleDelta().y())
		
	def mouseMoveEvent(self, event: QMouseEvent):
		newPos = self.mousePosToCanvasPos(event.pos())
		
		if newPos == self.curPos:
			return
		
		self.oldPos = self.curPos
		self.curPos = newPos
		self.updateBindSystems(Input(InputType.MOUSE, event.button()), (None, self.curPos)) # TODO: make proper event for this?
	
	def composeCanvas(self):
		with QPainter(self.canvas) as painter:
			painter.drawImage(0, 0, self.base)

			maskToQt = QImage(self.mask.data, self.mask.shape[1], self.mask.shape[0], QImage.Format_Indexed8)
			maskToQt.setColorTable([0] * 255 + [qRgba(255,0,0,127)])
			painter.drawImage(0, 0, maskToQt)
			
		self.activeAction.drawHints(self.canvas, self.curPos)
		
	def paintEvent(self, event: QPaintEvent):
		# TODO: Make use of event.rect(), may get better performance
		w = self.width()
		h = self.height()
		
		painter = QPainter(self)
		painter.setClipping(False)
		
		pen = QPen()
		pen.setWidth(2)
		pen.setColor(Qt.black)
		
		bgBrush = QBrush()
		bgBrush.setStyle(Qt.Dense5Pattern)
		bgBrush.setColor(QColor(0, 0, 0, 50))
		
		# Draw background
		painter.setBrush(Qt.white)
		painter.drawRect(0, 0, w, h)
		
		painter.setPen(pen)
		painter.setBrush(bgBrush)
		painter.drawRect(0, 0, w, h)
		
		# Draw Canvas
		# TODO: switch to Pillow resize here
		self.composeCanvas()
		painter.drawImage(self.scaledOffset, self.canvas.scaled(self.scaledSize))
		#painter.drawImage(QPoint(), self.canvas)
		
################################################################################
class LayerView(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		layout.addWidget(QCheckBox()) # TODO: Custom eye icons?
		# TODO: Layer Preview
		layout.addWidget(QLabel("This is the label")) # TODO: Dropdown to select
		layout.addWidget(QLabel("[B]")) # TODO: Icon
		layout.addWidget(QPushButton("-"))
		
		# TODO: override paint? call super().paint ?
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.red)
		self.setAutoFillBackground(True)
		self.setPalette(pal)
		
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton: # TODO: Change to bind system
			self.parent().setLayerSelection(self) # TODO: Look at https://doc.qt.io/qt-5/signalsandslots.html
		
################################################################################
class LayerListViewContainer(QWidget): # TODO: Rename all this layer stuff. its bad LayerViewList
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		self.setLayout(self.layout)
		
		pal = QPalette()
		pal.setColor(QPalette.Background, QColor(255, 255, 0))
		self.setAutoFillBackground(True)
		self.setPalette(pal)
		
	def addLayer(self):
		self.layout.addWidget(LayerView(self))
		
	def setLayerSelection(self, layer: LayerView):
		print("WOOOp", layer)
################################################################################
class LayerListView(QScrollArea):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		
		self.setFrameShape(QFrame.NoFrame)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.setWidgetResizable(True)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		self.layerContainer = LayerListViewContainer(self)
		self.setWidget(self.layerContainer)
		
		for i in range(0, 10):
			self.layerContainer.addLayer()
		
		#this = QWidget()
		#self.setWidget(this)
		#this.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		#
		#layout = QVBoxLayout()
		#layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		#this.setLayout(layout)
		#print("Self: ", self)
		#print("This: ", this)
		#for i in range(0,10):
		#	layout.addWidget(LayerView(this))
		#this.adjustSize()
		
		self.setMinimumWidth(self.sizeHint().width() + self.verticalScrollBar().sizeHint().width())
		
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.blue)
		self.setAutoFillBackground(True)
		self.setPalette(pal)
class LayerListViewToolbar(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
		
		layout = QHBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		layout.addWidget(QPushButton("New Bitmap"))
		layout.addWidget(QPushButton("New Vector"))
		self.setLayout(layout)
		
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.green)
		self.setAutoFillBackground(True)
		self.setPalette(pal)
		
class LayerListWidget(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.listView = LayerListView(self)
		self.toolbar = LayerListViewToolbar(self)
		
		layout = QVBoxLayout()
		layout.addWidget(self.listView)
		layout.addWidget(self.toolbar)
		self.setLayout(layout)
		
################################################################################
class MainWindow(QMainWindow):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		windowFeatures = QDockWidget.DockWidgetMovable
		
		self.setWindowTitle("Tator")
		self.setWindowIcon(QIcon("icon.png"))
		self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
		
		editArea = EditArea()
		self.setCentralWidget(editArea)
		
		# TODO: Toolbar
		self.toolbar = QToolBar("Tools")
		self.toolbar.addAction("Box")
		self.toolbar.addAction("Polygon")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Brush", lambda: editArea.setAction(ActionBrush))
		self.toolbar.addAction("Fill", lambda: editArea.setAction(ActionFill))
		self.toolbar.addAction("Wand Select")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Smart Select")
		
		# TODO: Look into flow layout
		self.imagePanel = QDockWidget("Images Panel")
		self.imagePanel.setFeatures(windowFeatures)
		
		self.labelPanel = QDockWidget("Labels Panel")
		self.labelPanel.setFeatures(windowFeatures)
		
		self.layerPanel = QDockWidget("Layers Panel")
		self.layerPanel.setFeatures(windowFeatures)
		self.layerPanel.setWidget(LayerListWidget())
		
		self.addToolBar(self.toolbar)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.imagePanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.labelPanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.layerPanel)
		self.setStatusBar(QStatusBar())
	
	def keyPressEvent(self, event: QKeyEvent):
		if event.key() == Qt.Key_Escape:
			self.close()

################################################################################
if __name__ == "__main__":
	app = QApplication([])
	# TODO: Set dark theme
	main = MainWindow()
	main.resize(1920, 1080)
	main.show()
	app.exec_()