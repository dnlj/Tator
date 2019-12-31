from typing import Any, Callable, List, Tuple, Dict
from collections import *
import os

from PIL import Image, ImageQt, ImageDraw

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import numpy as np
import rapidjson as json

from binder import *
from ActionBrush import ActionBrush
from ActionFill import ActionFill
from LayerBitmap import LayerBitmap
from LayerListWidget import LayerListWidget
from ThumbnailPreview import ThumbnailPreview
from Listenable import Listenable

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
	def __init__(self, actions, cats, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.onLayersUpdated = Listenable()
		self.activeLayer = None
		
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
		
		self.actions = {}
		for a, d in actions.items():
			self.actions[a] = a()
		self.activeAction = self.actions[ActionBrush]
	
	def setImage(self, img: QImage):
		self.base = img
		self.canvas = QImage(self.base.width(), self.base.height(), QImage.Format_RGBA8888)
		self.canvas.fill(Qt.transparent)
		self.layers = []
		self.layersUpdate()
		self.recalcScale()
		self.update()
	
	def getLayers(self):
		pass # TODO: impl
	
	def layersUpdate(self):
		self.onLayersUpdated.notify(self.layers)
		
	def setActiveLayer(self, layer: LayerBitmap):
		self.activeLayer = layer
		self.activeAction.setLayer(self.activeLayer)
		self.update()
		
	def addLayer(self, layer):
		self.layers.append(layer)
		def fieldChangedListener(new, old):
			self.layersUpdate()
			self.update()
		layer.label.addListener(fieldChangedListener)
		layer.visible.addListener(fieldChangedListener)
		self.setActiveLayer(layer)
		self.layersUpdate()
		
	def addBitmapLayer(self):
		self.addLayer(LayerBitmap(self.base.height(), self.base.width()))
		
	def deleteLayer(self, layer):
		self.layers.remove(layer)
		if layer == self.activeLayer:
			self.setActiveLayer(None)
		self.layersUpdate()
		self.update()
		
	def setAction(self, action):
		self.activeAction = self.actions[action]
		self.activeAction.setLayer(self.activeLayer)
		
	def recalcScale(self):
		self.scaledScale = min(self.width() / self.base.width(), self.height() / self.base.height())
		self.scaledSize = self.base.size() * self.scaledScale
		self.scaledOffset = (self.size() - self.scaledSize) / 2
		self.scaledOffset = QPoint(self.scaledOffset.width(), self.scaledOffset.height())
		
	def resizeEvent(self, event: QResizeEvent):
		self.recalcScale()
		
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
					color |= 0x44000000
					
				maskToQt.setColorTable([0] * 255 + [color])
				painter.drawImage(0, 0, maskToQt)
		
		# TODO: make hints inverse of background color?
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
				"key": Qt.Key_G,
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
			self.project = json.load(pfile)
		
		# TODO: We should be able to delete things from the json file and have it just work. Will need to change this.
		# Verify category ids
		cats = self.project["categories"]
		for i in range(len(cats)):
			if i != cats[i]["id"]: raise RuntimeError("Incorrect category id")
			oldColor = cats[i]["color"]
			newColor = QColor()
			newColor.setRgb(oldColor)
			cats[i]["color"] = newColor.rgba()
		
		# Verify image ids
		imgs = self.project["images"]
		for i in range(len(imgs)):
			if i != imgs[i]["id"]: raise RuntimeError("Incorrect image id")
			
		# Verify annotation ids
		anns = self.project["annotations"]
		for i in range(len(anns)):
			if i != anns[i]["id"]: raise RuntimeError("Incorrect annotation id")
			
		self.setWindowTitle("Tator")
		self.setWindowIcon(QIcon("icon.png"))
		self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
		
		self.editArea = EditArea(actions, cats)
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
		self.thumbnailPreview = ThumbnailPreview()
		self.imagePanel = QDockWidget("")
		self.imagePanel.setFeatures(windowFeatures)
		self.imagePanel.setWidget(self.thumbnailPreview)
		self.thumbnailPreview.prevButton.clicked.connect(lambda: self.prevImage())
		self.thumbnailPreview.nextButton.clicked.connect(lambda: self.nextImage())
		#self.imagePanel.setWidget(self.thumbList)
		# TODO: Image list with search bar (icon indicating if they have annotations)
		# TODO: preview of 5 imgs. prev 2, current and next 2
		# TODO: next/prev button
		
		self.labelPanel = QDockWidget("Categories Panel")
		self.labelPanel.setFeatures(windowFeatures)
		
		self.layerList = LayerListWidget(cats)
		self.layerList.onNewBitmapClicked.connect(self.editArea.addBitmapLayer)
		self.layerList.onLayerSelectionChanged.connect(self.editArea.setActiveLayer)
		self.layerList.onDeleteLayer.connect(lambda layer: self.editArea.deleteLayer(layer))
		self.editArea.onLayersUpdated.addListener(self.layerList.updateLayers)
		
		self.layerPanel = QDockWidget("Layers Panel")
		self.layerPanel.setFeatures(windowFeatures)
		self.layerPanel.setWidget(self.layerList)
		
		self.addToolBar(self.toolbar)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.imagePanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.labelPanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.layerPanel)
		self.setStatusBar(QStatusBar())
		
		self.curImage = -1
		self.nextImage()
	
	def setImage(self, path):
		self.editArea.setImage(QImage(path))
		self.editArea.addBitmapLayer()
		self.layerList.setLayerSelection(0)
		
	def nextImage(self, skipKnown: bool = False):
		if self.curImage == len(self.project["images"]) - 1: return # TODO: warning or something?
		self.curImage += 1
		img = self.project["images"][self.curImage]
		self.setImage(img["path"])
		
	def prevImage(self):
		if self.curImage == 0: return # TODO: warning or something?
		self.curImage -= 1
		img = self.project["images"][self.curImage]
		self.setImage(img["path"])
	
	#def closeEvent(self, event: QCloseEvent):
	# TODO: write to temp file then rename once complete
	#	with open("test.json", "w") as pfile:
	#		json.dump(
	#			self.project,
	#			pfile,
	#			ensure_ascii=False,
	#			indent=4
	#		)

################################################################################
if __name__ == "__main__":
	app = QApplication([])
	# TODO: Set dark theme
	main = MainWindow()
	main.resize(1920, 1080)
	main.show()
	app.exec_()