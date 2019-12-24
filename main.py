from typing import Any, Callable, List, Tuple, Dict
from collections import *

from PIL import Image, ImageQt, ImageDraw

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import numpy as np
import json

from binder import *
from ActionBrush import ActionBrush
from ActionFill import ActionFill
from LayerBitmap import LayerBitmap
from LayerListWidget import LayerListWidget
from ThumbnailPreview import ThumbnailPreview

# GrabCut (https://docs.opencv.org/3.4/d8/d83/tutorial_py_grabcut.html)
#	https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
# https://www.cc.gatech.edu/~aagrawal307/magic.pdf

# TODO: look into watershed:
#	https://en.wikipedia.org/wiki/Watershed_(image_processing)
#	https://scikit-image.org/docs/dev/auto_examples/segmentation/plot_watershed.html
# 	https://docs.opencv.org/master/d3/db4/tutorial_py_watershed.html

# TODO: change events to send np arrays instead of QPoints
# TODO: Undo/Redo
# TODO: cursor per tool
# TODO: Tool shortcuts
# TODO: Tool options menu
# TODO: Switch visible tools depending on.activeLayer.mask layer type
# TODO: Make 1-9+0 shortcuts for changing the active layers label
# TODO: Warn if a layer is unlabeled
# TODO: right click open dropdown to select layer type?


################################################################################
class EditArea(QWidget):
	onLayersUpdated = pyqtSignal([int, LayerBitmap])
	activeLayer = None
	
	def __init__(self, actions, cats, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.cats = cats
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("close",
			inputs=[(Input(InputType.KEYBOARD, Qt.Key_Escape), lambda e : e[0])]
		))
		self.binds.addListener("close", BindEvent.PRESS, lambda i, v, ii: self.parent().close())
		
		# TODO: Should these binds be the MainWindow?
		for a, d in actions.items():
			self.binds.addBind(Bind(d["name"],
				inputs=[(Input(InputType.KEYBOARD, d["key"]), lambda e : e[0])]
			))
			def callback(input, value, inputs, a=a): self.setAction(a)
			self.binds.addListener(d["name"], BindEvent.PRESS, callback)
		
		self.setFocusPolicy(Qt.WheelFocus)
		self.setMouseTracking(True)
		self.curPos = QPoint()
		self.oldPos = QPoint()
		self.points = []
		
		self.base = QImage("data/test3.jpg")
		
		self.canvas = QImage(self.base.width(), self.base.height(), QImage.Format_RGBA8888)
		self.canvas.fill(Qt.transparent)
		
		# TODO: should layers be stored on the widget? seems out of place
		self.layers = []
		
		self.actions = {}
		
		for a, d in actions.items():
			self.actions[a] = a()
		self.activeAction = self.actions[ActionBrush]
		
	def setActiveLayer(self, layer: LayerBitmap):
		self.activeLayer = layer
		self.activeAction.setLayer(self.activeLayer)
		self.update()
		
	def addLayer(self, layer):
		self.layers.append(layer)
		def fieldChangedListener(new, old):
			# TODO: This is wrong. This should be the index of the currently selected layer.
			self.onLayersUpdated.emit(len(self.layers) - 1, layer)
			self.update()
		layer.label.addListener(fieldChangedListener)
		layer.visible.addListener(fieldChangedListener)
		self.setActiveLayer(layer)
		# TODO: This is wrong. This should be the index of the currently selected layer.
		self.onLayersUpdated.emit(len(self.layers) - 1, layer)
		
	def addBitmapLayer(self):
		self.addLayer(LayerBitmap(self.base.height(), self.base.width()))
		
	def deleteLayer(self, layer):
		self.layers.remove(layer)
		# TODO: This is wrong. This should be the index of the currently selected layer.
		self.onLayersUpdated.emit(len(self.layers) - 1, layer)
		self.update()
		
	def setAction(self, action):
		self.activeAction = self.actions[action]
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
	
	def keyPressEvent(self, event: QKeyEvent):
		self.updateBindSystems(Input(InputType.KEYBOARD, event.key()), (True,))
		
	def keyReleaseEvent(self, event: QKeyEvent):
		self.updateBindSystems(Input(InputType.KEYBOARD, event.key()), (False,))
		
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
			
			# TODO: Cache the composite of the layers. So we dont lag when not editing with large number of layers.
			for layer in self.layers:
				if not layer.visible.value: continue
				# TODO: always draw active layer on top, lower opacity of BG layers
				# TODO: See if composing in numpy then converting is faster than converting to QImage and composing
				mask = layer.mask
				maskToQt = QImage(mask.data, mask.shape[1], mask.shape[0], QImage.Format_Indexed8)
				color = self.cats[layer.label.value]["color"]
				
				# Set the alpha
				color &= 0x00FFFFFF
				if layer == self.activeLayer:
					color |= 0xCC000000
				else:
					color |= 0x66000000
					
				maskToQt.setColorTable([0] * 255 + [color])
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
		
		actions = {
			ActionBrush: {
				"name": "Brush",
				"key": Qt.Key_B,
			},
			ActionFill: {
				"name": "Fill",
				"key": Qt.Key_F,
			},
		}
		
		labels = [
			"",
			"Label A",
			"Label B",
			"Label C",
			"Label D",
			"Label E",
		]
		
		categories = None
		
		with open("project.json") as pfile:
			project = json.load(pfile)
		
		# TODO: We should be able to delete things from the json file and have it just work. Will need to change this.
		# Verify category ids
		categories = project["categories"]
		for i in range(len(categories)):
			if i != categories[i]["id"]: raise RuntimeError("Incorrect category id")
			oldColor = categories[i]["color"]
			newColor = QColor()
			newColor.setRgb(oldColor)
			categories[i]["color"] = newColor.rgba()
		
		# Verify image ids
		images = project["images"]
		for i in range(len(images)):
			if i != images[i]["id"]: raise RuntimeError("Incorrect image id")
			
		# Verify annotation ids
		annotations = project["annotations"]
		for i in range(len(annotations)):
			if i != annotations[i]["id"]: raise RuntimeError("Incorrect annotation id")
			
		self.setWindowTitle("Tator")
		self.setWindowIcon(QIcon("icon.png"))
		self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
		
		self.editArea = EditArea(actions, categories)
		self.setCentralWidget(self.editArea)
		
		# TODO: Toolbar
		self.toolbar = QToolBar("Tools")
		self.toolbar.addAction("Box")
		self.toolbar.addAction("Polygon")
		self.toolbar.addSeparator()
		
		for a, d in actions.items():
			def callback(a=a): self.editArea.setAction(a)
			self.toolbar.addAction(d["name"], callback)
		self.toolbar.addAction("Wand Select")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Smart Select")
		
		# TODO: Look into flow layout
		self.imagePanel = QDockWidget("")
		self.imagePanel.setFeatures(windowFeatures)
		self.imagePanel.setWidget(ThumbnailPreview())
		#self.imagePanel.setWidget(self.thumbList)
		# TODO: Image list with search bar (icon indicating if they have annotations)
		# TODO: preview of 5 imgs. prev 2, current and next 2
		# TODO: next/prev button
		
		self.labelPanel = QDockWidget("Categories Panel")
		self.labelPanel.setFeatures(windowFeatures)
		
		self.layerList = LayerListWidget(self.editArea.layers, categories)
		self.layerList.onNewBitmapClicked.connect(self.editArea.addBitmapLayer)
		self.layerList.onLayerSelectionChanged.connect(self.editArea.setActiveLayer)
		self.layerList.onDeleteLayer.connect(lambda layer: self.editArea.deleteLayer(layer))
		
		self.layerPanel = QDockWidget("Layers Panel")
		self.layerPanel.setFeatures(windowFeatures)
		self.layerPanel.setWidget(self.layerList)
		self.editArea.onLayersUpdated.connect(self.layerList.layersUpdated)
		
		self.addToolBar(self.toolbar)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.imagePanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.labelPanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.layerPanel)
		self.setStatusBar(QStatusBar())
		
		self.editArea.addBitmapLayer()

################################################################################
if __name__ == "__main__":
	app = QApplication([])
	# TODO: Set dark theme
	main = MainWindow()
	main.resize(1920, 1080)
	main.show()
	app.exec_()