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
from LayerBitmap import LayerBitmap

# Flood fill
# GrabCut (https://docs.opencv.org/3.4/d8/d83/tutorial_py_grabcut.html)
#	https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
# https://www.cc.gatech.edu/~aagrawal307/magic.pdf

# TODO: change events to send np arrays instead of QPoints
# TODO: Undo/Redo
# TODO: cursor per tool
# TODO: Tool shortcuts
# TODO: Tool options menu
# TODO: Switch visible tools depending on.activeLayer.mask layer type

################################################################################
class EditArea(QWidget):
	onLayerAdded = pyqtSignal()
	activeLayer = None
	
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
		
		# TODO: should layers be stored on the widget? seems out of place
		self.layers = []
		
		self.activeAction = ActionBrush()
		
	def setActiveLayer(self, layerIndex):
		self.activeLayer = self.layers[layerIndex]
		self.activeAction.setLayer(self.activeLayer)
		
	def addLayer(self, layer):
		self.layers.append(layer)
		self.setActiveLayer(len(self.layers) - 1)
		self.onLayerAdded.emit()
		
	def addBitmapLayer(self):
		self.addLayer(LayerBitmap(self.base.height(), self.base.width()))
		
	def setAction(self, action):
		self.activeAction = action()
		self.activeAction.setLayer(self.activeLayer)
		
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
			
			if self.activeLayer is not None:
				mask = self.activeLayer.mask
				maskToQt = QImage(mask.data, mask.shape[1], mask.shape[0], QImage.Format_Indexed8)
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
	def __init__(self, layer, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.layer = layer
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
			# TODO: lookinto signals for this
			self.parent().setLayerSelection(self) # TODO: Look at https://doc.qt.io/qt-5/signalsandslots.html
			
	def setSelected(self, value: bool):
		pal = QPalette() # TODO: surely not the best way to handle this. Look into style sheets?
		if value:
			pal.setColor(QPalette.Background, Qt.blue)
		else:
			pal.setColor(QPalette.Background, Qt.red)
		self.setPalette(pal)
		
################################################################################
class LayerViewList(QWidget):
	def __init__(self, layers, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.selected = None
		self.layers = layers
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		self.setLayout(self.layout)
		self.updateLayers()
		
	def updateLayers(self):
		selectedLayer = self.selected and self.selected.layer or None
		
		# TODO: how do i delete a widget? This doesnt work
		while True:
			taken = self.layout.takeAt(0)
			if taken is not None:
				taken.widget().deleteLater()
			else:
				break
		for layer in self.layers:
			layerView = LayerView(layer)
			self.layout.addWidget(layerView)
			if layer is selectedLayer:
				self.setLayerSelection(layerView)
		
	def setLayerSelection(self, layerView: LayerView):
		if self.selected:
			self.selected.setSelected(False)
		self.selected = layerView
		self.selected.setSelected(True)
################################################################################
class LayerViewListScroll(QScrollArea):
	def __init__(self, layers, parent=None):
		super().__init__(parent=parent)
		
		self.setFrameShape(QFrame.NoFrame)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.setWidgetResizable(True)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		self.layerViewList = LayerViewList(layers=layers)
		self.setWidget(self.layerViewList)
		
	def sizeHint(self):
		return self.layerViewList.sizeHint() + self.verticalScrollBar().sizeHint()
		
	def updateLayers(self):
		self.layerViewList.updateLayers()
		self.updateGeometry() # TODO: can we move this into layerListView udpateLayers? does it propogate back up?
################################################################################
class LayerListToolbar(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
		
		layout = QHBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		
		self.newBitmapButton = QPushButton("New Bitmap")
		layout.addWidget(self.newBitmapButton)
		
		layout.addWidget(QPushButton("New Vector"))
		
		self.setLayout(layout)
		
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.green)
		self.setAutoFillBackground(True)
		self.setPalette(pal)
################################################################################		
class LayerListWidget(QWidget):
	def __init__(self, layers, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.listView = LayerViewListScroll(layers=layers)
		self.toolbar = LayerListToolbar()
		
		#self.toolbar.newBitmapButton.clicked.connect(self.onNewBitmapClicked)
		
		self.onNewBitmapClicked = self.toolbar.newBitmapButton.clicked
		
		layout = QVBoxLayout()
		layout.addWidget(self.listView)
		layout.addWidget(self.toolbar)
		self.setLayout(layout)
	
	def updateLayers(self):
		self.listView.updateLayers()
################################################################################
class MainWindow(QMainWindow):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		windowFeatures = QDockWidget.DockWidgetMovable
		
		self.setWindowTitle("Tator")
		self.setWindowIcon(QIcon("icon.png"))
		self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
		
		self.editArea = EditArea()
		self.setCentralWidget(self.editArea)
		
		# TODO: Toolbar
		self.toolbar = QToolBar("Tools")
		self.toolbar.addAction("Box")
		self.toolbar.addAction("Polygon")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Brush", lambda: self.editArea.setAction(ActionBrush))
		self.toolbar.addAction("Fill", lambda: self.editArea.setAction(ActionFill))
		self.toolbar.addAction("Wand Select")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Smart Select")
		
		# TODO: Look into flow layout
		self.imagePanel = QDockWidget("Images Panel")
		self.imagePanel.setFeatures(windowFeatures)
		
		self.labelPanel = QDockWidget("Labels Panel")
		self.labelPanel.setFeatures(windowFeatures)
		
		self.layerList = LayerListWidget(self.editArea.layers)
		self.layerList.onNewBitmapClicked.connect(self.addNewBitmapLayer)
		
		self.layerPanel = QDockWidget("Layers Panel")
		self.layerPanel.setFeatures(windowFeatures)
		self.layerPanel.setWidget(self.layerList)
		self.editArea.onLayerAdded.connect(self.layerList.updateLayers)
		
		self.addToolBar(self.toolbar)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.imagePanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.labelPanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.layerPanel)
		self.setStatusBar(QStatusBar())
		
		self.addNewBitmapLayer()
		
	def addNewBitmapLayer(self):
		self.editArea.addBitmapLayer()
		
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