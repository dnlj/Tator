from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from binder import *
from LayerBitmap import LayerBitmap
from Listenable import Listenable
from ActionBrush import ActionBrush
from ActionFill import ActionFill

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
					color |= 0xAA000000
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
