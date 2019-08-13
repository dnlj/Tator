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

################################################################################
class EditArea(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.binds = BindSystem()
		
		self.setMouseTracking(True)
		self.curPos = QPoint()
		self.oldPos = QPoint()
		self.points = []
		
		# TODO: Change to numpy + skimage
		self.base = QImage("test3.jpg")
		
		self.canvas = QImage(self.base.width(), self.base.height(), QImage.Format_RGBA8888)
		self.canvas.fill(Qt.transparent)
		
		self.mask = np.zeros((self.base.height(), self.base.width()), dtype=np.uint8)
		#self.mask = Image.new("RGBA", (self.base.width(), self.base.height()), (0, 0, 0, 0))
		
		self.actionBrush = ActionBrush(self.mask)
		self.actionFill = ActionFill(self.mask)
		
		self.activeAction = self.actionBrush
		
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
		self.updateBindSystems(Input(InputType.MOUSE_WHEEL), event.angleDelta().y() / 120)
		
	def mouseMoveEvent(self, event: QMouseEvent):
		self.oldPos = self.curPos
		self.curPos = self.mousePosToCanvasPos(event.pos())
		
		if self.oldPos == self.curPos:
			return
		
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
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		windowFeatures = QDockWidget.DockWidgetMovable
		
		self.setWindowTitle("Tator")
		self.setWindowIcon(QIcon("icon.png"))
		self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
		
		self.setCentralWidget(EditArea())
		
		# TODO: Toolbar
		self.toolbar = QToolBar("Tools")
		self.toolbar.addAction("Box")
		self.toolbar.addAction("Polygon")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Brush")
		self.toolbar.addAction("Fill")
		self.toolbar.addAction("Wand Select")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Smart Select")
		
		self.imagePanel = QDockWidget("Image Panel")
		self.imagePanel.setFeatures(windowFeatures)
		
		self.labelPanel = QDockWidget("Label Panel")
		self.labelPanel.setFeatures(windowFeatures)
		
		self.layerPanel = QDockWidget("Layer Panel")
		self.layerPanel.setFeatures(windowFeatures)
		
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