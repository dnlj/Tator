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
from LayerListWidget import LayerListWidget

# GrabCut (https://docs.opencv.org/3.4/d8/d83/tutorial_py_grabcut.html)
#	https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
# https://www.cc.gatech.edu/~aagrawal307/magic.pdf

# TODO: change events to send np arrays instead of QPoints
# TODO: Undo/Redo
# TODO: cursor per tool
# TODO: Tool shortcuts
# TODO: Tool options menu
# TODO: Switch visible tools depending on.activeLayer.mask layer type
# TODO: Make 1-9+0 shortcuts for changing the active layers label
# TODO: Warn if a layer is unlabeled

################################################################################
class EditArea(QWidget):
	onLayerAdded = pyqtSignal([int, LayerBitmap])
	onLayerDeleted = pyqtSignal([LayerBitmap])
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
		
	def setActiveLayer(self, layer: LayerBitmap):
		self.activeLayer = layer
		self.activeAction.setLayer(self.activeLayer)
		
	def addLayer(self, layer):
		self.layers.append(layer)
		layer.visible.addListener(lambda new, old: self.update())
		self.setActiveLayer(layer)
		self.onLayerAdded.emit(len(self.layers) - 1, layer)
		
	def addBitmapLayer(self):
		self.addLayer(LayerBitmap(self.base.height(), self.base.width()))
		
	def deleteLayer(self, layer):
		self.layers.remove(layer)
		self.onLayerDeleted.emit(layer)
		self.update()
		
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
		
		if self.activeLayer and self.activeLayer.visible.value:
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
			
			for layer in self.layers:
				if not layer.visible.value: continue
				# TODO: always draw active layer on top, lower opacity of BG layers
				mask = layer.mask
				maskToQt = QImage(mask.data, mask.shape[1], mask.shape[0], QImage.Format_Indexed8)
				maskToQt.setColorTable([0] * 255 + [layer.color])
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
class MainWindow(QMainWindow):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		windowFeatures = QDockWidget.DockWidgetMovable
		
		labels = [
			"",
			"Label A",
			"Label B",
			"Label C",
			"Label D",
			"Label E",
		]
		
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
		
		self.layerList = LayerListWidget(self.editArea.layers, labels)
		self.layerList.onNewBitmapClicked.connect(self.editArea.addBitmapLayer)
		self.layerList.onLayerSelectionChanged.connect(self.editArea.setActiveLayer)
		self.layerList.onDeleteLayer.connect(lambda layer: self.editArea.deleteLayer(layer))
		
		self.layerPanel = QDockWidget("Layers Panel")
		self.layerPanel.setFeatures(windowFeatures)
		self.layerPanel.setWidget(self.layerList)
		self.editArea.onLayerAdded.connect(self.layerList.layerAdded)
		self.editArea.onLayerDeleted.connect(self.layerList.layerDeleted)
		
		self.addToolBar(self.toolbar)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.imagePanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.labelPanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.layerPanel)
		self.setStatusBar(QStatusBar())
		
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